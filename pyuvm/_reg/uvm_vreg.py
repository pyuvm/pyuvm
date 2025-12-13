from __future__ import annotations

from typing import TYPE_CHECKING

from pyuvm._reg.uvm_reg_model import (
    uvm_door_e,
)
from pyuvm._s05_base_classes import uvm_object
from pyuvm._s10_synchronization_classes import (
    uvm_callback,
    uvm_callback_iter,
    uvm_callbacks,
)

if TYPE_CHECKING:
    from pyuvm._reg.uvm_mem import uvm_mem
    from pyuvm._reg.uvm_mem_mam import (
        uvm_mem_mam,
        uvm_mem_mam_policy,
        uvm_mem_region,
    )
    from pyuvm._reg.uvm_reg_block import uvm_reg_block
    from pyuvm._reg.uvm_reg_map import uvm_reg_map
    from pyuvm._reg.uvm_reg_model import (
        uvm_reg_addr_t,
        uvm_reg_data_t,
        uvm_status_e,
    )
    from pyuvm._reg.uvm_vreg_field import uvm_vreg_field
    from pyuvm._s14_15_python_sequences import uvm_sequence_base

__all__ = ["uvm_vreg", "uvm_vreg_cbs", "uvm_vreg_cb", "uvm_vreg_cb_iter"]


class uvm_vreg(uvm_object):
    def __init__(self, name: str, n_bits: int):
        raise NotImplementedError

    def configure(
        self,
        parent: uvm_reg_block,
        mem: uvm_mem = None,
        size: int = 0,
        offset: uvm_reg_addr_t = 0,
        incr: int = 0,
    ) -> None:
        raise NotImplementedError

    def implement(
        self, mem: uvm_mem = None, offset: uvm_reg_addr_t = 0, incr: int = 0
    ) -> None:
        raise NotImplementedError

    def allocate(
        self, n: int, mam: uvm_mem_mam, alloc: uvm_mem_mam_policy = None
    ) -> None:
        raise NotImplementedError

    def get_region(self) -> uvm_mem_region:
        raise NotImplementedError

    def release_region(self) -> None:
        raise NotImplementedError

    def get_full_name(self) -> str:
        raise NotImplementedError

    def get_parent(self) -> uvm_reg_block:
        raise NotImplementedError

    def get_block(self) -> uvm_reg_block:
        raise NotImplementedError

    def get_memory(self) -> uvm_mem:
        raise NotImplementedError

    def get_n_maps(self) -> int:
        raise NotImplementedError

    def is_in_map(self, map: uvm_reg_map) -> bool:
        raise NotImplementedError

    def get_maps(self, maps: list[uvm_reg_map]) -> None:
        raise NotImplementedError

    def get_rights(self, map: uvm_reg_map = None) -> str:
        raise NotImplementedError

    def get_access(self, map: uvm_reg_map = None) -> str:
        raise NotImplementedError

    def get_size(self) -> int:
        raise NotImplementedError

    def get_n_bytes(self) -> int:
        raise NotImplementedError

    def get_incr(self) -> int:
        raise NotImplementedError

    def get_n_memlocs(self) -> int:
        raise NotImplementedError

    def get_fields(self, fields: list[uvm_vreg_field]) -> None:
        raise NotImplementedError

    def get_field_by_name(self, name: str) -> uvm_vreg_field:
        raise NotImplementedError

    def get_offset_in_memory(self, idx: int) -> uvm_reg_addr_t:
        raise NotImplementedError

    def get_address(self, idx: int, map: uvm_reg_map = None) -> uvm_reg_addr_t:
        raise NotImplementedError

    async def write(
        self,
        idx: int,
        value: uvm_reg_data_t,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def read(
        self,
        idx: int,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def poke(
        self,
        idx: int,
        value: uvm_reg_data_t,
        parent: uvm_sequence_base = None,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def peek(
        self,
        idx: int,
        parent: uvm_sequence_base = None,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def pre_write(
        self, idx: int, wdata: uvm_reg_data_t, path: uvm_door_e, map: uvm_reg_map
    ) -> None:
        raise NotImplementedError

    async def post_write(
        self,
        idx: int,
        wdat: uvm_reg_data_t,
        path: uvm_door_e,
        map: uvm_reg_map,
        status: uvm_status_e,
    ) -> None:
        raise NotImplementedError

    async def pre_read(self, idx: int, path: uvm_door_e, map: uvm_reg_map) -> None:
        raise NotImplementedError

    async def post_read(
        self,
        idx: int,
        rdat: uvm_reg_data_t,
        path: uvm_door_e,
        map: uvm_reg_map,
        status: uvm_status_e,
    ) -> None:
        raise NotImplementedError


class uvm_vreg_cbs(uvm_callback):
    def __init__(self, name: str = "uvm_vreg_cbs"):
        super().__init__(name)
        raise NotImplementedError

    async def pre_write(
        self,
        rg: uvm_vreg,
        idx: int,
        wdat: uvm_reg_data_t,
        path: uvm_door_e,
        map: uvm_reg_map,
    ) -> None:
        raise NotImplementedError

    async def post_write(
        self,
        rg: uvm_vreg,
        idx: int,
        wdat: uvm_reg_data_t,
        path: uvm_door_e,
        map: uvm_reg_map,
        status: uvm_status_e,
    ) -> None:
        raise NotImplementedError

    async def pre_read(
        self, rg: uvm_vreg, idx: int, path: uvm_door_e, map: uvm_reg_map
    ) -> None:
        raise NotImplementedError

    async def post_read(
        self,
        rg: uvm_vreg,
        idx: int,
        rdat: uvm_reg_data_t,
        path: uvm_door_e,
        map: uvm_reg_map,
        status: uvm_status_e,
    ) -> None:
        raise NotImplementedError


class uvm_vreg_cb(uvm_callbacks):
    pass


class uvm_vreg_cb_iter(uvm_callback_iter):
    pass
