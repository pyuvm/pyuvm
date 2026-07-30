from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from math import gcd
from typing import TYPE_CHECKING, ClassVar

from pyuvm._error_classes import UVMFatalError
from pyuvm._reg.uvm_reg_backdoor import uvm_reg_backdoor
from pyuvm._reg.uvm_reg_item import uvm_reg_bus_op
from pyuvm._reg.uvm_reg_model import (
    uvm_access_e,
    uvm_elem_kind_e,
    uvm_endianness_e,
    uvm_hier_e,
    uvm_reg_map_addr_range,
    uvm_status_e,
)
from pyuvm._reg.uvm_reg_reporting import (
    uvm_reg_report_error as _report_error,
)
from pyuvm._reg.uvm_reg_reporting import (
    uvm_reg_report_warning as _report_warning,
)
from pyuvm._s05_base_classes import uvm_object
from pyuvm._s14_15_python_sequences import (
    uvm_sequence,
    uvm_sequence_base,
    uvm_sequencer,
)

if TYPE_CHECKING:
    from pyuvm import uvm_sequencer_base
    from pyuvm._reg.uvm_mem import uvm_mem
    from pyuvm._reg.uvm_reg import uvm_reg
    from pyuvm._reg.uvm_reg_adapter import uvm_reg_adapter
    from pyuvm._reg.uvm_reg_block import uvm_reg_block
    from pyuvm._reg.uvm_reg_field import uvm_reg_field
    from pyuvm._reg.uvm_reg_item import uvm_reg_item
    from pyuvm._reg.uvm_reg_model import (
        uvm_reg_addr_t,
        uvm_reg_map_addr_range,
    )
    from pyuvm._reg.uvm_reg_sequence import uvm_reg_frontdoor
    from pyuvm._reg.uvm_vreg import uvm_vreg
    from pyuvm._reg.uvm_vreg_field import uvm_vreg_field

__all__ = [
    "uvm_reg_map_info",
    "uvm_reg_transaction_order_policy",
    "uvm_reg_seq_base",
    "uvm_reg_map",
]
logger = logging.getLogger("RegModel")


