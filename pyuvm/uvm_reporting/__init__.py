# Copyright zeroRISC Inc.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

"""UVM reporting helpers."""

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
    "uvm_reporter",
]
