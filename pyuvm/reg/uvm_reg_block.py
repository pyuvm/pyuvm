from __future__ import annotations

import logging
import warnings
from asyncio import Event
from typing import TYPE_CHECKING, ClassVar

from pyuvm.error_classes import UVMFatalError
from pyuvm.reg.uvm_mem import uvm_mem
from pyuvm.reg.uvm_reg import uvm_reg
from pyuvm.reg.uvm_reg_field import uvm_reg_field
from pyuvm.reg.uvm_reg_map import uvm_reg_map
from pyuvm.reg.uvm_reg_model import (
    UVM_REG_DATA_WIDTH,
    uvm_check_e,
    uvm_coverage_model_e,
    uvm_door_e,
    uvm_hier_e,
)
from pyuvm.s05_base_classes import uvm_object

if TYPE_CHECKING:
    from pyuvm.reg.uvm_mem import uvm_mem
    from pyuvm.reg.uvm_reg_backdoor import uvm_reg_backdoor
    from pyuvm.reg.uvm_reg_model import (
        uvm_endianness_e,
        uvm_path_e,
        uvm_reg_addr_t,
        uvm_reg_cvr_t,
        uvm_reg_data_t,
        uvm_status_e,
    )
    from pyuvm.reg.uvm_vreg import uvm_vreg
    from pyuvm.reg.uvm_vreg_field import uvm_vreg_field
    from pyuvm.s14_15_python_sequences import uvm_sequence_base

__all__ = ["uvm_reg_block"]
logger = logging.getLogger("RegModel")


