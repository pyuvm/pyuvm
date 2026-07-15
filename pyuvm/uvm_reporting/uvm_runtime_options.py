# Copyright zeroRISC Inc.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

"""Runtime option helpers for SV-UVM-style reporting."""

from __future__ import annotations

import os
from collections.abc import Iterable
from typing import Any

_TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}
_FALSE_VALUES = {"0", "false", "f", "no", "n", "off", ""}


def _as_names(names: str | Iterable[str]) -> tuple[str, ...]:
    if isinstance(names, str):
        return (names,)
    return tuple(str(name) for name in names)


def get_plusarg(name: str) -> str | None:
    """Return a cocotb plusarg value when cocotb exposes plusargs."""
    try:
        import cocotb
    except Exception:
        return None

    plusargs = getattr(cocotb, "plusargs", None)
    if plusargs is None:
        return None

    value = plusargs.get(name)
    if value in (None, False):
        return None
    if value is True:
        return "1"
    return str(value)


def get_runtime_option(names: str | Iterable[str], default: Any = None) -> Any:
    """Return the first matching plusarg/env value for ``names``."""
    for name in _as_names(names):
        value = get_plusarg(name)
        if value is not None:
            return value

    for name in _as_names(names):
        value = os.getenv(name)
        if value is not None:
            return value

    return default


def parse_bool_text(value: Any, default: bool = False) -> bool:
    """Parse common textual boolean forms."""
    if value is None:
        return bool(default)
    text = str(value).strip().lower()
    if text in _TRUE_VALUES:
        return True
    if text in _FALSE_VALUES:
        return False
    return bool(default)


def get_runtime_bool(names: str | Iterable[str], default: bool = False) -> bool:
    return parse_bool_text(get_runtime_option(names, None), default)


def get_runtime_int(names: str | Iterable[str], default: int = 0) -> int:
    value = get_runtime_option(names, None)
    if value is None:
        return int(default)
    try:
        return int(str(value), 0)
    except (TypeError, ValueError):
        return int(default)
