from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

from pyuvm.error_classes import UVMFatalError
from pyuvm.reg.uvm_reg_model import (
    uvm_coverage_model_e,
    uvm_door_e,
)
from pyuvm.s05_base_classes import uvm_object

if TYPE_CHECKING:
    from pyuvm.reg.uvm_mem_mam import (
        alloc_mode_e,
        locality_e,
        uvm_mem_mam,
        uvm_mem_mam_cfg,
    )
    from pyuvm.reg.uvm_reg_backdoor import uvm_reg_backdoor
    from pyuvm.reg.uvm_reg_block import uvm_reg_block
    from pyuvm.reg.uvm_reg_item import uvm_reg_item
    from pyuvm.reg.uvm_reg_map import uvm_reg_map, uvm_reg_map_info
    from pyuvm.reg.uvm_reg_model import (
        uvm_hdl_path_concat,
        uvm_hdl_path_slice,
        uvm_reg_addr_t,
        uvm_reg_cvr_t,
        uvm_reg_data_t,
        uvm_status_e,
    )
    from pyuvm.reg.uvm_reg_sequence import uvm_reg_frontdoor
    from pyuvm.reg.uvm_vreg import uvm_vreg
    from pyuvm.reg.uvm_vreg_field import uvm_vreg_field
    from pyuvm.s14_15_python_sequences import uvm_sequence_base

__all__ = ["uvm_mem"]
logger = logging.getLogger("RegModel")