class uvm_reg_block(uvm_object):
    _root_names: ClassVar[list[str]] = list()
    _roots: ClassVar[list[uvm_reg_block]] = list()
    _enable_reg_lookup_cache: ClassVar[bool] = False
    _reg_block_registry: ClassVar[dict[str, uvm_reg_block]] = dict()

    def __init__(
        self, name: str = "", has_coverage: int = uvm_coverage_model_e.UVM_NO_COVERAGE
    ):
        super().__init__(name)
        self._name: str | None = None  # assign when model is locked
        self.default_path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR
        self._parent = None
        self._blks: dict[int, uvm_reg_block] = dict()
        self._regs: dict[int, uvm_reg] = dict()
        self._vregs: dict[int, uvm_vreg] = dict()
        self._mems: dict[int, uvm_mem] = dict()
        self._maps: list[uvm_reg_map] = list()
        self._locked: bool = False
        self._default_map: uvm_reg_map = None
        self._lock_model_complete: Event = Event()
        self._default_hdl_path = "RTL"
        self._hdl_paths_pool: dict[str, list[str]] = dict()

    def configure(self, parent: uvm_reg_block = None, hdl_path: str = "") -> None:
        self._parent = parent
        if parent:
            self._parent._add_block(self)
        self.add_hdl_path(hdl_path)

    def create_map(
        self,
        name: str,
        base_addr: uvm_reg_addr_t,
        n_bytes: int,
        endian: uvm_endianness_e,
        byte_addressing: bool = True,
    ) -> uvm_reg_map:
        map = uvm_reg_map(name)
        map.configure(self, base_addr, n_bytes, endian, byte_addressing)
        return map

    @staticmethod
    def check_data_width(width: int) -> bool:
        raise NotImplementedError

    def set_default_map(self, map: uvm_reg_map) -> None:
        if map not in self._maps:
            logger.error(f"Map {repr(map.get_name())} does not exist in block")
            return
        self._default_map = map

    def get_default_map(self) -> uvm_reg_map:
        return self._default_map

    def set_parent(self, parent: uvm_reg_block) -> None:
        self._parent = parent

    def _add_block(self, blk: uvm_reg_block) -> None:
        uid = blk.get_inst_id()
        if self.is_locked():
            logger.error("Cannot add subblock to a locked block model")
            return
        if uid in self._blks:
            logger.error(
                f"Subblock {repr(blk.get_name())} has already been "
                f"registered with block {repr(self.get_name())}"
            )
            return
        self._blks[uid] = blk
        if blk in self._roots:
            self._roots.remove(blk)
        if blk.get_name() in self._root_names:
            self._root_names.remove(blk.get_name())

    def _add_map(self, map: uvm_reg_map) -> None:
        if self.is_locked():
            logger.error("Cannot add map to locked model")
            return
        if map in self._maps:
            logger.error(
                f"Map {repr(map.get_name())} already exists in {repr(self.get_full_name())}"
            )
            return
        self._maps.append(map)
        if len(self._maps) == 1:
            self.set_default_map(map)

    def _add_register(self, reg: uvm_reg) -> None:
        uid = reg.get_inst_id()
        if self.is_locked():
            logger.error("Cannot add register to a locked block model")
            return
        if uid in self._regs:
            logger.error(
                f"Register {repr(reg.get_name())} has already been "
                f"registered with block {self.get_full_name()}"
            )
            return
        self._regs[uid] = reg

    def _add_virtual_register(self, vreg: uvm_vreg) -> None:
        raise NotImplementedError

    def lock_model(self) -> None:
        if self.is_locked():
            return
        self.set_lock(True)
        self._name = self.get_full_name()
        uvm_reg_block._reg_block_registry[self._name] = self

        for reg in self._regs.values():
            reg._lock_model()
        for mem in self._mems.values():
            mem._lock_model()
        for blk in self._blks.values():
            blk.lock_model()
        if self.get_parent():
            for map in self._maps:
                if map.get_parent_map() is None:
                    map._init_address_map()
        else:
            max_size = max(
                uvm_reg_field.get_max_size(),
                uvm_reg.get_max_size(),
                uvm_mem.get_max_size(),
            )
            if max_size > UVM_REG_DATA_WIDTH:
                raise UVMFatalError(
                    "Register model requires that "
                    f"UVM_REG_DATA_WIDTH be defined as {max_size} or greater. "
                    f"Currently defined as {UVM_REG_DATA_WIDTH}"
                )
            self._init_address_maps()
            names = uvm_reg_block._root_names.copy()
            while names:
                count = names.count(names[0])
                _ = names.pop(0)
                if count > 1:
                    logger.error(
                        f"There are {count} root register models "
                        "named {repr(name)}. The names of the root register "
                        "models have to be unique"
                    )
            # NOTE: Trigger event
            self._lock_model_complete.set()

    def unlock_model(self) -> None:
        raise NotImplementedError

    async def wait_for_lock(self) -> None:
        await self._lock_model_complete.wait()
        self._lock_model_complete.clear()

    def is_locked(self) -> bool:
        return self._locked

    def get_full_name(self) -> str:
        if self._name is None:
            parent = self.get_parent()
            if parent is None:
                return self.get_name()
            else:
                return parent.get_full_name() + "." + self.get_name()
        return self._name

    def get_parent(self) -> uvm_reg_block:
        return self._parent

    # TODO: Document definition compared to IEEE 1800.2
    @staticmethod
    def get_root_blocks() -> list[uvm_reg_block]:
        raise NotImplementedError

    # TODO: Document definition compared to IEEE 1800.2
    @staticmethod
    def find_blocks(
        name: str, root: uvm_reg_block = None, accessor: uvm_object = None
    ) -> list[uvm_reg_block]:
        raise NotImplementedError

    # TODO: Document definition compared to IEEE 1800.2
    def get_blocks(self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> list[uvm_reg_block]:
        blks = list()
        if hier == uvm_hier_e.UVM_HIER:
            for blk in self._blks.values():
                blks += blk.get_blocks(hier)
        return list(self._blks.values()) + blks

    # TODO: Document definition compared to IEEE 1800.2
    def get_maps(self) -> list[uvm_reg_map]:
        return self._maps

    # TODO: Document definition compared to IEEE 1800.2
    def get_registers(self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> list[uvm_reg]:
        regs = list()
        if hier == uvm_hier_e.UVM_HIER:
            for blk in self._blks.values():
                regs += blk.get_registers(hier)
        return list(self._regs.values()) + regs

    # TODO: Document definition compared to IEEE 1800.2
    def get_fields(self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> list[uvm_reg_field]:
        fields = list()
        for reg in self._regs.values():
            fields += reg.get_fields()
        if hier == uvm_hier_e.UVM_HIER:
            for blk in self._blks.values():
                fields += blk.get_fields(hier)
        return fields

    # TODO: Document definition compared to IEEE 1800.2
    def get_memories(self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> list[uvm_mem]:
        mems = list()
        if hier == uvm_hier_e.UVM_HIER:
            for blk in self._blks.values():
                mems += blk.get_memories(hier)
        return list(self._mems.values()) + mems

    # TODO: Document definition compared to IEEE 1800.2
    def get_virtual_registers(
        self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER
    ) -> list[uvm_vreg]:
        regs = list()
        if hier == uvm_hier_e.UVM_HIER:
            for blk in self._blks.values():
                regs += blk.get_virtual_registers(hier)
        return list(self._vregs.values()) + regs

    # TODO: Document definition compared to IEEE 1800.2
    def get_virtual_fields(
        self, hier: uvm_hier_e = uvm_hier_e.UVM_HIER
    ) -> list[uvm_vreg_field]:
        fields = list()
        if hier == uvm_hier_e.UVM_HIER:
            for blk in self._blks.values():
                fields += blk.get_virtual_fields(hier)
        for reg in self._vregs.values():
            fields += list(reg.get_fields())
        return fields

    def get_block_by_name(self, name: str) -> uvm_reg_block | None:
        if self.get_name() == name:
            return self
        for blk in self.get_blocks(uvm_hier_e.UVM_HIER):
            blk_name = blk.get_full_name()
            block = uvm_reg_block.get_block_by_name(f"{blk_name}.{name}")
            if block:
                return block
        logger.warning(
            f"Unable to locate block {repr(name)} in block {repr(self.get_full_name())}"
        )

    @staticmethod
    def get_block_by_full_name(name: str) -> uvm_reg_block | None:
        return uvm_reg_block._reg_block_registry.get(name)

    def get_map_by_name(self, name: str) -> uvm_reg_map:
        for map in self.get_maps():
            if map.get_name() == name:
                return map
        logger.warning(
            f"Unable to locate map {repr(name)} in block {repr(self.get_full_name())}"
        )

    def get_reg_by_name(self, name: str) -> uvm_reg | None:
        for reg in self.get_registers(uvm_hier_e.UVM_HIER):
            if reg.get_name() == name:
                return reg
        logger.warning(
            f"Unable to locate register {repr(name)} in block {repr(self.get_full_name())}"
        )

    def get_field_by_name(self, name: str) -> uvm_reg_field:
        for field in self.get_fields(uvm_hier_e.UVM_HIER):
            if field.get_name() == name:
                return field
        logger.warning(
            f"Unable to locate field {repr(name)} in block {repr(self.get_full_name())}"
        )

    def get_mem_by_name(self, name: str) -> uvm_mem | None:
        for mem in self.get_memories(uvm_hier_e.UVM_HIER):
            if mem.get_name() == name:
                return mem
        logger.warning(
            f"Unable to locate memory {repr(name)} in block {repr(self.get_full_name())}"
        )

    def get_vreg_by_name(self, name: str) -> uvm_vreg | None:
        for vreg in self.get_virtual_registers(uvm_hier_e.UVM_HIER):
            if vreg.get_name() == name:
                return vreg
        logger.warning(
            f"Unable to locate virtual register {repr(name)} in block "
            f"{repr(self.get_full_name())}"
        )

    def get_vfield_by_name(self, name: str) -> uvm_vreg_field:
        for vfield in self.get_virtual_fields(uvm_hier_e.UVM_HIER):
            if vfield.get_name() == name:
                return vfield
        logger.warning(
            f"Unable to locate virtual field {repr(name)}' in block {repr(self.get_full_name())}"
        )

    def build_coverage(self, models: uvm_reg_cvr_t) -> uvm_reg_cvr_t:
        raise NotImplementedError

    def add_coverage(self, models: uvm_reg_cvr_t) -> None:
        raise NotImplementedError

    def has_coverage(self, models: uvm_reg_cvr_t) -> bool:
        raise NotImplementedError

    def set_coverage(self, is_on: uvm_reg_cvr_t) -> uvm_reg_cvr_t:
        raise NotImplementedError

    def get_coverage(
        self, is_on: uvm_reg_cvr_t = uvm_coverage_model_e.UVM_CVR_ALL
    ) -> bool:
        raise NotImplementedError

    def sample(self, offset: uvm_reg_addr_t, is_read: bool, map: uvm_reg_map) -> None:
        raise NotImplementedError

    def sample_values(self) -> None:
        raise NotImplementedError

    def _sample(self, addr: uvm_reg_addr_t, is_read: bool, map: uvm_reg_map) -> None:
        raise NotImplementedError

    def get_default_door(self) -> uvm_door_e:
        if self.default_path is not uvm_door_e.UVM_DEFAULT_DOOR:
            return self.default_path
        if self._parent is not None:
            return self._parent.get_default_door()
        return uvm_door_e.UVM_FRONTDOOR

    def set_default_door(self, door: uvm_door_e) -> None:
        self.default_path = door

    def get_default_path(self) -> uvm_path_e:
        return self.get_default_door()

    def reset(self, kind: str = "HARD") -> None:
        for reg in self._regs.values():
            reg.reset(kind)
        for block in self.get_blocks():
            block.reset(kind)

    def needs_update(self) -> bool:
        raise NotImplementedError

    async def update(
        self,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def mirror(
        self,
        check: uvm_check_e = uvm_check_e.UVM_NO_CHECK,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def write_reg_by_name(
        self,
        name: str,
        data: uvm_reg_data_t,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def read_reg_by_name(
        self,
        name: str,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def write_mem_by_name(
        self,
        name: str,
        offset: uvm_reg_addr_t,
        data: uvm_reg_data_t,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def read_mem_by_name(
        self,
        name: str,
        offset: uvm_reg_addr_t,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def readmemh(filename: str) -> None:
        raise NotImplementedError

    async def writememh(filename: str) -> None:
        raise NotImplementedError

    def get_backdoor(self, inherited: bool = True) -> uvm_reg_backdoor:
        raise NotImplementedError

    def set_backdoor(
        self, bkdr: uvm_reg_backdoor, fname: str = "", lineno: int = 0
    ) -> None:
        raise NotImplementedError

    def clear_hdl_path(self, kind: str = "RTL") -> None:
        raise NotImplementedError

    def add_hdl_path(self, path: str, kind: str = "RTL") -> None:
        if kind not in self._hdl_paths_pool:
            self._hdl_paths_pool[kind] = list()
        self._hdl_paths_pool[kind].append(path)

    def has_hdl_path(self, kind: str = "") -> bool:
        raise NotImplementedError

    def get_hdl_path(self, paths: list[str], kind: str = "") -> None:
        raise NotImplementedError

    def get_full_hdl_path(
        self, paths: list[str], kind: str = "", separator: str = "."
    ) -> None:
        raise NotImplementedError

    def set_default_hdl_path(self, kind: str) -> None:
        raise NotImplementedError

    def get_default_hdl_path(self) -> str:
        raise NotImplementedError

    def set_hdl_path_root(self, path: str, kind: str = "RTL") -> None:
        raise NotImplementedError

    def is_hdl_path_root(self, kind: str = "") -> bool:
        raise NotImplementedError

    def _init_address_maps(self) -> None:
        for map in self._maps:
            map._init_address_map()

    def set_lock(self, v: bool = None) -> None:
        if v is None:
            warnings.warn(
                "The 'set_lock' method is changed. Please use "
                "the argument to set the lock state",
                DeprecationWarning,
                2,
            )
            v = True
        self._locked = v
        for blk in self._blks.values():
            blk.set_lock(v)

    def _unregister(self, m: uvm_reg_map) -> None:
        raise NotImplementedError

    # TODO: Remove backward compatibility
    def add_block(self, blk: uvm_reg_block) -> None:
        warnings.warn(
            "The 'add_block' method should not be called directly.",
            DeprecationWarning,
            2,
        )
        self._add_block(blk)

    # TODO: Should this be dunder methods?
    # extern virtual function void   do_print      (uvm_printer printer);
    # extern virtual function void   do_copy       (uvm_object rhs);
    # extern virtual function bit    do_compare    (uvm_object  rhs,
    #                                               uvm_comparer comparer);
    # extern virtual function void   do_pack       (uvm_packer packer);
    # extern virtual function void   do_unpack     (uvm_packer packer);
    # extern virtual function string convert2string ();
    # extern virtual function uvm_object clone();
