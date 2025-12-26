from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pyuvm._reg.uvm_reg_model import uvm_access_e, uvm_status_e
from pyuvm._s05_base_classes import uvm_object
from pyuvm._s14_15_python_sequences import uvm_sequence_base, uvm_sequence_item

if TYPE_CHECKING:
    from pyuvm._reg.uvm_reg_map import uvm_reg_map
    from pyuvm._reg.uvm_reg_model import (
        uvm_door_e,
        uvm_elem_kind_e,
        uvm_reg_addr_t,
        uvm_reg_byte_en_t,
        uvm_reg_data_t,
    )

__all__ = ["uvm_reg_item", "uvm_reg_bus_op"]


class uvm_reg_item(uvm_sequence_item):
    def __init__(self, name: str = ""):
        super().__init__(name)
        self.element_kind: uvm_elem_kind_e = None
        self.element: uvm_object = None
        self.kind: uvm_access_e = None
        self.value: list[uvm_reg_data_t] = list()
        self.offset: uvm_reg_addr_t = None
        self.status: uvm_status_e = uvm_status_e.UVM_IS_OK
        self.local_map: uvm_reg_map = None
        self.map: uvm_reg_map = None
        self.path: uvm_door_e = None
        self.parent: uvm_sequence_base = None
        self.prior: int = -1
        self.extension: uvm_object = None
        self.bd_kind: str = None
        self.fname: str = None
        self.lineno: int = None

    def set_element_kind(self, element_kind: uvm_elem_kind_e) -> None:
        self.element_kind = element_kind

    def get_element_kind(self) -> uvm_elem_kind_e:
        return self.element_kind

    def set_element(self, element: uvm_object) -> None:
        self.element = element

    def get_element(self) -> uvm_object:
        return self.element

    def set_kind(self, kind: uvm_access_e) -> None:
        self.kind = kind

    def get_kind(self) -> uvm_access_e:
        return self.kind

    def set_value(self, value: uvm_reg_data_t, idx: int = 0) -> None:
        # NOTE: When extending the value array the items value is set to 0
        if idx >= len(self.value):
            for _ in range(idx - len(self.value) + 1):
                self.value.append(0)
        self.value[idx] = value

    def get_value(self, idx: int = 0) -> uvm_reg_data_t:
        try:
            return self.value[idx]
        except IndexError:
            return 0

    def set_value_size(self, sz: int) -> None:
        self.value = [0] * sz

    def get_value_size(self) -> int:
        return len(self.value)

    def set_value_array(self, value: list[uvm_reg_data_t]) -> None:
        self.value = value

    # TODO: Document
    def get_value_array(self) -> list[uvm_reg_data_t]:
        return self.value

    def set_offset(self, offset: uvm_reg_addr_t) -> None:
        self.offset = offset

    def get_offset(self) -> uvm_reg_addr_t:
        return self.offset

    def set_status(self, status: uvm_status_e) -> None:
        self.status = status

    def get_status(self) -> uvm_status_e:
        return self.status

    def set_local_map(self, map: uvm_reg_map) -> None:
        self.local_map = map

    def get_local_map(self) -> uvm_reg_map:
        return self.local_map

    def set_map(self, map: uvm_reg_map) -> None:
        self.map = map

    def get_map(self) -> uvm_reg_map:
        return self.map

    def set_door(self, door: uvm_door_e) -> None:
        self.path = door

    def get_door(self) -> uvm_door_e:
        return self.path

    def set_parent_sequence(self, parent: uvm_sequence_base) -> None:
        self.parent = parent

    def get_parent_sequence(self) -> uvm_sequence_base:
        return self.parent

    def set_priority(self, value: int) -> None:
        self.prior = value

    def get_priority(self) -> int:
        return self.prior

    def set_extension(self, value: uvm_object) -> None:
        self.extension = value

    def get_extension(self) -> uvm_object:
        return self.extension

    def set_bd_kind(self, bd_kind: str) -> None:
        self.bd_kind = bd_kind

    def get_bd_kind(self) -> str:
        return self.bd_kind

    def set_fname(self, fname: str) -> None:
        self.fname = fname

    def get_fname(self) -> str:
        return self.fname

    def set_line(self, line: int) -> None:
        self.lineno = line

    def get_line(self) -> int:
        return self.lineno


@dataclass
class uvm_reg_bus_op:
    kind: uvm_access_e = uvm_access_e.UVM_READ
    addr: uvm_reg_addr_t = 0
    data: uvm_reg_data_t = 0
    n_bits: int = 0
    byte_en: uvm_reg_byte_en_t = 0
    status: uvm_status_e = uvm_status_e.UVM_NOT_OK
