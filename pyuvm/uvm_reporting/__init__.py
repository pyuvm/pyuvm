# Copyright zeroRISC Inc.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

"""UVM reporting helpers."""

import logging
import os
from typing import Any

from pyuvm.uvm_reporting.uvm_runtime_options import get_plusarg


_ENV_VAR = "PYUVM_ENABLE_SV_UVM_STYLE_REPORTING"
_TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
_FALSE_VALUES = {"0", "false", "f", "no", "n", "off", ""}


def _parse_bool(value: Any) -> bool:
    text = str(value).strip().lower()
    if text in _TRUE_VALUES:
        return True
    if text in _FALSE_VALUES:
        return False
    return False


_sv_uvm_style_reporting_enabled = _parse_bool(os.getenv(_ENV_VAR, "0"))
_reg_model_logger = logging.getLogger("RegModel")


def set_sv_uvm_style_reporting_enabled(enabled: bool) -> None:
    """Enable or disable SV-UVM-style centralized reporting behavior."""
    global _sv_uvm_style_reporting_enabled
    _sv_uvm_style_reporting_enabled = bool(enabled)


def get_sv_uvm_style_reporting_enabled() -> bool:
    """Return whether SV-UVM-style centralized reporting behavior is enabled."""
    plusarg_value = get_plusarg(_ENV_VAR)
    if plusarg_value is not None:
        return _parse_bool(plusarg_value)
    return _sv_uvm_style_reporting_enabled


def uvm_report_warning(obj: Any, report_id: str, msg: str) -> None:
    """Issue a warning through SV-UVM reporting or the RegModel logger."""
    if get_sv_uvm_style_reporting_enabled():
        obj.uvm_report.warning(report_id, msg)
    else:
        _reg_model_logger.warning(msg)


def uvm_report_error(obj: Any, report_id: str, msg: str) -> None:
    """Issue an error through SV-UVM reporting or the RegModel logger."""
    if get_sv_uvm_style_reporting_enabled():
        obj.uvm_report.error(report_id, msg)
    else:
        _reg_model_logger.error(msg)


from pyuvm.uvm_reporting.uvm_verbosity import (
    UVM_DEBUG,
    UVM_ERROR,
    UVM_FATAL,
    UVM_FULL,
    UVM_HIGH,
    UVM_INFO,
    UVM_LOW,
    UVM_MEDIUM,
    UVM_NONE,
    UVM_WARNING,
    parse_uvm_verbosity,
    resolve_uvm_verbosity,
    uvm_reporter,
)

__all__ = [
    "UVM_DEBUG",
    "UVM_ERROR",
    "UVM_FATAL",
    "UVM_FULL",
    "UVM_HIGH",
    "UVM_INFO",
    "UVM_LOW",
    "UVM_MEDIUM",
    "UVM_NONE",
    "UVM_WARNING",
    "parse_uvm_verbosity",
    "resolve_uvm_verbosity",
    "get_sv_uvm_style_reporting_enabled",
    "set_sv_uvm_style_reporting_enabled",
    "uvm_report_error",
    "uvm_report_warning",
    "uvm_reporter",
]