class uvm_mem(uvm_object):
    _max_size: ClassVar[int] = 0

    def __init__(
        self,
        name: str,
        size: int,
        n_bits: int,
        access: str = "RW",
        has_coverage: int = uvm_coverage_model_e.UVM_NO_COVERAGE,
    ) -> None:
        super().__init__(name)
        self._locked: bool = False
        self._read_in_progress: bool = False
        self._write_in_progress: bool = False
        self._access: str = access
        self._size: int = size
        self._parent = None
        self._maps: list[uvm_reg_map] = list()
        self._n_bits: int = n_bits
        self._backdoor: uvm_reg_backdoor = None
        self._is_powered_down: bool = False
        self._has_coverage: int = has_coverage
        self._cover_on: int = 0
        self._fname: str = ""
        self._lineno: int = 0
        self._vregs: list[uvm_vreg] = list()
        # self._hdl_paths_pool: uvm_object_string_pool = None
        self._mam: uvm_mem_mam = None
        raise NotImplementedError

    def configure(self, parent: uvm_reg_block, hdl_path: str = "") -> None:
        if not parent:
            raise UVMFatalError("Configure: parent is None")
        self._parent = parent

        if self._access not in ["RW", "RO"]:
            logger.error(
                f"Memory '{self.get_full_name()}' can only be 'RW' "
                "and 'RO', setting access to 'RW'"
            )
            self._access = "RW"
            cfg = uvm_mem_mam_cfg()
            cfg.n_bytes = 0
            cfg.start_offset = 0
            cfg.end_offset = self._size - 1
            cfg.mode = alloc_mode_e.GREEDY
            cfg.locality = locality_e.BROAD
            self.mam = uvm_mem_mam(self.get_full_name(), cfg, self)
            self._parent.add_mem(self)
            if hdl_path != "":
                self.add_hdl_path_slice(hdl_path, -1, -1)

    def set_offset(
        self, map: uvm_reg_map, offset: uvm_reg_addr_t, unmapped: bool = False
    ) -> None:
        if len(self._maps) > 1 and not map:
            logger.error(
                f"Set offset requires a map when memory "
                f"'{self.get_full_name()}' belongs to more than one map"
            )
            return
        local_map = self.get_local_map(map)
        if local_map:
            local_map._set_mem_offset(self, offset, unmapped)

    def set_parent(self, parent: uvm_reg_block) -> None:
        self._parent = parent

    def add_map(self, map: uvm_reg_map) -> None:
        self._maps.append(map)

    def _lock_model(self) -> None:
        self._lock_model = True

    def _add_vreg(self, vreg: uvm_vreg) -> None:
        raise NotImplementedError

    def _delete_vreg(self, vreg: uvm_vreg) -> None:
        raise NotImplementedError

    def get_full_name(self) -> str:
        if not self._parent:
            return self.get_name()
        return f"{self._parent.get_full_name()}.{self.get_name()}"

    def get_parent(self) -> uvm_reg_block:
        return self._parent

    def get_block(self) -> uvm_reg_block:
        return self._parent

    def get_n_maps(self) -> int:
        return len(self._maps)

    def is_in_map(self, map: uvm_reg_map) -> bool:
        if map in self._maps:
            return True
        for local_map in self._maps:
            parent_map = local_map.get_parent_map()
            while parent_map:
                if parent_map == map:
                    return True
                parent_map = parent_map.get_parent_map()
        return False

    def get_maps(self, maps: list[uvm_reg_map]) -> None:
        return self._maps

    def get_local_map(self, map: uvm_reg_map) -> uvm_reg_map | None:
        if not map:
            return self.get_default_map()
        if map in self._maps:
            return map
        for local_map in self._maps:
            parent_map = local_map.get_parent_map()
            while parent_map:
                if parent_map == map:
                    return local_map
                parent_map = parent_map.get_parent_map()
        logger.warning(
            f"Memory '{self.get_full_name()}' is not contained "
            f"within map '{map.get_full_name()}'"
        )

    def get_default_map(self) -> uvm_reg_map | None:
        if not self._maps:
            logger.warning(
                f"Memory '{self.get_full_name()}' is not registered with any map"
            )
            return
        if len(self._maps) == 1:
            return self._maps[0]
        for map in self._maps:
            blk = map.get_parent()
            default_map = blk.get_default_map()
            if default_map:
                local_map = self.get_local_map(default_map)
                if local_map:
                    return local_map
        return self._maps[0]

    def get_rights(self, map: uvm_reg_map = None) -> str:
        # If memory is not shared
        if len(self._maps) <= 1:
            return "RW"
        local_map = self.get_local_map(map)
        if not local_map:
            return "RW"
        info = local_map.get_mem_map_info(self)
        return info.rights

    def get_access(self, map: uvm_reg_map = None) -> str:
        if self.get_n_maps() == 1:
            return self._access
        local_map = self.get_local_map(map)
        if not local_map:
            return self._access
        rights = self.get_rights(local_map)
        if rights == "RW":
            return self._access
        elif rights == "RO":
            if self._access in ["RW", "WO"]:
                return "RO"
        elif rights == "WO":
            if self._access in ["RW", "WO"]:
                return "WO"
            elif self._access in ["RO"]:
                logger.error(
                    f"RO memory '{self.get_full_name()}' restricted "
                    f"to WO in map '{local_map.get_full_name()}'"
                )
            else:
                logger.error(
                    f"Memory '{self.get_full_name()}' has invalid "
                    f"access mode '{self._access}'"
                )
        return self._access

    def get_size(self) -> int:
        return self._size

    def get_n_bytes(self) -> int:
        return int(self._n_bits - 1 / 8 + 1)

    def get_n_bits(self) -> int:
        return self._n_bits

    @staticmethod
    def get_max_size() -> int:
        return uvm_mem._max_size

    # TODO: Document definition compared to IEEE 1800.2
    def get_virtual_registers(self) -> list[uvm_vreg]:
        return self._vregs

    # TODO: Document definition compared to IEEE 1800.2
    def get_virtual_fields(self) -> list[uvm_vreg_field]:
        field = list()
        for vreg in self._vregs:
            field += vreg.get_virtual_fields()
        return field

    def get_vreg(self, name: str) -> uvm_vreg:
        raise NotImplementedError

    def get_vreg_by_name(self, name: str) -> uvm_vreg | None:
        for vreg in self.get_virtual_registers():
            if vreg.get_name() == name:
                return vreg
        logger.warning(
            f"Unable to find virtual register '{name}' in memory "
            f"'{self.get_full_name()}'"
        )

    def get_vfield_by_name(self, name: str) -> uvm_vreg_field | None:
        for field in self.get_virtual_fields():
            if field.get_name() == name:
                return field
        logger.warning(
            f"Unable to find virtual field '{name}' in memory '{self.get_full_name()}'"
        )

    def get_vreg_by_offset(
        self, offset: uvm_reg_addr_t, map: uvm_reg_map = None
    ) -> uvm_vreg:
        raise NotImplementedError

    def get_offset(
        self, offset: uvm_reg_addr_t = 0, map: uvm_reg_map = None
    ) -> uvm_reg_addr_t:
        raise NotImplementedError

    def get_address(
        self, offset: uvm_reg_addr_t = 0, map: uvm_reg_map = None
    ) -> uvm_reg_addr_t:
        _, addresses = self.get_addresses(offset, map)
        return addresses[0]

    def get_addresses(
        self,
        offset: uvm_reg_addr_t = 0,
        map: uvm_reg_map = None,
    ) -> tuple[int, list[uvm_reg_addr_t]]:
        if offset >= self._size:
            logger.warning(
                f"Offset 0x{offset:X} lies outside of memory "
                f"'{self.get_name()}' which has size 0x{self._size:X}"
            )
            return -1, list()
        local_map = self.get_local_map(map)
        if not local_map:
            map_name = "None" if not map else map.get_full_name()
            logger.warning(f"Memory '{self.get_name()}' not found in map '{map_name}'")
            return -1, list()
        map_info = local_map.get_mem_map_info(self)
        if map_info.unmapped:
            map_name = local_map.get_full_name() if not map else map.get_full_name()
            logger.warning(
                f"Memory '{self.get_name()}' is unmapped in map '{map_name}'"
            )
            return -1, list()
        stride = map_info.stride
        addresses = [a + stride * offset for a in map_info.addr]
        return local_map.get_n_bytes(), addresses

    async def write(
        self,
        offset: uvm_reg_addr_t,
        value: uvm_reg_data_t,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def read(
        self,
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

    async def burst_write(
        self,
        offset: uvm_reg_addr_t,
        value: list[uvm_reg_data_t],
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def burst_read(
        self,
        offset: uvm_reg_addr_t,
        value: list[uvm_reg_data_t],
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def poke(
        self,
        offset: uvm_reg_addr_t,
        value: uvm_reg_data_t,
        kind: str = "",
        parent: uvm_sequence_base = None,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def peek(
        self,
        offset: uvm_reg_addr_t,
        kind: str = "",
        parent: uvm_sequence_base = None,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    def _check_access(self, rw: uvm_reg_item) -> uvm_reg_map_info | None:
        raise NotImplementedError

    async def do_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def do_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    def set_frontdoor(
        self,
        ftdr: uvm_reg_frontdoor,
        map: uvm_reg_map = None,
        fname: str = "",
        lineno: int = 0,
    ) -> None:
        raise NotImplementedError

    def get_frontdoor(self, map: uvm_reg_map = None) -> uvm_reg_frontdoor:
        raise NotImplementedError

    def set_backdoor(
        self, bkdr: uvm_reg_backdoor, fname: str = "", lineno: int = 0
    ) -> None:
        raise NotImplementedError

    def get_backdoor(self, inherited: bool = True) -> uvm_reg_backdoor:
        raise NotImplementedError

    def clear_hdl_path(self, kind: str = "RTL") -> None:
        raise NotImplementedError

    def add_hdl_path(self, slices: list[uvm_hdl_path_slice], kind: str = "RTL") -> None:
        raise NotImplementedError

    def add_hdl_path_slice(
        self, name: str, offset: int, size: int, first: bool = False, kind: str = "RTL"
    ) -> None:
        raise NotImplementedError

    def has_hdl_path(self, kind: str = "") -> bool:
        raise NotImplementedError

    def get_hdl_path(self, paths: list[uvm_hdl_path_concat], kind: str = "") -> None:
        raise NotImplementedError

    def get_full_hdl_path(
        self, paths: list[uvm_hdl_path_concat], kind: str = "", separator: str = "."
    ) -> None:
        raise NotImplementedError

    def get_hdl_path_kinds(self, kinds: list[str]) -> None:
        raise NotImplementedError

    async def backdoor_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def backdoor_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    def backdoor_read_func(self, rw: uvm_reg_item) -> uvm_status_e:
        raise NotImplementedError

    async def pre_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def post_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def pre_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def post_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    def build_coverage(self, models: uvm_reg_cvr_t) -> uvm_reg_cvr_t:
        raise NotImplementedError

    def add_coverage(self, models: uvm_reg_cvr_t) -> None:
        raise NotImplementedError

    def set_coverage(self, is_on: uvm_reg_cvr_t) -> uvm_reg_cvr_t:
        raise NotImplementedError

    def get_coverage(self, is_on: uvm_reg_cvr_t) -> bool:
        raise NotImplementedError

    def sample(self, offset: uvm_reg_addr_t, is_read: bool, map: uvm_reg_map) -> None:
        raise NotImplementedError

    def _sample(self, addr: uvm_reg_addr_t, is_read: bool, map: uvm_reg_map) -> None:
        self.sample(addr, is_read, map)

    # TODO: Should this be dunder methods?
    # extern virtual function void do_print (uvm_printer printer);
    # extern virtual function string convert2string();
    # extern virtual function uvm_object clone();
    # extern virtual function void do_copy   (uvm_object rhs);
    # extern virtual function bit do_compare (uvm_object  rhs,
    #                                        uvm_comparer comparer);
    # extern virtual function void do_pack (uvm_packer packer);
    # extern virtual function void do_unpack (uvm_packer packer);
