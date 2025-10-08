from __future__ import annotations

from typing import TYPE_CHECKING

from pyuvm import uvm_object
from pyuvm.reg.uvm_reg_model import (
    uvm_check_e,
    uvm_door_e,
    uvm_predict_e,
)

if TYPE_CHECKING:
    from pyuvm import uvm_sequence_base
    from pyuvm.reg.uvm_reg_backdoor import uvm_reg_backdoor
    from pyuvm.reg.uvm_reg_block import uvm_reg_block
    from pyuvm.reg.uvm_reg_field import uvm_reg_field
    from pyuvm.reg.uvm_reg_file import uvm_reg_file
    from pyuvm.reg.uvm_reg_item import uvm_reg_item
    from pyuvm.reg.uvm_reg_map import uvm_reg_map, uvm_reg_map_info
    from pyuvm.reg.uvm_reg_model import (
        uvm_hdl_path_concat,
        uvm_hdl_path_slice,
        uvm_reg_addr_t,
        uvm_reg_byte_en_t,
        uvm_reg_cvr_t,
        uvm_reg_data_t,
        uvm_status_e,
    )
    from pyuvm.reg.uvm_reg_sequence import uvm_reg_frontdoor

__all__ = ["uvm_reg"]


class uvm_reg_err_service(uvm_object):
    def __init__(self, name: str = ""):
        super().__init__(name)
        raise NotImplementedError


