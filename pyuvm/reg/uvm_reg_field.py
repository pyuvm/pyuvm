from __future__ import annotations

from pyuvm import uvm_object, uvm_reg_item, uvm_reg_map, uvm_sequence_base
from pyuvm.reg.uvm_reg import uvm_reg
from pyuvm.reg.uvm_reg_map import uvm_reg_map_info
from pyuvm.reg.uvm_reg_model import (
    uvm_check_e,
    uvm_door_e,
    uvm_predict_e,
    uvm_reg_byte_en_t,
    uvm_reg_data_t,
    uvm_status_e,
)

__all__ = ["uvm_reg_field"]


class uvm_reg_field(uvm_object):

    _max_size: int
    _policy_names: set
    _reg_field_registry: dict[str, uvm_reg_field]

    def __init__(self, name: str = "uvm_reg_field") -> None:
        raise NotImplementedError

    def configure(self,
                  parent: uvm_reg,
                  size: int,
                  lsb_pos: int,
                  access: str,
                  volatile: bool,
                  reset: uvm_reg_data_t,
                  has_reset: bool,
                  is_rand: bool,
                  individually_accessible: bool) -> None:
        raise NotImplementedError

    def get_full_name(self) -> str:
        raise NotImplementedError

    def get_parent(self) -> uvm_reg:
        raise NotImplementedError

    def get_register(self) -> uvm_reg:
        raise NotImplementedError

    def get_lsb_pos(self) -> int:
        raise NotImplementedError

    def get_n_bits(self) -> int:
        raise NotImplementedError

    @staticmethod
    def get_max_size() -> int:
        raise NotImplementedError

    def set_access(self, mode: str) -> str:
        raise NotImplementedError

    def set_rand_mode(self) -> None:
        raise NotImplementedError

    @staticmethod
    def define_access(name: str) -> bool:
        raise NotImplementedError

    @staticmethod
    def _predefined_policies() -> set:
        raise NotImplementedError

    def get_access(map: uvm_reg_map = None) -> str:
        raise NotImplementedError

    def is_known_access(map: uvm_reg_map = None) -> bool:
        raise NotImplementedError

    def set_volatility(self, volatile: bool) -> None:
        raise NotImplementedError

    def is_volatile(self) -> bool:
        raise NotImplementedError

    @staticmethod
    def get_field_by_full_name(name: str) -> uvm_reg_field:
        return uvm_reg_field._reg_field_registry[name]

    def set(self,
            value: uvm_reg_data_t,
            fname: str = "",
            lineno: int = 0) -> None:
        raise NotImplementedError

    def get(self, fname: str = "", lineno: int = 0) -> uvm_reg_data_t:
        raise NotImplementedError

    def get_mirrored_value(self,
                           fname: str = "",
                           lineno: int = 0) -> uvm_reg_data_t:
        raise NotImplementedError

    def reset(self, kind: str = "HARD") -> None:
        raise NotImplementedError

    def get_reset(self, kind: str = "HARD") -> uvm_reg_data_t:
        raise NotImplementedError

    def has_reset(self, kind: str = "HARD", delete: bool = False) -> bool:
        raise NotImplementedError

    def set_reset(self, value: uvm_reg_data_t, kind: str = "HARD") -> None:
        raise NotImplementedError

    def needs_update(self) -> bool:
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

    def set_compare(self, check: uvm_check_e) -> None:
        raise NotImplementedError

    def get_compare(self) -> uvm_check_e:
        raise NotImplementedError

    def is_indv_accessible(self,
                           path: uvm_door_e,
                           local_map: uvm_reg_map) -> bool:
        raise NotImplementedError

    def predict(self,
                value: uvm_reg_data_t,
                be: uvm_reg_byte_en_t = -1,
                kind: uvm_predict_e = uvm_predict_e.UVM_PREdict_DIRECT,
                path: uvm_door_e = uvm_door_e.UVM_FRONTDOOR,
                map: uvm_reg_map = None,
                fname: str = "",
                lineno: int = 0) -> bool:
        raise NotImplementedError

    def _predict(self,
                 cur_val: uvm_reg_data_t,
                 wr_val: uvm_reg_data_t,
                 map: uvm_reg_map) -> uvm_reg_data_t:
        raise NotImplementedError

    def _update(self) -> uvm_reg_data_t:
        raise NotImplementedError

    def _check_access(self,
                      rw: uvm_reg_item,
                      map_info: uvm_reg_map_info) -> bool:
        raise NotImplementedError

    async def do_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def do_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    def do_predict(self,
                   rw: uvm_reg_item,
                   kind: uvm_predict_e = uvm_predict_e.UVM_PREdict_DIRECT,
                   be: uvm_reg_byte_en_t = -1) -> bool:
        raise NotImplementedError

    def pre_randomize(self) -> None:
        raise NotImplementedError

    def post_randomize(self) -> None:
        raise NotImplementedError

    async def pre_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def post_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def pre_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def post_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    # TODO: Should this be dunder methods?
    # extern virtual function void do_print (uvm_printer printer);
    # extern virtual function string convert2string;
    # extern virtual function uvm_object clone();
    # extern virtual function void do_copy   (uvm_object rhs);
    # extern virtual function bit  do_compare (uvm_object  rhs,
    #                                         uvm_comparer comparer);
    # extern virtual function void do_pack (uvm_packer packer);
    # extern virtual function void do_unpack (uvm_packer packer);
