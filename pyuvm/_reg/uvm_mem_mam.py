from __future__ import annotations

from enum import Enum

from pyuvm._reg.uvm_mem import uvm_mem
from pyuvm._reg.uvm_reg_map import uvm_reg_map
from pyuvm._reg.uvm_reg_model import (
    uvm_door_e,
    uvm_reg_addr_t,
    uvm_reg_data_t,
    uvm_status_e,
)
from pyuvm._reg.uvm_vreg import uvm_vreg
from pyuvm._s05_base_classes import uvm_object
from pyuvm._s14_15_python_sequences import uvm_sequence_base
from pyuvm._utility_classes import uvm_void

__all__ = ["uvm_mem_mam_cfg", "uvm_mem_mam", "uvm_mem_region", "uvm_mem_mam_policy"]


class uvm_mem_mam(uvm_void):
    def __init__(self, name: str, cfg: uvm_mem_mam_cfg, mem: uvm_mem = None) -> None:
        raise NotImplementedError

    def reconfigure(self, cfg: uvm_mem_mam_cfg = None) -> uvm_mem_mam_cfg:
        raise NotImplementedError

    def reserve_region(
        self,
        start_offset: uvm_reg_addr_t,
        n_bytes: int,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_mem_region:
        raise NotImplementedError

    def request_region(
        self,
        n_bytes: int,
        alloc: uvm_mem_mam_policy = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_mem_region:
        raise NotImplementedError

    def release_region(self, region: uvm_mem_region) -> None:
        raise NotImplementedError

    def release_all_regions(self) -> None:
        raise NotImplementedError

    def for_each(reset: bool = False) -> uvm_mem_region:
        raise NotImplementedError

    def get_memory(self) -> uvm_mem:
        raise NotImplementedError

    # TODO: Should these be dunder methods?
    # extern function string convert2string();


class uvm_mem_region(uvm_void):
    def __init__(
        self,
        start_offset: uvm_reg_addr_t,
        end_offset: uvm_reg_addr_t,
        len: int,
        n_bytes: int,
        parent: uvm_mem_mam,
    ) -> None:
        raise NotImplementedError

    def get_start_offset(self) -> uvm_reg_addr_t:
        raise NotImplementedError

    def get_end_offset(self) -> uvm_reg_addr_t:
        raise NotImplementedError

    def get_len(self) -> int:
        raise NotImplementedError

    def get_n_bytes(self) -> int:
        raise NotImplementedError

    def release_region(self) -> None:
        raise NotImplementedError

    def get_memory(self) -> uvm_mem:
        raise NotImplementedError

    def get_virtual_registers(
        self,
    ) -> uvm_vreg:
        raise NotImplementedError

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

    async def burst_read(
        self,
        offset: uvm_reg_addr_t,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, list[uvm_reg_data_t]]:
        raise NotImplementedError

    async def poke(
        self,
        offset: uvm_reg_addr_t,
        value: uvm_reg_data_t,
        parent: uvm_sequence_base = None,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def peek(
        self,
        offset: uvm_reg_addr_t,
        parent: uvm_sequence_base = None,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    # TODO: Should these be dunder methods?
    # extern function string convert2string();


class uvm_mem_mam_policy(uvm_void):
    len: int
    start_offset: uvm_reg_addr_t  # rand
    min_offset: uvm_reg_addr_t
    max_offset: uvm_reg_addr_t
    in_use: list[uvm_mem_region]

    # TODO: constraints
    # constraint uvm_mem_mam_policy_valid {
    #     start_offset >= min_offset;
    #     start_offset <= max_offset - len + 1;
    # }
    # constraint uvm_mem_mam_policy_no_overlap {
    #     foreach (in_use[i]) {
    #     !(start_offset <= in_use[i].Xend_offsetX &&
    #     start_offset + len - 1 >= in_use[i].Xstart_offsetX);
    #     }


class uvm_mem_mam_cfg(uvm_void):
    n_bytes: int  # rand
    start_offset: uvm_reg_addr_t  # rand
    end_offset: uvm_reg_addr_t  # rand
    mode: alloc_mode_e  # rand
    locality: locality_e  # rand

    # TODO: constraints
    # constraint uvm_mem_mam_cfg_valid {
    #     end_offset > start_offset;
    #     n_bytes < 64;
    # }


class alloc_mode_e(Enum):
    GREEDY = 0
    THRIFTY = 1


class locality_e(Enum):
    BROAD = 0
    NEARBY = 1
