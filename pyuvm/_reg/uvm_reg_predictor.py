from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pyuvm._s12_uvm_tlm_interfaces import uvm_analysis_imp
from pyuvm._s13_uvm_component import uvm_component

if TYPE_CHECKING:
    from pyuvm import uvm_analysis_port, uvm_phase
    from pyuvm._reg.uvm_reg_adapter import uvm_reg_adapter
    from pyuvm._reg.uvm_reg_item import uvm_reg_item
    from pyuvm._reg.uvm_reg_map import uvm_reg_map

__all__ = ["uvm_reg_predictor"]
logger = logging.getLogger("RegModel")


class uvm_predict_s:
    addr: list[bool]
    reg_item: uvm_reg_item


class uvm_reg_predictor(uvm_component):
    def __init__(self, name: str, parent: uvm_component) -> None:
        self.bus_in: uvm_analysis_imp = uvm_analysis_imp("bus_in")
        self.reg_ap: uvm_analysis_port = uvm_analysis_port("reg_ap")
        self.map: uvm_reg_map = None
        self.adapter: uvm_reg_adapter = None
        self._pending: list[uvm_predict_s] = list()
        raise NotImplementedError

    def pre_predict(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError("Must be implemented by user")

    def check_phase(self, phase: uvm_phase):
        super().check_phase(phase)
        if self._pending:
            string: str = ""
            for reg in self._pending:
                string += f"{reg.get_full_name()}\n"

            logger.error(
                f"There are {len(self._pending)} incomplete "
                "register transactions still pending completion:\n"
                f"{string}"
            )

    def flush(self) -> None:
        self._pending.clear()
