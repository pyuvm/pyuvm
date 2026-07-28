"""Shared reporting helpers for the register abstraction layer."""

import logging
from typing import Any

from pyuvm.uvm_reporting import get_sv_uvm_style_reporting_enabled

_reg_model_logger = logging.getLogger("RegModel")


def uvm_reg_report_warning(obj: Any, report_id: str, msg: str) -> None:
    """Issue a RAL warning through SV-UVM reporting or the RegModel logger."""
    if get_sv_uvm_style_reporting_enabled():
        obj.uvm_report.warning(report_id, msg)
    else:
        _reg_model_logger.warning(msg)


def uvm_reg_report_error(obj: Any, report_id: str, msg: str) -> None:
    """Issue a RAL error through SV-UVM reporting or the RegModel logger."""
    if get_sv_uvm_style_reporting_enabled():
        obj.uvm_report.error(report_id, msg)
    else:
        _reg_model_logger.error(msg)


__all__ = ["uvm_reg_report_error", "uvm_reg_report_warning"]
