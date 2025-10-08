from __future__ import annotations

from typing import TYPE_CHECKING

from pyuvm import uvm_object
from pyuvm.reg.uvm_reg_model import (
    uvm_coverage_model_e,
    uvm_door_e,
)

if TYPE_CHECKING:
    from pyuvm import uvm_sequence_base
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

__all__ = ["uvm_mem"]


class uvm_mem(uvm_object):

    _max_size: int

    def __init__(self,
                 name: str,
                 size: int,
                 n_bits: int,
                 access: str = "RW",
                 has_coverage: int = uvm_coverage_model_e.UVM_NO_COVERAGE):
        raise NotImplementedError

    def configure(self, parent: uvm_reg_block, hdl_path: str = "") -> None:
        raise NotImplementedError

    def set_offset(self,
                   map: uvm_reg_map,
                   offset: uvm_reg_addr_t,
                   unmapped: bool = False) -> None:
        raise NotImplementedError

    def set_parent(self, parent: uvm_reg_block) -> None:
        raise NotImplementedError

    def add_map(self, map: uvm_reg_map) -> None:
        raise NotImplementedError

    def _lock_model(self) -> None:
        raise NotImplementedError

    def _add_vreg(self, vreg: uvm_vreg) -> None:
        raise NotImplementedError

    def _delete_vreg(self, vreg: uvm_vreg) -> None:
        raise NotImplementedError

    def get_full_name(self) -> str:
        raise NotImplementedError

    def get_parent(self) -> uvm_reg_block:
        raise NotImplementedError

    def get_block(self) -> uvm_reg_block:
        raise NotImplementedError

    def get_n_maps(self) -> int:
        raise NotImplementedError

    def is_in_map(map: uvm_reg_map) -> bool:
        raise NotImplementedError

    def get_maps(self, maps: list[uvm_reg_map]) -> None:
        raise NotImplementedError

    def get_local_map(self, map: uvm_reg_map) -> uvm_reg_map:
        raise NotImplementedError

    def get_default_map(self) -> uvm_reg_map:
        raise NotImplementedError

    def get_rights(self, map: uvm_reg_map = None) -> str:
        raise NotImplementedError

    def get_access(self, map: uvm_reg_map = None) -> str:
        raise NotImplementedError

    def get_size(self) -> int:
        raise NotImplementedError

    def get_n_bytes(self) -> int:
        raise NotImplementedError

    def get_n_bits(self) -> int:
        raise NotImplementedError

    def get_max_size(self) -> int:
        raise NotImplementedError

    # TODO: Do not match sv definition
    def get_virtual_registers(self, regs: list[uvm_vreg]) -> None:
        raise NotImplementedError

    # TODO: Do not match sv definition
    def get_virtual_fields(self, fields: list[uvm_vreg_field]) -> None:
        raise NotImplementedError

    def get_vreg(self, name: str) -> uvm_vreg:
        raise NotImplementedError

    def get_vreg_by_name(self, name: str) -> uvm_vreg:
        raise NotImplementedError

    def get_vfield_by_name(self, name: str) -> uvm_vreg_field:
        raise NotImplementedError

    def get_vreg_by_offset(self,
                           offset: uvm_reg_addr_t,
                           map: uvm_reg_map = None) -> uvm_vreg:
        raise NotImplementedError

    def get_offset(self,
                   offset: uvm_reg_addr_t = 0,
                   map: uvm_reg_map = None) -> uvm_reg_addr_t:
        raise NotImplementedError

    def get_address(self,
                    offset: uvm_reg_addr_t = 0,
                    map: uvm_reg_map = None) -> uvm_reg_addr_t:
        raise NotImplementedError

    def get_addresses(self,
                      offset: uvm_reg_addr_t = 0,
                      map: uvm_reg_map = None,
                      addr: list[uvm_reg_addr_t] = None) -> int:
        raise NotImplementedError

    async def write(self,
                    offset: uvm_reg_addr_t,
                    value: uvm_reg_data_t,
                    path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
                    map: uvm_reg_map = None,
                    parent: uvm_sequence_base = None,
                    prior: int = -1,
                    extension: uvm_object = None,
                    fname: str = "",
                    lineno: int = 0) -> uvm_status_e:
        raise NotImplementedError

    async def read(self,
                   offset: uvm_reg_addr_t,
                   path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
                   map: uvm_reg_map = None,
                   parent: uvm_sequence_base = None,
                   prior: int = -1,
                   extension: uvm_object = None,
                   fname: str = "",
                   lineno: int = 0) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def burst_write(self,
                          offset: uvm_reg_addr_t,
                          value: list[uvm_reg_data_t],
                          path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
                          map: uvm_reg_map = None,
                          parent: uvm_sequence_base = None,
                          prior: int = -1,
                          extension: uvm_object = None,
                          fname: str = "",
                          lineno: int = 0) -> uvm_status_e:
        raise NotImplementedError

    async def burst_read(self,
                         offset: uvm_reg_addr_t,
                         value: list[uvm_reg_data_t],
                         path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
                         map: uvm_reg_map = None,
                         parent: uvm_sequence_base = None,
                         prior: int = -1,
                         extension: uvm_object = None,
                         fname: str = "",
                         lineno: int = 0) -> uvm_status_e:
        raise NotImplementedError

    async def poke(self,
                   offset: uvm_reg_addr_t,
                   value: uvm_reg_data_t,
                   kind: str = "",
                   parent: uvm_sequence_base = None,
                   extension: uvm_object = None,
                   fname: str = "",
                   lineno: int = 0) -> uvm_status_e:
        raise NotImplementedError

    async def peek(self,
                   offset: uvm_reg_addr_t,
                   kind: str = "",
                   parent: uvm_sequence_base = None,
                   extension: uvm_object = None,
                   fname: str = "",
                   lineno: int = 0) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    def _check_access(self, rw: uvm_reg_item) -> uvm_reg_map_info | None:
        raise NotImplementedError

    async def do_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def do_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    def set_frontdoor(self,
                      ftdr: uvm_reg_frontdoor,
                      map: uvm_reg_map = None,
                      fname: str = "",
                      lineno: int = 0) -> None:
        raise NotImplementedError

    def get_frontdoor(self, map: uvm_reg_map = None) -> uvm_reg_frontdoor:
        raise NotImplementedError

    def set_backdoor(self,
                     bkdr: uvm_reg_backdoor,
                     fname: str = "",
                     lineno: int = 0) -> None:
        raise NotImplementedError

    def get_backdoor(self, inherited: bool = True) -> uvm_reg_backdoor:
        raise NotImplementedError

    def clear_hdl_path(self, kind: str = "RTL") -> None:
        raise NotImplementedError

    def add_hdl_path(self,
                     slices: list[uvm_hdl_path_slice],
                     kind: str = "RTL") -> None:
        raise NotImplementedError

    def add_hdl_path_slice(self,
                           name: str,
                           offset: int,
                           size: int,
                           first: bool = False,
                           kind: str = "RTL") -> None:
        raise NotImplementedError

    def has_hdl_path(self, kind: str = "") -> bool:
        raise NotImplementedError

    def get_hdl_path(self,
                     paths: list[uvm_hdl_path_concat],
                     kind: str = "") -> None:
        raise NotImplementedError

    def get_full_hdl_path(self,
                          paths: list[uvm_hdl_path_concat],
                          kind: str = "",
                          separator: str = ".") -> None:
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

    def sample(self,
               offset: uvm_reg_addr_t,
               is_read: bool,
               map: uvm_reg_map) -> None:
        raise NotImplementedError

    def _sample(self,
                addr: uvm_reg_addr_t,
                is_read: bool,
                map: uvm_reg_map) -> None:
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
