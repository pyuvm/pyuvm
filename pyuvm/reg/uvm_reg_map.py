from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING, ClassVar

from pyuvm.error_classes import UVMFatalError
from pyuvm.reg.uvm_reg_backdoor import uvm_reg_backdoor
from pyuvm.reg.uvm_reg_item import uvm_reg_bus_op
from pyuvm.reg.uvm_reg_model import (
    uvm_access_e,
    uvm_elem_kind_e,
    uvm_endianness_e,
    uvm_hier_e,
)
from pyuvm.s05_base_classes import uvm_object
from pyuvm.s14_15_python_sequences import uvm_sequence, uvm_sequence_base

if TYPE_CHECKING:
    from pyuvm import (
        uvm_sequencer,
        uvm_sequencer_base,
    )
    from pyuvm.reg.uvm_mem import uvm_mem
    from pyuvm.reg.uvm_reg import uvm_reg
    from pyuvm.reg.uvm_reg_adapter import uvm_reg_adapter
    from pyuvm.reg.uvm_reg_block import uvm_reg_block
    from pyuvm.reg.uvm_reg_field import uvm_reg_field
    from pyuvm.reg.uvm_reg_item import uvm_reg_item
    from pyuvm.reg.uvm_reg_model import (
        uvm_reg_addr_t,
        uvm_reg_map_addr_range,
    )
    from pyuvm.reg.uvm_reg_sequence import uvm_reg_frontdoor
    from pyuvm.reg.uvm_vreg import uvm_vreg
    from pyuvm.reg.uvm_vreg_field import uvm_vreg_field

__all__ = [
    "uvm_reg_map_info",
    "uvm_reg_transaction_order_policy",
    "uvm_reg_seq_base",
    "uvm_reg_map",
]
logger = logging.getLogger("RegModel")


class uvm_reg_map_info:
    def __init__(self):
        self.offset: uvm_reg_addr_t = 0
        self.rights: str = ""
        self.unmapped: bool = False
        self.addr: list[uvm_reg_addr_t] = list()
        self.frontdoor: uvm_reg_frontdoor = None
        self.mem_range: uvm_reg_map_addr_range = None
        self.is_initialized: bool = False


class uvm_reg_transaction_order_policy(uvm_object):
    def __init__(self, name: str = "policy"):
        super().__init__(name)
        raise NotImplementedError

    def order(self, q: list[uvm_reg_bus_op]) -> None:
        raise NotImplementedError


class uvm_reg_seq_base(uvm_sequence_base):
    def __init__(self, name: str = "uvm_reg_seq_base"):
        super().__init__(name)