class uvm_reg(uvm_object):

    _reg_registry: dict[str, uvm_reg] = {}

    def __init__(self,
                 name="",
                 n_bits: int = 0,
                 has_coverage: int = 0) -> None:
        super().__init__(name)
        raise NotImplementedError

    def configure(self,
                  blk_parent: uvm_reg_block,
                  regfile_parent: uvm_reg_file = None,
                  hdl_path: str = "") -> None:
        raise NotImplementedError

    def set_offset(self,
                   map: uvm_reg_map,
                   offset: uvm_reg_addr_t,
                   unmapped: bool = False) -> None:
        raise NotImplementedError

    def _set_parent(self,
                    blk_parent: uvm_reg_block,
                    regfile_parent: uvm_reg_file) -> None:
        raise NotImplementedError

    def _add_field(self, field: uvm_reg_field) -> None:
        raise NotImplementedError

    def add_map(self, map: uvm_reg_map) -> None:
        raise NotImplementedError

    def _lock_model(self) -> None:
        raise NotImplementedError

    def _unlock_model(self) -> None:
        raise NotImplementedError

    def unregister(self, map: uvm_reg_map) -> None:
        raise NotImplementedError

    def get_full_name(self) -> str:
        raise NotImplementedError

    def get_parent(self) -> uvm_reg_block:
        raise NotImplementedError

    def get_block(self) -> uvm_reg_block:
        raise NotImplementedError

    def get_regfile(self) -> uvm_reg_file:
        raise NotImplementedError

    def get_n_maps(self) -> int:
        raise NotImplementedError

    def is_in_map(self, map: uvm_reg_map) -> bool:
        raise NotImplementedError

    def get_maps(self) -> list[uvm_reg_map]:
        raise NotImplementedError

    def get_local_map(self, map: uvm_reg_map) -> uvm_reg_map:
        raise NotImplementedError

    def get_default_map(self) -> uvm_reg_map | None:
        raise NotImplementedError

    def get_rights(self, map: uvm_reg_map = None) -> str:
        raise NotImplementedError

    def get_n_bits(self) -> int:
        raise NotImplementedError

    def get_n_bytes(self) -> int:
        raise NotImplementedError

    def get_max_size(self) -> int:
        raise NotImplementedError

    def get_fields(self) -> list[uvm_reg_field]:
        raise NotImplementedError

    def get_field_by_name(self, name: str) -> uvm_reg_field:
        raise NotImplementedError

    def _get_fields_access(self, map: uvm_reg_map) -> str:
        raise NotImplementedError

    def get_offset(self, map: uvm_reg_map) -> uvm_reg_addr_t:
        raise NotImplementedError

    def get_address(self, map: uvm_reg_map = None) -> uvm_reg_addr_t:
        raise NotImplementedError

    def get_addresses(self,
                      map: uvm_reg_map = None,
                      addr: list[uvm_reg_addr_t] = None) -> int:
        raise NotImplementedError

    def get_reg_by_full_name(self, full_name: str) -> uvm_reg | None:
        raise NotImplementedError

    def set(self,
            value: uvm_reg_data_t,
            fname: str = "",
            lineno: int = 0) -> None:
        raise NotImplementedError

    def get(self, fname: str = "", lineno: int = 0) -> uvm_reg_data_t:
        raise NotImplementedError

    def get_mirrored_value(self, fname: str = "", lineno: int = 0) -> int:
        raise NotImplementedError

    def needs_update() -> bool:
        raise NotImplementedError

    def reset(self, kind: str = "HARD") -> None:
        raise NotImplementedError

    def get_reset(self, kind: str = "HARD") -> int:
        raise NotImplementedError

    def has_reset(self, kind: str = "HARD", delete: bool = False) -> bool:
        raise NotImplementedError

    def set_reset(self, value: uvm_reg_data_t, kind: str = "HARD") -> None:
        raise NotImplementedError

    async def write(self,
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
                   path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
                   map: uvm_reg_map = None,
                   parent: uvm_sequence_base = None,
                   prior: int = -1,
                   extension: uvm_object = None,
                   fname: str = "",
                   lineno: int = 0) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def poke(self,
                   value: uvm_reg_data_t,
                   kind: str = "",
                   parent: uvm_sequence_base = None,
                   extension: uvm_object = None,
                   fname: str = "",
                   lineno: int = 0) -> uvm_status_e:
        raise NotImplementedError

    async def peek(self,
                   kind: str = "",
                   parent: uvm_sequence_base = None,
                   extension: uvm_object = None,
                   fname: str = "",
                   lineno: int = 0) -> tuple[uvm_status_e, uvm_reg_data_t]:
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
                     map: uvm_reg_map = None,
                     parent: uvm_sequence_base = None,
                     prior: int = -1,
                     extension: uvm_object = None,
                     fname: str = "",
                     lineno: int = 0) -> uvm_status_e:
        raise NotImplementedError

    def predict(self,
                value: uvm_reg_data_t,
                be: uvm_reg_byte_en_t = -1,
                kind: uvm_predict_e = uvm_predict_e.UVM_PREDICT_DIRECT,
                path: uvm_door_e = uvm_door_e.UVM_FRONTDOOR,
                map: uvm_reg_map = None,
                fname: str = "",
                lineno: int = 0) -> bool:
        raise NotImplementedError

    def is_busy(self) -> bool:
        raise NotImplementedError

    def _set_is_busy(self, busy: bool) -> None:
        raise NotImplementedError

    async def _read(self,
                    path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
                    map: uvm_reg_map = None,
                    parent: uvm_sequence_base = None,
                    prior: int = -1,
                    extension: uvm_object = None,
                    fname: str = "",
                    lineno: int = 0) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def _atomic(self, on: bool) -> None:
        raise NotImplementedError

    # TODO: look at method definition it as multiple return values
    def _check_access(self,
                      rw: uvm_reg_item,
                      map_info: uvm_reg_map_info) -> bool:
        raise NotImplementedError

    def _is_locked_by_field(self) -> bool:
        raise NotImplementedError

    def do_check(self,
                 expected: uvm_reg_data_t,
                 actual: uvm_reg_data_t,
                 map: uvm_reg_map) -> bool:
        raise NotImplementedError

    async def do_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def do_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    def do_predict(self,
                   rw: uvm_reg_item,
                   kind: uvm_predict_e,
                   be: uvm_reg_byte_en_t = -1) -> bool:
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

    # TODO: Check method definition
    def get_hdl_path(self,
                     paths: list[uvm_hdl_path_concat],
                     kind: str = "") -> None:
        raise NotImplementedError

    # TODO: Check method definition
    def get_hdl_path_kind(self, kinds: list[str]) -> None:
        raise NotImplementedError

    def get_full_hdl_path(self,
                          paths: list[uvm_hdl_path_concat],
                          kind: str = "",
                          separator: str = ".") -> None:
        raise NotImplementedError

    async def backdoor_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def backdoor_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    def backdoor_read_func(self, rw: uvm_reg_item) -> uvm_status_e:
        raise NotImplementedError

    def backdoor_watch(self) -> None:
        raise NotImplementedError

    def include_coverage(self,
                         scope: str,
                         models: uvm_reg_cvr_t,
                         accessor: uvm_object = None) -> None:
        raise NotImplementedError

    def build_coverage(self, models: uvm_reg_cvr_t) -> uvm_reg_cvr_t:
        raise NotImplementedError

    def add_coverage(self, models: uvm_reg_cvr_t) -> None:
        raise NotImplementedError

    def has_coverage(self, models: uvm_reg_cvr_t) -> bool:
        raise NotImplementedError

    def set_coverage(self, is_on: uvm_reg_cvr_t) -> uvm_reg_cvr_t:
        raise NotImplementedError

    def get_coverage(self, is_on: uvm_reg_cvr_t) -> bool:
        raise NotImplementedError

    def sample(self,
               data: uvm_reg_data_t,
               byte_en: uvm_reg_data_t,
               is_read: bool,
               map: uvm_reg_map) -> None:
        raise NotImplementedError

    def sample_values(self) -> None:
        raise NotImplementedError

    def _sample(self,
                data: uvm_reg_data_t,
                byte_en: uvm_reg_data_t,
                is_read: bool,
                map: uvm_reg_map) -> None:
        self.sample(data, byte_en, is_read, map)

# TODO: register callback
# `uvm_register_cb(uvm_reg, uvm_reg_cbs)

    async def pre_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def post_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def pre_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def post_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

# TODO: Should this be dunder methods?
#   extern virtual function void            do_print (uvm_printer printer);
#   extern virtual function string          convert2string();
#   extern virtual function uvm_object      clone      ();
#   extern virtual function void            do_copy    (uvm_object rhs);
#   extern virtual function bit             do_compare (uvm_object  rhs,
#                                                       uvm_comparer comparer);
#   extern virtual function void            do_pack    (uvm_packer packer);
#   extern virtual function void            do_unpack  (uvm_packer packer);
