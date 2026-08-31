from pyuvm._reg.uvm_reg import uvm_reg
from pyuvm._reg.uvm_reg_sequence import uvm_reg_frontdoor

__all__ = ["uvm_reg_indirect_data", "uvm_reg_indirect_ftdr_seq"]


class uvm_reg_indirect_data(uvm_reg):
    def __init__(
        self, name: str = "uvm_reg_indirect", n_bits: int = 0, has_coverage: int = 0
    ) -> None:
        super().__init__(name, n_bits, has_coverage)
        raise NotImplementedError


class uvm_reg_indirect_ftdr_seq(uvm_reg_frontdoor):
    def __init__(self, addr_reg: uvm_reg, idx: int, data_reg: uvm_reg) -> None:
        super().__init__("uvm_reg_indirect_ftdr_seq")
        raise NotImplementedError
