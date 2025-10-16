from typing import TYPE_CHECKING

from pyuvm.reg.uvm_reg_item import uvm_reg_bus_op, uvm_reg_item
from pyuvm.s05_base_classes import uvm_object
from pyuvm.s14_15_python_sequences import uvm_sequence_item

if TYPE_CHECKING:
    from pyuvm.s14_15_python_sequences import uvm_sequence_base

__all__ = ["uvm_reg_adapter", "uvm_reg_tlm_adapter"]


class uvm_reg_adapter(uvm_object):
    def __init__(self, name: str = ""):
        self.supports_byte_enable: bool = False
        self.provides_response: bool = False
        self.parent_sequence: uvm_sequence_base = None
        self._item: uvm_reg_item = None

    def get_item(self) -> uvm_reg_item:
        return self._item

    def set_item(self, item: uvm_reg_item) -> None:
        self._item = item

    def reg2bus(self, rw: uvm_reg_bus_op) -> uvm_sequence_item:
        pass

    def bus2reg(self, bus_item: uvm_sequence_item, rw: uvm_reg_bus_op) -> None:
        pass


class uvm_reg_tlm_adapter(uvm_reg_adapter):
    def __init__(self, name: str = "uvm_reg_tlm_adapter"):
        super().__init__(name)
        raise NotImplementedError

    def reg2bus(self, rw: uvm_reg_bus_op) -> uvm_sequence_item:
        raise NotImplementedError

    def bus2reg(self, bus_item: uvm_sequence_item, rw: uvm_reg_bus_op) -> None:
        raise NotImplementedError
