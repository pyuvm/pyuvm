from __future__ import annotations

from typing import TYPE_CHECKING

from pyuvm import uvm_object
from pyuvm.reg.uvm_reg_model import (
    uvm_check_e,
    uvm_coverage_model_e,
    uvm_door_e,
    uvm_hier_e,
)

if TYPE_CHECKING:
    from pyuvm import uvm_sequence_base
    from pyuvm.reg.uvm_mem import uvm_mem
    from pyuvm.reg.uvm_reg import uvm_reg
    from pyuvm.reg.uvm_reg_backdoor import uvm_reg_backdoor
    from pyuvm.reg.uvm_reg_field import uvm_reg_field
    from pyuvm.reg.uvm_reg_map import uvm_reg_map
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

__all__ = ["uvm_reg_block"]


class uvm_reg_block(uvm_object):
    def __init__(self,
                 name: str = "",
                 has_coverage: int = uvm_coverage_model_e.UVM_NO_COVERAGE):
        raise NotImplementedError

    def configure(self,
                  parent: uvm_reg_block = None,
                  hdl_path: str = "") -> None:
        raise NotImplementedError

    def create_map(self,
                   base_addr: uvm_reg_addr_t,
                   n_bytes: int,
                   endian: uvm_endianness_e,
                   byte_addressing: bool = True) -> uvm_reg_map:
        raise NotImplementedError

    @staticmethod
    def check_data_width(width: int) -> bool:
        raise NotImplementedError

    def set_default_map(self, map: uvm_reg_map) -> None:
        raise NotImplementedError

    def get_default_map(self) -> uvm_reg_map:
        raise NotImplementedError

    def set_parent(self, parent: uvm_reg_block) -> None:
        raise NotImplementedError

    def _add_block(self, blk: uvm_reg_block) -> None:
        raise NotImplementedError

    def _add_map(self, map: uvm_reg_map) -> None:
        raise NotImplementedError

    def _add_register(self, reg: uvm_reg) -> None:
        raise NotImplementedError

    def _add_virtual_register(self, vreg: uvm_vreg) -> None:
        raise NotImplementedError

    def lock_model(self) -> None:
        raise NotImplementedError

    def unlock_model(self) -> None:
        raise NotImplementedError

    async def wait_for_lock(self) -> None:
        raise NotImplementedError

    def is_locked(self) -> bool:
        raise NotImplementedError

    def get_full_name(self) -> str:
        raise NotImplementedError

    def get_parent(self) -> uvm_reg_block:
        raise NotImplementedError

    @staticmethod
    def get_root_blocks(blks: list[uvm_reg_block]) -> None:
        raise NotImplementedError

    @staticmethod
    def find_blocks(name: str,
                    blks: list[uvm_reg_block],  # ref
                    root: uvm_reg_block = None,
                    accessor: uvm_object = None) -> None:
        raise NotImplementedError

    def get_blocks(self,
                   blks: list[uvm_reg_block],  # ref
                   hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> None:
        raise NotImplementedError

    def get_maps(self, maps: list[uvm_reg_map]) -> None:  # ref
        raise NotImplementedError

    def get_registers(self,
                      regs: list[uvm_reg],
                      hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> None:
        raise NotImplementedError

    def get_fields(self,
                   fields: list[uvm_reg_field],
                   hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> None:
        raise NotImplementedError

    def get_memories(self,
                     mems: list[uvm_mem],  # ref
                     hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> None:
        raise NotImplementedError

    def get_virtual_registers(self,
                              regs: list[uvm_vreg],  # ref
                              hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> None:
        raise NotImplementedError

    def get_virtual_fields(self,
                           fields: list[uvm_vreg_field],  # ref
                           hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> None:
        raise NotImplementedError

    def get_block_by_name(self, name: str) -> uvm_reg_block:
        raise NotImplementedError

    def get_block_by_full_name(self, name: str) -> uvm_reg_block:
        raise NotImplementedError

    def get_map_by_name(self, name: str) -> uvm_reg_map:
        raise NotImplementedError

    def get_reg_by_name(self, name: str) -> uvm_reg:
        raise NotImplementedError

    def get_field_by_name(self, name: str) -> uvm_reg_field:
        raise NotImplementedError

    def get_mem_by_name(self, name: str) -> uvm_mem:
        raise NotImplementedError

    def get_vreg_by_name(self, name: str) -> uvm_vreg:
        raise NotImplementedError

    def get_vfield_by_name(self, name: str) -> uvm_vreg_field:
        raise NotImplementedError

    def build_coverage(self, models: uvm_reg_cvr_t) -> uvm_reg_cvr_t:
        raise NotImplementedError

    def add_coverage(self, models: uvm_reg_cvr_t) -> None:
        raise NotImplementedError

    def has_coverage(self, models: uvm_reg_cvr_t) -> bool:
        raise NotImplementedError

    def set_coverage(self, is_on: uvm_reg_cvr_t) -> uvm_reg_cvr_t:
        raise NotImplementedError

    def get_coverage(
            self,
            is_on: uvm_reg_cvr_t = uvm_coverage_model_e.UVM_CVR_ALL) -> bool:
        raise NotImplementedError

    def sample(self,
               offset: uvm_reg_addr_t,
               is_read: bool,
               map: uvm_reg_map) -> None:
        raise NotImplementedError

    def sample_values(self) -> None:
        raise NotImplementedError

    def _sample(self,
                addr: uvm_reg_addr_t,
                is_read: bool,
                map: uvm_reg_map) -> None:
        raise NotImplementedError

    def get_default_door(self) -> uvm_door_e:
        raise NotImplementedError

    def set_default_door(self, door: uvm_door_e) -> None:
        raise NotImplementedError

    def get_default_path(self) -> uvm_path_e:
        raise NotImplementedError

    def reset(self, kind: str = "HARD") -> None:
        raise NotImplementedError

    def needs_update(self) -> bool:
        raise NotImplementedError

    async def update(self,
                     path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
                     map: uvm_reg_map = None,
                     parent: uvm_sequence_base = None,
                     prior: int = -1,
                     extension: uvm_object = None,
                     fname: str = "",
                     lineno: int = 0) -> uvm_status_e:
        raise NotImplementedError

    async def mirror(self,
                     check: uvm_check_e = uvm_check_e.UVM_NO_CHECK,
                     path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
                     parent: uvm_sequence_base = None,
                     prior: int = -1,
                     extension: uvm_object = None,
                     fname: str = "",
                     lineno: int = 0) -> uvm_status_e:
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
            lineno: int = 0) -> uvm_status_e:
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
            lineno: int = 0) -> tuple[uvm_status_e, uvm_reg_data_t]:
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
            lineno: int = 0) -> uvm_status_e:
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
            lineno: int = 0) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def readmemh(filename: str) -> None:
        raise NotImplementedError

    async def writememh(filename: str) -> None:
        raise NotImplementedError

    def get_backdoor(self, inherited: bool = True) -> uvm_reg_backdoor:
        raise NotImplementedError

    def set_backdoor(self,
                     bkdr: uvm_reg_backdoor,
                     fname: str = "",
                     lineno: int = 0) -> None:
        raise NotImplementedError

    def clear_hdl_path(self, kind: str = "RTL") -> None:
        raise NotImplementedError

    def add_hdl_path(self, path: str, kind: str = "RTL") -> None:
        raise NotImplementedError

    def has_hdl_path(self, kind: str = "") -> bool:
        raise NotImplementedError

    def get_hdl_path(self, paths: list[str], kind: str = "") -> None:
        raise NotImplementedError

    def get_full_hdl_path(self,
                          paths: list[str],
                          kind: str = "",
                          separator: str = ".") -> None:
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
        raise NotImplementedError

    def set_lock(self, v: bool) -> None:
        raise NotImplementedError

    def _unregister(self, m: uvm_reg_map) -> None:
        raise NotImplementedError

    # TODO: Should this be dunder methods?
    # extern virtual function void   do_print      (uvm_printer printer);
    # extern virtual function void   do_copy       (uvm_object rhs);
    # extern virtual function bit    do_compare    (uvm_object  rhs,
    #                                               uvm_comparer comparer);
    # extern virtual function void   do_pack       (uvm_packer packer);
    # extern virtual function void   do_unpack     (uvm_packer packer);
    # extern virtual function string convert2string ();
    # extern virtual function uvm_object clone();
