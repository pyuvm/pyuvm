from __future__ import annotations

from pyuvm import uvm_object, uvm_sequence_base, uvm_sequence_item
from pyuvm.reg.uvm_reg_map import uvm_reg_map
from pyuvm.reg.uvm_reg_model import (
    uvm_access_e,
    uvm_door_e,
    uvm_elem_kind_e,
    uvm_reg_addr_t,
    uvm_reg_byte_en_t,
    uvm_reg_data_t,
    uvm_status_e,
)

__all__ = ["uvm_reg_item", "uvm_reg_bus_op"]


class uvm_reg_item(uvm_sequence_item):
    def __init__(self, name: str = ""):
        raise NotImplementedError

    def set_element_kind(element_kind: uvm_elem_kind_e) -> None:
        raise NotImplementedError

    def get_element_kind(self) -> uvm_elem_kind_e:
        raise NotImplementedError

    def set_element(self, element: uvm_object) -> None:
        raise NotImplementedError

    def get_element(self) -> uvm_object:
        raise NotImplementedError

    def set_kind(self, kind: uvm_access_e) -> None:
        raise NotImplementedError

    def get_kind(self) -> uvm_access_e:
        raise NotImplementedError

    def set_value(self, value: uvm_reg_data_t, idx: int = 0) -> None:
        raise NotImplementedError

    def get_value(self, idx: int = 0) -> uvm_reg_data_t:
        raise NotImplementedError

    def set_value_size(self, sz: int) -> None:
        raise NotImplementedError

    def get_value_size(self) -> int:
        raise NotImplementedError

    def set_value_array(self, value: list[uvm_reg_data_t]) -> None:
        raise NotImplementedError

    def get_value_array(self, value: list[uvm_reg_data_t]) -> None:
        raise NotImplementedError

    def set_offset(self, offset: uvm_reg_addr_t) -> None:
        raise NotImplementedError

    def get_offset(self) -> uvm_reg_addr_t:
        raise NotImplementedError

    def set_status(self, status: uvm_status_e) -> None:
        raise NotImplementedError

    def get_status(self) -> uvm_status_e:
        raise NotImplementedError

    def set_local_map(self, map: uvm_reg_map) -> None:
        raise NotImplementedError

    def get_local_map(self) -> uvm_reg_map:
        raise NotImplementedError

    def set_map(self, map: uvm_reg_map) -> None:
        raise NotImplementedError

    def get_map(self) -> uvm_reg_map:
        raise NotImplementedError

    def set_door(self, door: uvm_door_e) -> None:
        raise NotImplementedError

    def get_door(self) -> uvm_door_e:
        raise NotImplementedError

    def set_parent_sequence(self, parent: uvm_sequence_base) -> None:
        raise NotImplementedError

    def get_parent_sequence(self) -> uvm_sequence_base:
        raise NotImplementedError

    def set_priority(self, value: int) -> None:
        raise NotImplementedError

    def get_priority(self) -> int:
        raise NotImplementedError

    def set_extension(self, value: uvm_object) -> None:
        raise NotImplementedError

    def get_extension(self) -> uvm_object:
        raise NotImplementedError

    def set_bd_kind(bd_kind: str) -> None:
        raise NotImplementedError

    def get_bd_kind(self) -> str:
        raise NotImplementedError

    def set_fname(fname: str) -> None:
        raise NotImplementedError

    def get_fname(self) -> str:
        raise NotImplementedError

    def set_line(line: int) -> None:
        raise NotImplementedError

    def get_line(self) -> int:
        raise NotImplementedError


class uvm_reg_bus_op:
    kind: uvm_access_e
    addr: uvm_reg_addr_t
    data: uvm_reg_data_t
    n_bits: int
    byte_en: uvm_reg_byte_en_t
    status: uvm_status_e
