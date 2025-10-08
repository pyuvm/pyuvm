from pyuvm import uvm_object, uvm_sequence_item
from pyuvm.reg.uvm_reg_item import uvm_reg_bus_op

__all__ = ["uvm_reg_adapter", "uvm_reg_tlm_adapter"]


class uvm_reg_adapter(uvm_object):
    def __init__(self, name: str = ""):
        raise NotImplementedError

    def reg2bus(self, rw: uvm_reg_bus_op) -> uvm_sequence_item:
        raise NotImplementedError

    def bus2reg(self,
                bus_item: uvm_sequence_item,
                rw: uvm_reg_bus_op) -> None:
        raise NotImplementedError


class uvm_reg_tlm_adapter(uvm_reg_adapter):
    def __init__(self, name: str = ""):
        super().__init__(name)

    def reg2bus(self, rw: uvm_reg_bus_op) -> uvm_sequence_item:
        raise NotImplementedError

    def bus2reg(self,
                bus_item: uvm_sequence_item,
                rw: uvm_reg_bus_op) -> None:
        raise NotImplementedError
