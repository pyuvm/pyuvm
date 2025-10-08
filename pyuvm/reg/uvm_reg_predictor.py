from __future__ import annotations

from pyuvm import uvm_component, uvm_phase
from pyuvm.reg.uvm_reg_item import uvm_reg_item

__all__ = ["uvm_reg_predictor"]


class uvm_predict_s:
    addr: list[bool]
    reg_item: uvm_reg_item


class uvm_reg_predictor(uvm_component):
    def __init__(self, name: str, parent: uvm_component) -> None:
        raise NotImplementedError

    def pre_predict(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    def check_phase(self, phase: uvm_phase):
        super().check_phase()
        raise NotImplementedError

    def flush(self) -> None:
        raise NotImplementedError