def _first_progression_overlap(
    first_a: int,
    stride_a: int,
    count_a: int,
    first_b: int,
    stride_b: int,
    count_b: int,
) -> int | None:
    """Return the first address shared by two finite arithmetic progressions.

    A mapped memory is represented by one progression per physical byte lane.
    For example, a lane whose first address is 0x100 and whose element stride
    is four occupies 0x100, 0x104, 0x108, ... .  Map initialization needs to
    know whether two such lanes ever occupy the same address so that it can
    report memory-to-memory overlap accurately.

    Merely comparing the minimum and maximum addresses is insufficient because
    the progressions can contain holes.  Expanding every memory element into a
    dictionary would preserve those holes, but would also consume storage
    proportional to memory depth.  This helper instead solves

        first_a + stride_a * i == first_b + stride_b * j

    for finite index ranges using the greatest common divisor and the Chinese
    Remainder Theorem.  The GCD test determines whether the infinite
    progressions can intersect; the modular inverse produces one intersection;
    and ``period`` advances that solution to the first address inside both
    finite ranges.

    A zero stride represents a progression containing only one distinct
    address, which occurs for a one-element memory.  The explicit zero-stride
    cases also avoid taking a modular inverse with a zero modulus.

    Returns:
        The lowest shared address within both finite progressions, or ``None``
        when they do not intersect.
    """
    last_a = first_a + stride_a * (count_a - 1)
    last_b = first_b + stride_b * (count_b - 1)
    lower = max(first_a, first_b)
    upper = min(last_a, last_b)
    if lower > upper:
        return None
    if stride_a == 0:
        if stride_b == 0:
            return first_a if first_a == first_b else None
        delta = first_a - first_b
        return first_a if delta >= 0 and delta % stride_b == 0 else None
    if stride_b == 0:
        delta = first_b - first_a
        return first_b if delta >= 0 and delta % stride_a == 0 else None

    common = gcd(stride_a, stride_b)
    difference = first_b - first_a
    if difference % common:
        return None
    reduced_b = stride_b // common
    multiplier = 0
    if reduced_b > 1:
        multiplier = (
            (difference // common) * pow(stride_a // common, -1, reduced_b)
        ) % reduced_b
    period = stride_a * reduced_b
    candidate = (first_a + stride_a * multiplier) % period
    if candidate < lower:
        candidate += ((lower - candidate + period - 1) // period) * period
    return candidate if candidate <= upper else None


@dataclass(frozen=True)
class _uvm_mem_address_set:
    """Compact description of all physical addresses occupied by a memory.

    ``uvm_reg_map.get_physical_addresses()`` can return several addresses for
    one memory element, typically one per bus byte lane.  ``first_addresses``
    stores those addresses for element zero, while ``element_strides`` stores
    the difference between the corresponding addresses of elements zero and
    one.  Each pair therefore describes one finite arithmetic progression
    containing ``size`` addresses.

    The register map uses this descriptor for three operations:

    * ``contains()`` resolves a bus address to its mapped memory without
      incorrectly filling gaps between strided elements.
    * ``first_overlap()`` detects exact memory-to-memory collisions during map
      initialization.
    * The ``min`` and ``max`` bounds provide a cheap rejection test before the
      exact progression calculations.

    Keeping one descriptor per memory makes lookup metadata proportional to
    the number and width of mapped memories, rather than their total number of
    elements.  This is important for models containing very large memories.
    """

    mem: uvm_mem
    first_addresses: tuple[uvm_reg_addr_t, ...]
    element_strides: tuple[int, ...]
    size: int
    min: uvm_reg_addr_t
    max: uvm_reg_addr_t

    @classmethod
    def create(
        cls,
        mem: uvm_mem,
        first_addresses: list[uvm_reg_addr_t],
        second_addresses: list[uvm_reg_addr_t] | None,
    ) -> _uvm_mem_address_set:
        if second_addresses is None:
            strides = tuple(0 for _ in first_addresses)
        else:
            strides = tuple(
                second - first
                for first, second in zip(first_addresses, second_addresses)
            )
        final_addresses = [
            first + stride * (mem.get_size() - 1)
            for first, stride in zip(first_addresses, strides)
        ]
        all_bounds = [*first_addresses, *final_addresses]
        return cls(
            mem,
            tuple(first_addresses),
            strides,
            mem.get_size(),
            min(all_bounds),
            max(all_bounds),
        )

    def contains(self, address: uvm_reg_addr_t) -> bool:
        if address < self.min or address > self.max:
            return False
        for first, stride in zip(self.first_addresses, self.element_strides):
            if stride == 0:
                if address == first:
                    return True
                continue
            delta = address - first
            if delta >= 0 and delta % stride == 0 and delta // stride < self.size:
                return True
        return False

    def first_overlap(self, other: _uvm_mem_address_set) -> int | None:
        if self.max < other.min or other.max < self.min:
            return None
        for first_a, stride_a in zip(self.first_addresses, self.element_strides):
            for first_b, stride_b in zip(other.first_addresses, other.element_strides):
                overlap = _first_progression_overlap(
                    first_a,
                    stride_a,
                    self.size,
                    first_b,
                    stride_b,
                    other.size,
                )
                if overlap is not None:
                    return overlap
        return None


class uvm_reg_map_info:
    def __init__(self):
        self.offset: uvm_reg_addr_t = 0
        self.rights: str = ""
        self.unmapped: bool = False
        self.addr: list[uvm_reg_addr_t] = list()
        self.frontdoor: uvm_reg_frontdoor = None
        self.mem_range: uvm_reg_map_addr_range = None
        self.stride: int = 1
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
        self._mems_by_offset: dict[uvm_mem, _uvm_mem_address_set] = dict()
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
                            _report_warning(
                                self,
                                "REG_MAP",
                                f"In map {repr(self.get_full_name())} "
                                f"register {repr(reg.get_full_name())} maps "
                                "to the same address as register "
                                f"{repr(other_reg.get_full_name())}: 0x{addr:X}",
                            )
                    else:
                        root_map._regs_by_offset[addr] = reg
                    # TODO: check memory overlap uvm_reg_map.svh:1619
                self._regs_info[reg].addr = reg_addrs
        for mem, mem_info in self._mems_info.items():
            self._initialize_memory(mem, mem_info)
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
            _report_error(
                self,
                "REG_MAP",
                f"Register {repr(rg.get_name())} has already been added "
                f"to map {repr(self.get_full_name())}",
            )
        if rg.get_parent() != self.get_parent():
            _report_error(
                self,
                "REG_MAP",
                f"Register {repr(rg.get_name())} may not be added to "
                f"the address map {repr(self.get_full_name())}: they  "
                "are not in the same block",
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
    ) -> None:
        if mem in self._mems_info:
            _report_error(
                self,
                "REG_MAP",
                f"Memory {repr(mem.get_name())} has already been added "
                f"to map {repr(self.get_full_name())}",
            )
            return
        if mem.get_parent() is not self.get_parent():
            _report_error(
                self,
                "REG_MAP",
                f"Memory {repr(mem.get_name())} may not be added to "
                f"address map {repr(self.get_full_name())}: they are not "
                "in the same block",
            )
            return
        rights = rights.upper()
        if rights not in ("RW", "RO", "WO"):
            _report_error(
                self,
                "REG_MAP",
                f"Memory {repr(mem.get_name())} has invalid map rights "
                f"{repr(rights)}; using 'RW'",
            )
            rights = "RW"
        info = uvm_reg_map_info()
        info.offset = offset
        info.rights = rights
        info.unmapped = unmapped
        info.frontdoor = frontdoor
        info.stride = max(1, ceildiv(mem.get_n_bytes(), self.get_addr_unit_bytes()))
        self._mems_info[mem] = info
        mem.add_map(self)

    def _memory_element_addresses(
        self, mem: uvm_mem, info: uvm_reg_map_info, element_offset: int
    ) -> list[uvm_reg_addr_t]:
        _, addresses = self.get_physical_addresses(
            info.offset + element_offset * info.stride, 0, mem.get_n_bytes()
        )
        return addresses

    def _initialize_memory(self, mem: uvm_mem, info: uvm_reg_map_info) -> None:
        root_map = self.get_root_map()
        info.is_initialized = True
        if info.unmapped:
            info.addr = []
            info.mem_range = None
            return

        info.addr = self._memory_element_addresses(mem, info, 0)
        second_addresses = None
        if mem.get_size() > 1:
            second_addresses = self._memory_element_addresses(mem, info, 1)
        address_set = _uvm_mem_address_set.create(mem, info.addr, second_addresses)
        info.mem_range = uvm_reg_map_addr_range(
            address_set.min, address_set.max, info.stride
        )
        for other_mem, other_set in root_map._mems_by_offset.items():
            overlap = address_set.first_overlap(other_set)
            if overlap is not None and other_mem is not mem:
                _report_warning(
                    self,
                    "REG_MAP",
                    f"In map {repr(self.get_full_name())} memory "
                    f"{repr(mem.get_full_name())} overlaps memory "
                    f"{repr(other_mem.get_full_name())} at 0x{overlap:X}",
                )
        for addr, reg in root_map._regs_by_offset.items():
            if not address_set.contains(addr):
                continue
            _report_warning(
                self,
                "REG_MAP",
                f"In map {repr(self.get_full_name())} memory "
                f"{repr(mem.get_full_name())} overlaps register "
                f"{repr(reg.get_full_name())} at 0x{addr:X}",
            )
        root_map._mems_by_offset[mem] = address_set

    def add_submap(self, child_map: uvm_reg_map, offset: uvm_reg_addr_t) -> None:
        if not child_map:
            _report_error(self, "REG_MAP", "Child map cannot be None")
            return
        parent_map = child_map.get_parent_map()
        if parent_map:
            _report_error(
                self,
                "REG_MAP",
                f"Map {repr(child_map.get_full_name())} is already a child "
                f"of map {repr(parent_map.get_full_name())}",
            )
        child_n_bytes = child_map.get_n_bytes(uvm_hier_e.UVM_NO_HIER)
        if self._n_bytes > child_n_bytes:
            _report_warning(
                self,
                "REG_MAP",
                f"Adding {child_n_bytes}-bytes submap to "
                f"{repr(child_map.get_full_name())} {self._n_bytes}-bytes map "
                f"parent map {repr(self.get_full_name())}",
            )
        child_map._add_parent_map(self, offset)
        self.set_submap_offset(child_map, offset)

    def set_sequencer(
        self, sequencer: uvm_sequencer, adapter: uvm_reg_adapter = None
    ) -> None:
        if not sequencer:
            _report_error(self, "REG_MAP", "None value specified for bus sequencer")
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
            _report_error(self, "REG_MAP", "set_submap_offset: submap cannot be None")
            return
        self._submaps[submap] = offset
        if self._parent.is_locked():
            root_map = self.get_root_map()
            root_map._init_address_map()

    def get_submap_offset(self, submap: uvm_reg_map) -> uvm_reg_addr_t:
        if submap is None:
            _report_error(self, "REG_MAP", "get_submap_offset: submap cannot be None")
            return -1
        try:
            return self._submaps[submap]
        except KeyError:
            _report_error(
                self,
                "REG_MAP",
                f"Map {repr(submap.get_full_name())} is not a submap of map "
                f"{repr(self.get_full_name())}",
            )
        return -1

    def set_base_addr(self, offset: uvm_reg_addr_t) -> None:
        raise NotImplementedError

    def reset(self, kind: str = "SOFT") -> None:
        for reg in self.get_registers():
            reg.reset(kind)

    def _add_parent_map(self, parent_map: uvm_reg_map, offset: uvm_reg_addr_t) -> None:
        if not parent_map:
            _report_error(self, "REG_MAP", "Parent map cannot be None")
            return
        if self._parent_map:
            _report_error(
                self,
                "REG_MAP",
                f"Map {repr(self.get_full_name())} is already a submap "
                f"of map {repr(self._parent_map.get_full_name())}",
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
            _report_error(
                self,
                "REG_MAP",
                f"Cannot modify offset of register "
                f"{repr(reg.get_full_name())} in address map "
                f"{repr(self.get_full_name())} register is not "
                "mapped in that address map",
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
                        _report_warning(
                            self,
                            "REG_MAP",
                            f"In map {repr(self.get_full_name())} "
                            f" register {repr(reg.get_full_name())} maps to same "
                            f"address as register "
                            f"{repr(root_map._regs_by_offset[addr].get_full_name())} "
                            f": 0x{addr:X}",
                        )
                else:
                    root_map._regs_by_offset[addr] = reg

                for mem, address_set in root_map._mems_by_offset.items():
                    if address_set.contains(addr):
                        _report_warning(
                            self,
                            "REG_MAP",
                            f"In map {repr(self.get_full_name())} "
                            f"register {repr(reg.get_full_name())} "
                            "overlaps with memory "
                            f"{repr(mem.get_full_name())} "
                            f": 0x{addr:X}",
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
        if mem not in self._mems_info:
            _report_error(
                self,
                "REG_MAP",
                f"Cannot modify offset of memory {repr(mem.get_full_name())} "
                f"in address map {repr(self.get_full_name())}: memory is not mapped",
            )
            return
        info = self._mems_info[mem]
        info.offset = offset if not unmapped else -1
        info.unmapped = unmapped
        info.is_initialized = False
        if self.get_parent().is_locked():
            self.get_root_map()._init_address_map()

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
                _report_error(
                    self,
                    "REG_MAP",
                    f"Register {repr(rg.get_name())} not in map {repr(self.get_full_name())}",
                )
            return
        map_info = self._regs_info[rg]
        if not map_info.is_initialized:
            _report_warning(
                self,
                "REG_MAP",
                f"Map {repr(self.get_full_name())} does not seem to "
                "initialized correctly, check that the top "
                "register model is locked()",
            )
        return map_info

    def get_mem_map_info(
        self, mem: uvm_mem, error: bool = True
    ) -> uvm_reg_map_info | None:
        if mem not in self._mems_info:
            if error:
                _report_error(
                    self,
                    "REG_MAP",
                    f"Memory {repr(mem.get_name())} not in map "
                    f"{repr(self.get_full_name())}",
                )
            return None
        info = self._mems_info[mem]
        if not info.is_initialized:
            _report_warning(
                self,
                "REG_MAP",
                f"Map {repr(self.get_full_name())} does not seem to be "
                "initialized correctly; check that the top register model is locked",
            )
        return info

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
            _report_error(
                self,
                "REG_MAP",
                "Cannot get register by offset : block "
                f"{repr(self.get_parent().get_full_name())} is not locked",
            )
            return None
        if not read and offset in self._regs_by_offset_wo:
            return self._regs_by_offset_wo[offset]
        if offset in self._regs_by_offset:
            return self._regs_by_offset[offset]
        return None

    def get_mem_by_offset(self, offset: uvm_reg_addr_t) -> uvm_mem | None:
        if not self.get_parent().is_locked():
            _report_error(
                self,
                "REG_MAP",
                "Cannot get memory by offset: block "
                f"{repr(self.get_parent().get_full_name())} is not locked",
            )
            return None
        address_sets = self.get_root_map()._mems_by_offset.values()
        for address_set in reversed(tuple(address_sets)):
            if address_set.contains(offset):
                return address_set.mem
        return None

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

    def _get_bus_access_config(
        self, rw: uvm_reg_item
    ) -> tuple[uvm_sequencer_base, uvm_reg_adapter]:
        system_map = self.get_root_map()
        adapter = system_map.get_adapter()
        sequencer = system_map.get_sequencer()
        element = rw.get_element()
        element_name = (
            element.get_full_name()
            if element is not None and hasattr(element, "get_full_name")
            else rw.get_name()
        )
        map_name = system_map.get_full_name()
        if adapter is None:
            raise UVMFatalError(
                f"Register map {repr(map_name)} has no adapter configured for "
                f"frontdoor access to {repr(element_name)}. Call "
                "set_sequencer(sequencer, adapter) before using register "
                "frontdoor reads or writes."
            )
        if sequencer is None:
            raise UVMFatalError(
                f"Register map {repr(map_name)} has no sequencer configured for "
                f"frontdoor access to {repr(element_name)}. Call "
                "set_sequencer(sequencer, adapter) before using register "
                "frontdoor reads or writes."
            )
        return sequencer, adapter

    def _get_bus_sequence(
        self, rw: uvm_reg_item, adapter: uvm_reg_adapter
    ) -> uvm_sequence:
        sequence = adapter.parent_sequence
        if sequence is None:
            sequence = uvm_sequence("base_seq")
        if not hasattr(sequence, "start_item") or not hasattr(sequence, "finish_item"):
            raise UVMFatalError(
                f"Adapter {repr(adapter.get_full_name())} parent_sequence must "
                "provide start_item() and finish_item()."
            )
        rw.set_parent_sequence(sequence)
        return sequence

    def _make_bus_op(
        self,
        rw: uvm_reg_item,
        access_kind: uvm_access_e,
        adapter: uvm_reg_adapter,
    ) -> uvm_reg_bus_op:
        element = rw.get_element()
        if rw.get_element_kind() == uvm_elem_kind_e.UVM_MEM:
            info = self._mems_info[element]
            addrs = self._memory_element_addresses(element, info, rw.get_offset())
            bus_width = self.get_n_bytes()
            byte_offset = 0
        else:
            info = self._regs_info[element]
            bus_width, addrs, byte_offset = self._get_physical_addresses_to_map(
                info.offset, 0x0, element.get_n_bytes(), None, None
            )
        bus_op = uvm_reg_bus_op()
        bus_op.kind = access_kind
        bus_op.addr = addrs[0]
        bus_op.data = rw.get_value()
        bus_op.n_bits = min(element.get_n_bits(), bus_width * 8)
        bus_op.status = rw.get_status()
        if adapter.supports_byte_enable:
            byte_offset = int(byte_offset)
            available_bytes = max(bus_width - byte_offset, 0)
            enabled_bytes = min(ceildiv(bus_op.n_bits, 8), available_bytes)
            bus_op.byte_en = ((1 << enabled_bytes) - 1) << byte_offset
        else:
            bus_op.byte_en = -1
        return bus_op

    async def _send_bus_op(
        self,
        rw: uvm_reg_item,
        bus_op: uvm_reg_bus_op,
        sequencer: uvm_sequencer_base,
        adapter: uvm_reg_adapter,
    ) -> None:
        sequence = self._get_bus_sequence(rw, adapter)
        adapter.set_item(rw)
        try:
            bus_seq_item = adapter.reg2bus(bus_op)
        finally:
            adapter.set_item(None)
        if bus_seq_item is None:
            raise UVMFatalError(
                f"Adapter {repr(adapter.get_full_name())} reg2bus() returned None"
            )

        sequence.sequencer = sequencer
        await sequence.start_item(bus_seq_item)
        await sequence.finish_item(bus_seq_item)

        bus_rsp_item = bus_seq_item
        if adapter.provides_responses:
            bus_rsp_item = await sequence.get_response()
            if bus_rsp_item is None:
                raise UVMFatalError(
                    f"Adapter {repr(adapter.get_full_name())} expects bus "
                    "responses, but the sequencer returned None"
                )

        adapter.bus2reg(bus_rsp_item, bus_op)
        rw.set_value(bus_op.data)
        rw.set_status(bus_op.status)

    async def do_bus_write(
        self, rw: uvm_reg_item, sequencer: uvm_sequencer_base, adapter: uvm_reg_adapter
    ) -> None:
        bus_op = self._make_bus_op(rw, uvm_access_e.UVM_WRITE, adapter)
        await self._send_bus_op(rw, bus_op, sequencer, adapter)

    async def do_bus_read(
        self, rw: uvm_reg_item, sequencer: uvm_sequencer_base, adapter: uvm_reg_adapter
    ) -> None:
        bus_op = self._make_bus_op(rw, uvm_access_e.UVM_READ, adapter)
        await self._send_bus_op(rw, bus_op, sequencer, adapter)

    async def do_write(self, rw: uvm_reg_item) -> None:
        sequencer, adapter = self._get_bus_access_config(rw)
        await self.do_bus_write(rw, sequencer, adapter)

    async def do_read(self, rw: uvm_reg_item) -> None:
        sequencer, adapter = self._get_bus_access_config(rw)
        await self.do_bus_read(rw, sequencer, adapter)

    async def do_frontdoor(
        self, rw: uvm_reg_item, frontdoor: uvm_reg_frontdoor
    ) -> bool:
        prior_sequencer = frontdoor.sequencer
        sequencer = prior_sequencer
        if sequencer is None:
            sequencer = self.get_root_map().get_sequencer()
        if sequencer is None:
            element = rw.get_element()
            element_name = (
                element.get_full_name()
                if element is not None and hasattr(element, "get_full_name")
                else rw.get_name()
            )
            _report_error(
                self,
                "REG_FRONTDOOR",
                f"Custom frontdoor access to {element_name!r} has no sequencer; "
                "configure the frontdoor sequencer or the root-map sequencer",
            )
            rw.set_status(uvm_status_e.UVM_NOT_OK)
            return False
        if not isinstance(sequencer, uvm_sequencer):
            _report_error(
                self,
                "REG_FRONTDOOR",
                f"Custom frontdoor sequencer {sequencer!r} is not a uvm_sequencer",
            )
            rw.set_status(uvm_status_e.UVM_NOT_OK)
            return False

        await frontdoor.atomic_lock()
        try:
            frontdoor.rw_info = rw
            frontdoor.sequencer = sequencer
            await frontdoor.start(sequencer)
        except BaseException:
            rw.set_status(uvm_status_e.UVM_NOT_OK)
            raise
        finally:
            frontdoor.sequencer = prior_sequencer
            frontdoor.atomic_unlock()
        return True

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
            _report_error(
                self,
                "REG_MAP",
                "Map has no specified endianness. Cannot access "
                f"{repr(n_bytes)} bytes register via its {repr(bus_width)} "
                f"byte {repr(self.get_full_name())} interface",
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