class uvm_reg_map(uvm_object):
    _backdoor: ClassVar[uvm_reg_backdoor | None] = None

    def __init__(self, name: str = "uvm_reg_map"):
        if name == "":
            name = "default_map"
        super().__init__(name)
        self._base_addr: uvm_reg_addr_t = 0
        self._n_bytes: int = 0
        self._endian: uvm_endianness_e = None
        self._byte_addressing: bool = False
        # TODO: implement uvm_object_wrapper class
        # self._sequence_wrapper: uvm_object_wrapper = None
        self._adapter: uvm_reg_adapter = None
        self._sequencer: uvm_sequencer_base = None
        self._auto_predict: bool = False
        self._check_on_read: bool = False
        self._parent: uvm_reg_block = None
        self._system_n_bytes: int = 0
        self._parent_map: uvm_reg_map = None
        self._submaps: dict[uvm_reg_map, uvm_reg_addr_t] = dict()
        self._submap_rights: dict[uvm_reg_map, str] = dict()
        self._regs_info: dict[uvm_reg, uvm_reg_map_info] = dict()
        self._mems_info: dict[uvm_mem, uvm_reg_map_info] = dict()
        self._regs_by_offset: dict[uvm_reg_addr_t, uvm_reg] = dict()
        self._regs_by_offset_wo: dict[uvm_reg_addr_t, uvm_reg] = dict()
        self._mems_by_offset: dict[uvm_reg_map_addr_range, uvm_mem] = dict()
        self._policy: uvm_reg_transaction_order_policy = None

    def _init_address_map(self) -> None:
        bus_width = 0
        root_map = self.get_root_map()
        if self is root_map:
            self._regs_by_offset.clear()
            self._mems_by_offset.clear()
            self._regs_by_offset_wo.clear()
        for map in self._submaps:
            map._init_address_map()
        for reg, reg_info in self._regs_info.items():
            reg_info.is_initialized = True
            if not reg_info.unmapped:
                reg_access = reg._get_fields_access(self)
                bus_width, reg_addrs = self.get_physical_addresses(
                    reg_info.offset, 0, reg.get_n_bytes()
                )
                for addr in reg_addrs:
                    if (
                        addr in self._regs_by_offset
                        and root_map._regs_by_offset.get(addr) is not reg
                    ):
                        other_reg = root_map._regs_by_offset.get(addr)
                        other_reg_access = other_reg._get_fields_access(self)
                        if reg_access == "RO" and other_reg_access == "WO":
                            root_map._regs_by_offset[addr] = reg
                            root_map._regs_by_offset_wo[addr] = other_reg
                            # TODO: when callback are implemented
                            # uvm_reg_read_only_cb.add(reg)
                            # uvm_reg_write_only_cb.add(other_reg)
                        elif reg_access == "WO" and other_reg_access == "RO":
                            root_map._regs_by_offset[addr] = other_reg
                            root_map._regs_by_offset_wo[addr] = reg
                            # TODO: when callback are implemented
                            # uvm_reg_read_only_cb.add(other_reg)
                            # uvm_reg_write_only_cb.add(reg)
                        else:
                            logger.warning(
                                f"In map {repr(self.get_full_name())} "
                                f"register {repr(reg.get_full_name())} maps "
                                "to the same address as register "
                                f"{repr(other_reg.get_full_name())}: 0x{addr:X}"
                            )
                    else:
                        root_map._regs_by_offset[addr] = reg
                    # TODO: check memory overlap uvm_reg_map.svh:1619
                self._regs_info[reg].addr = reg_addrs
        for mem, mem_info in self._mems_info.items():
            raise NotImplementedError
        if bus_width == 0:
            bus_width = self._n_bytes
        self._system_n_bytes = bus_width

    @staticmethod
    def backdoor() -> uvm_reg_backdoor:
        if uvm_reg_map._backdoor is None:
            uvm_reg_map._backdoor = uvm_reg_backdoor("Backdoor")
        return uvm_reg_map._backdoor

    def configure(
        self,
        parent: uvm_reg_block,
        base_addr: uvm_reg_addr_t,
        n_bytes: int = None,
        endian: uvm_endianness_e = None,
        byte_addressing: bool = True,
    ) -> None:
        # TODO: Remove backward compatibility
        if n_bytes is None:
            warnings.warn("n_bytes not set, assuming 4 bytes", DeprecationWarning, 2)
            n_bytes = 4
        if endian is None:
            warnings.warn(
                "endian not set, assuming little endian", DeprecationWarning, 2
            )
            endian = uvm_endianness_e.UVM_LITTLE_ENDIAN
        # END
        self._parent = parent
        self._base_addr = base_addr
        self._n_bytes = n_bytes
        self._endian = endian
        self._byte_addressing = byte_addressing
        if self not in parent.get_maps():
            parent._add_map(self)

    def add_reg(
        self,
        rg: uvm_reg,
        offset: uvm_reg_addr_t,
        rights: str = "RW",
        unmapped: bool = False,
        frontdoor: uvm_reg_frontdoor = None,
    ) -> None:
        if rg in self._regs_info:
            logger.error(
                f"Register {repr(rg.get_name())} has already been added "
                f"to map {repr(self.get_full_name())}"
            )
        if rg.get_parent() != self.get_parent():
            logger.error(
                f"Register {repr(rg.get_name())} may not be added to "
                f"the address map {repr(self.get_full_name())}: they  "
                "are not in the same block"
            )
        rg.add_map(self)
        info = uvm_reg_map_info()
        info.offset = offset
        info.rights = rights
        info.unmapped = unmapped
        info.frontdoor = frontdoor
        info.is_initialized = False
        self._regs_info[rg] = info

    def add_mem(
        self,
        mem: uvm_mem,
        offset: uvm_reg_addr_t,
        rights: str = "RW",
        unmapped: bool = False,
        frontdoor: uvm_reg_frontdoor = None,
    ):
        raise NotImplementedError

    def add_submap(self, child_map: uvm_reg_map, offset: uvm_reg_addr_t) -> None:
        if not child_map:
            logger.error("Child map cannot be None")
        parent_map = child_map.get_parent_map()
        if parent_map:
            logger.error(
                f"Map {repr(child_map.get_full_name())} is already a child "
                f"of map {repr(parent_map.get_full_name())}"
            )
        child_n_bytes = child_map.get_n_bytes(uvm_hier_e.UVM_NO_HIER)
        if self._n_bytes > child_n_bytes:
            logger.warning(
                f"Adding {child_n_bytes}-bytes submap to "
                f"{repr(child_map.get_full_name())} {self._n_bytes}-bytes map "
                f"parent map {repr(self.get_full_name())}"
            )
        child_map._add_parent_map(self, offset)
        self.set_submap_offset(child_map, offset)

    def set_sequencer(
        self, sequencer: uvm_sequencer, adapter: uvm_reg_adapter = None
    ) -> None:
        if not sequencer:
            logger.error("None value specified for bus sequencer")
            return
        if not adapter:
            logger.info(
                f"Adapter not specified for map {repr(self.get_full_name())}. "
                "Accesses via this map will send abstract 'uvm_reg_item' "
                f"items to sequencer {repr(sequencer.get_full_name())}"
            )
        self._sequencer = sequencer
        self._adapter = adapter

    def set_submap_offset(self, submap: uvm_reg_map, offset: uvm_reg_addr_t) -> None:
        if not submap:
            logger.error("set_submap_offset: submap cannot be None")
            return
        self._submaps[submap] = offset
        if self._parent.is_locked():
            root_map = self.get_root_map()
            root_map._init_address_map()

    def get_submap_offset(self, submap: uvm_reg_map) -> uvm_reg_addr_t:
        try:
            return self._submaps[submap]
        except KeyError:
            logger.error(
                f"Map {repr(submap.get_full_name())} is not a submap of map "
                f"{repr(self.get_full_name())}"
            )
        except TypeError:
            logger.error("get_submap_offset: submap cannot be None")
        return -1

    def set_base_addr(self, offset: uvm_reg_addr_t) -> None:
        raise NotImplementedError

    def reset(self, kind: str = "SOFT") -> None:
        for reg in self.get_registers():
            reg.reset(kind)

    def _add_parent_map(self, parent_map: uvm_reg_map, offset: uvm_reg_addr_t) -> None:
        if not parent_map:
            logger.error("Parent map cannot be None")
            return
        if self._parent_map:
            logger.error(
                f"Map {repr(self.get_full_name())} is already a submap "
                f"of map {repr(self._parent_map.get_full_name())}"
            )
            return
        parent_map._submaps[self] = offset
        self._parent_map = parent_map

    def _verify_map_config(self) -> None:
        raise NotImplementedError

    def _set_reg_offset(
        self, reg: uvm_reg, offset: uvm_reg_addr_t, unmapped: bool
    ) -> None:
        if reg not in self._regs_info:
            logger.error(
                f"Cannot modify offset of register "
                f"{repr(reg.get_full_name())} in address map "
                f"{repr(self.get_full_name())} register is not "
                "mapped in that address map"
            )
            return
        info = self._regs_info[reg]
        blk = self.get_parent()
        root_map = self.get_root_map()
        # When block is locked we need to resolve the map. This is otherwise
        # handled by the init addresses when the block is locked
        if blk.is_locked():
            if not info.unmapped:
                for addr in info.addr:
                    if addr not in root_map._regs_by_offset_wo:
                        del root_map._regs_by_offset[addr]
                    else:
                        if root_map._regs_by_offset[addr] is reg:
                            root_map._regs_by_offset[addr] = (
                                root_map._regs_by_offset_wo[addr]
                            )
                            # TODO: callbacks
                            # uvm_reg_read_only_cbs::remove(rg);
                            # uvm_reg_write_only_cbs::remove(top_map.m_regs_by_offset[info.addr[i]]);
                        else:
                            # TODO: callbacks
                            # uvm_reg_write_only_cbs::remove(rg);
                            # uvm_reg_read_only_cbs::remove(top_map.m_regs_by_offset[info.addr[i]]);
                            pass
                        del root_map._regs_by_offset_wo[addr]
        # remapping
        if not unmapped:
            reg_access = reg._get_fields_access(self)
            bus_width, addrs = self.get_physical_addresses(offset, 0, reg.get_n_bytes())
            for addr in addrs:
                if (
                    addr in root_map._regs_by_offset
                    and root_map._regs_by_offset.get(addr) is not reg
                ):
                    reg2 = root_map._regs_by_offset.get(addr)
                    reg2_access = reg2._get_fields_access(self)
                    if reg_access == "RO" and reg2_access == "WO":
                        root_map._regs_by_offset[addr] = reg
                        root_map._regs_by_offset_wo[addr] = reg2
                        # TODO: callbacks
                        # uvm_reg_read_only_cbs::add(reg);
                        # uvm_reg_write_only_cbs::add(reg2);
                    elif reg_access == "WO" and reg2_access == "RO":
                        root_map._regs_by_offset[addr] = reg2
                        root_map._regs_by_offset_wo[addr] = reg
                        # TODO: callbacks
                        # uvm_reg_read_only_cbs::remove(reg2);
                        # uvm_reg_write_only_cbs::remove(reg2);
                    else:
                        logger.warning(
                            f"In map {repr(self.get_full_name())} "
                            f" register {repr(reg.get_full_name())} maps to same "
                            f"address as register "
                            f"{repr(root_map._regs_by_offset[addr].get_full_name())} "
                            f": 0x{addr:X}"
                        )
                else:
                    root_map._regs_by_offset[addr] = reg

                for range in root_map._mems_by_offset.keys():
                    if addr >= range.min and addr <= range.max:
                        logger.warning(
                            f"In map {repr(self.get_full_name())} "
                            f"register {repr(reg.get_full_name())} "
                            "overlaps with address range of memory"
                            f"{repr(root_map._mems_by_offset[range].get_full_name())} "
                            f": 0x{addr:X}"
                        )
            info.addr = addrs
        if unmapped:
            info.offset = -1
            info.unmapped = True
        else:
            info.offset = offset
            info.unmapped = False

    def _set_mem_offset(
        self, mem: uvm_mem, offset: uvm_reg_addr_t, unmapped: bool
    ) -> None:
        raise NotImplementedError

    def get_full_name(self) -> str:
        parent = self.get_parent()
        if parent is None:
            return self.get_name()
        else:
            return parent.get_full_name() + "." + self.get_name()

    def get_root_map(self) -> uvm_reg_map:
        if self._parent_map is None:
            return self
        else:
            return self._parent_map.get_root_map()

    def get_parent(self) -> uvm_reg_block:
        return self._parent

    def get_parent_map(self) -> uvm_reg_map:
        return self._parent_map

    def get_base_addr(self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> uvm_reg_addr_t:
        map = self.get_parent_map()
        if not map or hier == uvm_hier_e.UVM_NO_HIER:
            return self._base_addr
        return map.get_submap_offset(self) + map.get_base_addr(hier)

    def get_n_bytes(self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> int:
        if hier == uvm_hier_e.UVM_NO_HIER:
            return self._n_bytes
        else:
            return self._system_n_bytes

    def get_addr_unit_bytes(self) -> int:
        return 1 if self._byte_addressing else self._n_bytes

    def get_endian(self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> uvm_endianness_e:
        map = self.get_parent_map()
        if not map or hier == uvm_hier_e.UVM_NO_HIER:
            return self._endian
        return map.get_endian(hier)

    def get_sequencer(
        self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER
    ) -> uvm_sequencer_base:
        map = self.get_parent_map()
        if not map or hier == uvm_hier_e.UVM_NO_HIER:
            return self._sequencer
        return map.get_sequencer(hier)

    def get_adapter(self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> uvm_reg_adapter:
        map = self.get_parent_map()
        if not map or hier == uvm_hier_e.UVM_NO_HIER:
            return self._adapter
        return map.get_adapter(hier)

    def get_submaps(self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> list[uvm_reg_map]:
        submaps = list()
        if hier == uvm_hier_e.UVM_HIER:
            for submap in self._submaps:
                submaps += submap.get_submaps(hier)
        return submaps + list(self._submaps.keys())

    def get_registers(self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> list[uvm_reg]:
        registers = list()
        if hier == uvm_hier_e.UVM_HIER:
            for submap in self._submaps:
                registers += submap.get_registers(hier)
        return registers + list(self._regs_info.keys())

    def get_fields(self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> list[uvm_reg_field]:
        fields = list()
        if hier == uvm_hier_e.UVM_HIER:
            for submap in self._submaps:
                fields += submap.get_fields(hier)
        for reg in self.registers(hier):
            fields += reg.get_fields(hier)
        return fields

    def get_memories(self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> list[uvm_mem]:
        memories = list()
        if hier == uvm_hier_e.UVM_HIER:
            for submap in self._submaps:
                memories += submap.get_memories(hier)
        return memories + list(self._mems_info.keys())

    def get_virtual_registers(
        self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER
    ) -> list[uvm_vreg]:
        virtual_registers = list()
        for mem in self.get_memories(hier):
            virtual_registers += mem.get_virtual_registers(hier)
        return virtual_registers

    def get_virtual_fields(
        self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER
    ) -> list[uvm_vreg_field]:
        virtual_register = list()
        for vreg in self.get_virtual_registers(hier):
            virtual_register += vreg.get_fields(hier)
        return virtual_register

    def get_reg_map_info(
        self, rg: uvm_reg, error: bool = True
    ) -> uvm_reg_map_info | None:
        if rg not in self._regs_info:
            if error:
                logger.error(
                    f"Register {repr(rg.get_name())} not in map {repr(self.get_full_name())}"
                )
            return
        map_info = self._regs_info[rg]
        if not map_info.is_initialized:
            logger.warning(
                f"Map {repr(self.get_full_name())} does not seem to "
                "initialized correctly, check that the top "
                "register model is locked()"
            )
        return map_info

    def get_mem_map_info(self, mem: uvm_mem, error: bool) -> uvm_reg_map_info:
        raise NotImplementedError

    def get_size(self) -> int:
        raise NotImplementedError

    def get_physical_addresses(
        self,
        base_addr: uvm_reg_addr_t,
        mem_offset: uvm_reg_addr_t,
        n_bytes: int,
    ) -> tuple[int, list[uvm_reg_addr_t]]:
        rval, addrs, _ = self._get_physical_addresses_to_map(
            base_addr, mem_offset, n_bytes, None
        )
        return (rval, addrs)

    def get_reg_by_offset(
        self, offset: uvm_reg_addr_t, read: bool = True
    ) -> uvm_reg | None:
        if not self.get_parent().is_locked():
            logger.error(
                "Cannot get register by offset : block "
                f"{repr(self.get_parent().get_full_name())} is not locked"
            )
            return None
        if not read and offset in self._regs_by_offset_wo:
            return self._regs_by_offset_wo[offset]
        if offset in self._regs_by_offset:
            return self._regs_by_offset[offset]
        return None

    def get_mem_by_offset(self, offset: uvm_reg_addr_t) -> uvm_mem:
        raise NotImplementedError

    def set_auto_predict(self, on: bool = True) -> None:
        self._auto_predict = on

    def get_auto_predict(self) -> bool:
        return self._auto_predict

    def set_check_on_read(self, on: bool = True) -> None:
        self._check_on_read = on
        for submap in self._submaps.keys():
            submap.set_check_on_read(on)

    def get_check_on_read(self) -> bool:
        return self._check_on_read

    async def do_bus_write(
        self, rw: uvm_reg_item, sequencer: uvm_sequencer_base, adapter: uvm_reg_adapter
    ) -> None:
        reg = rw.get_element()
        bus_width, addrs, _ = self._get_physical_addresses_to_map(
            self._regs_info[reg].offset, 0x0, reg.get_n_bytes(), None, None
        )
        bus_op = uvm_reg_bus_op()
        bus_op.kind = uvm_access_e.UVM_WRITE
        bus_op.addr = addrs[0]
        bus_op.data = rw.get_value()
        bus_op.n_bits = bus_width * 8
        # TODO: Support byte enable
        bus_op.byte_en = (1 << bus_width) - 1
        adapter.set_item(rw)
        bus_seq_item = adapter.reg2bus(bus_op)
        adapter.set_item(None)
        sequence: uvm_sequence = adapter.parent_sequence
        sequence.sequencer = sequencer
        await sequence.start_item(bus_seq_item)
        await sequence.finish_item(bus_seq_item)
        adapter.bus2reg(bus_seq_item, bus_op)
        rw.set_value(bus_op.data)
        rw.set_status(bus_op.status)

    async def do_bus_read(
        self, rw: uvm_reg_item, sequencer: uvm_sequencer_base, adapter: uvm_reg_adapter
    ) -> None:
        reg = rw.get_element()
        bus_width, addrs, _ = self._get_physical_addresses_to_map(
            self._regs_info[reg].offset, 0x0, reg.get_n_bytes(), None, None
        )
        bus_op = uvm_reg_bus_op()
        bus_op.kind = uvm_access_e.UVM_READ
        bus_op.addr = addrs[0]
        bus_op.data = rw.get_value()
        bus_op.n_bits = bus_width * 8
        bus_op.byte_en = (1 << bus_width) - 1
        adapter.set_item(rw)
        bus_seq_item = adapter.reg2bus(bus_op)
        adapter.set_item(None)
        sequence: uvm_sequence = adapter.parent_sequence
        sequence.sequencer = sequencer
        await sequence.start_item(bus_seq_item)
        await sequence.finish_item(bus_seq_item)
        adapter.bus2reg(bus_seq_item, bus_op)
        rw.set_value(bus_op.data)
        rw.set_status(bus_op.status)

    async def do_write(self, rw: uvm_reg_item) -> None:
        system_map = self.get_root_map()
        adapter = system_map.get_adapter()
        sequencer = system_map.get_sequencer()
        # TODO: See official UVM implementation for special cases
        if adapter and adapter.parent_sequence:
            rw.set_parent_sequence(adapter.parent_sequence)
        else:
            base_seq = uvm_sequence("base_seq")
            rw.set_parent_sequence(base_seq)
            adapter.parent_sequence = base_seq
        # if not rw.get_parent_sequence():
        #     raise NotImplementedError
        if not adapter:
            raise NotImplementedError
        await self.do_bus_write(rw, sequencer, adapter)

    async def do_read(self, rw: uvm_reg_item) -> None:
        system_map = self.get_root_map()
        adapter = system_map.get_adapter()
        sequencer = system_map.get_sequencer()
        # TODO: See official UVM implementation for special cases
        if adapter and adapter.parent_sequence:
            rw.set_parent_sequence(adapter.parent_sequence)
        else:
            base_seq = uvm_sequence("base_seq")
            rw.set_parent_sequence(base_seq)
            adapter.parent_sequence = base_seq
        # if not rw.get_parent_sequence():
        #     raise NotImplementedError
        if not adapter:
            raise NotImplementedError
        await self.do_bus_read(rw, sequencer, adapter)

    def _get_bus_info(self, rw: uvm_reg_item) -> tuple[uvm_reg_map_info, int, int, int]:
        map_info = None
        size = 0
        lsb = 0
        skip = 0
        kind = rw.get_element_kind()
        if kind == uvm_elem_kind_e.UVM_MEM:
            mem: uvm_mem = rw.get_element()
            if not mem:
                raise UVMFatalError(
                    f"uvm_reg_item 'element_kind' is UVM_MEM but 'element' "
                    f"does not point to a memory: {rw.get_name()}"
                )
            map_info = self.get_mem_map_info(mem)
            size = mem.get_n_bits()
        elif kind == uvm_elem_kind_e.UVM_REG:
            reg: uvm_reg = rw.get_element()
            if not reg:
                raise UVMFatalError(
                    f"uvm_reg_item 'element_kind' is UVM_REG but 'element' "
                    f"does not point to a register: {rw.get_name()}"
                )
            map_info = self.get_reg_map_info(reg)
            size = reg.get_n_bits()
        elif kind == uvm_elem_kind_e.UVM_FIELD:
            field: uvm_reg_field = rw.get_element()
            if not field:
                raise UVMFatalError(
                    f"uvm_reg_item 'element_kind' is UVM_FIELD but 'element' "
                    f"does not point to a field: {rw.get_name()}"
                )
            map_info = self.get_field_map_info(field.get_parent())
            size = field.get_n_bits()
            lsb = field.get_lsb_pos()
            skip = int(lsb / (self.get_n_bytes() * 8))
        return (map_info, size, lsb, skip)

    def set_transaction_order_policy(
        self, pol: uvm_reg_transaction_order_policy
    ) -> None:
        self._policy = pol

    def get_transaction_order_policy(self) -> uvm_reg_transaction_order_policy:
        return self._policy

    def _get_physical_addresses_to_map(
        self,
        base_addr: uvm_reg_addr_t,
        mem_offset: uvm_reg_addr_t,
        n_bytes: int,
        parent_map: uvm_reg_map,
        mem: uvm_mem = None,
    ) -> tuple[int, list[uvm_reg_addr_t], int]:
        byte_offset: int = 0
        bus_width = self.get_n_bytes(uvm_hier_e.UVM_NO_HIER)
        map = self.get_parent_map()

        # If not in target map -> recurse upward
        if map is None:
            lbase_addr = self.get_base_addr(uvm_hier_e.UVM_NO_HIER)
        else:
            lbase_addr = map.get_submap_offset(self)

        if map is not parent_map:
            if mem_offset:
                base_addr += mem_offset * mem.get_n_bytes() / self.get_addr_unit_bytes()
            laddr = (
                lbase_addr
                + base_addr * self.get_addr_unit_bytes() / map.get_addr_unit_bytes()
            )
            lb = (base_addr * self.get_addr_unit_bytes()) % map.get_addr_unit_bytes()
            byte_offset += lb
            # recursive call one level up
            return map._get_physical_addresses_to_map(
                laddr, 0, n_bytes + lb, parent_map, byte_offset
            )

        # In target map
        n_addrs = ceildiv(n_bytes, bus_width)
        local_addr = [None] * n_addrs
        lbase_addr2 = base_addr
        if mem_offset:
            if mem and mem.get_n_bytes() > self.get_addr_unit_bytes():
                lbase_addr2 = (
                    base_addr
                    + mem_offset * mem.get_n_bytes() / self.get_addr_unit_bytes()
                )
                byte_offset += (
                    mem_offset * mem.get_n_bytes() % self.get_addr_unit_bytes()
                )
            else:
                lbase_addr2 = base_addr + mem_offset

        # Build address list per endian mode
        endian = self.get_endian(uvm_hier_e.UVM_NO_HIER)
        if endian == uvm_endianness_e.UVM_LITTLE_ENDIAN:
            for i, _ in enumerate(local_addr):
                local_addr[i] = lbase_addr2 + i * bus_width / self.get_addr_unit_bytes()
        elif endian == uvm_endianness_e.UVM_BIG_ENDIAN:
            for i, _ in enumerate(local_addr):
                local_addr[i] = (
                    lbase_addr2
                    + (len(local_addr) - i - 1) * bus_width / self.get_addr_unit_bytes()
                )
        elif endian in (
            uvm_endianness_e.UVM_LITTLE_FIFO,
            uvm_endianness_e.UVM_BIG_FIFO,
        ):
            local_addr = lbase_addr2 * n_addrs
        else:
            logger.error(
                "Map has no specified endianness. Cannot access "
                f"{repr(n_bytes)} bytes register via its {repr(bus_width)} "
                f"byte {repr(self.get_full_name())} interface"
            )

        # Scale into upper map's address space
        addr = [int(a + lbase_addr) for a in local_addr]
        return bus_width, addr, byte_offset

    async def perform_accesses(
        self,
        accesses: list[uvm_reg_bus_op],
        rw: uvm_reg_item,
        adapter: uvm_reg_adapter,
        sequencer: uvm_sequencer_base,
    ) -> None:
        raise NotImplementedError

    def unregister(self) -> None:
        raise NotImplementedError

    def clone_and_update(self, rights: str) -> uvm_reg_map:
        raise NotImplementedError

    # TODO: Remove backward compatibility
    def get_offset(self) -> uvm_reg_addr_t:
        warnings.warn(
            "The 'get_offset' method is deprecated, use 'get_base_addr' instead",
            DeprecationWarning,
            2,
        )
        return self.get_base_addr()

    def set_adapter(self, adapter) -> None:
        warnings.warn(
            "The 'set_adapter' method is deprecated, use "
            "'set_sequencer(seqr, adapter)' instead",
            DeprecationWarning,
            2,
        )
        self._adapter = adapter

    # TODO: Should this be dunder methods?
    # extern virtual function string      convert2string();
    # extern virtual function uvm_object  clone();
    # extern virtual function void        do_print (uvm_printer printer);
    # extern virtual function void        do_copy   (uvm_object rhs);


def ceildiv(a: int, b: int) -> int:
    "Ceils the division of a by b"
    return -(a // -b)
