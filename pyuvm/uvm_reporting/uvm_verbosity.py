# Copyright zeroRISC Inc.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

"""SV-UVM style verbosity helpers and reporter."""

from __future__ import annotations

import logging
from typing import Any

from pyuvm.uvm_reporting.uvm_report_catcher import uvm_report_catcher
from pyuvm.uvm_reporting.uvm_report_server import uvm_report_server

UVM_NONE = 0
UVM_LOW = 100
UVM_MEDIUM = 200
UVM_HIGH = 300
UVM_FULL = 400
UVM_DEBUG = 500

UVM_INFO = "INFO"
UVM_WARNING = "WARNING"
UVM_ERROR = "ERROR"
UVM_FATAL = "FATAL"


_VERBOSITY_MAP = {
    "NONE": UVM_NONE,
    "LOW": UVM_LOW,
    "MEDIUM": UVM_MEDIUM,
    "HIGH": UVM_HIGH,
    "FULL": UVM_FULL,
    "DEBUG": UVM_DEBUG,
}


def parse_uvm_verbosity(raw: str | None, default: int = UVM_LOW) -> int:
    """Parse UVM_VERBOSITY from symbolic level or integer string."""
    if raw is None:
        return default
    text = str(raw).strip()
    if not text:
        return default
    key = text.upper()
    if key in _VERBOSITY_MAP:
        return _VERBOSITY_MAP[key]
    try:
        return int(text, 0)
    except ValueError:
        return default


def resolve_uvm_verbosity(inherited: int, cfg: Any | None = None) -> int:
    """Resolve verbosity with optional cfg override."""
    if cfg is None:
        return int(inherited)
    raw = getattr(cfg, "uvm_verbosity", None)
    if raw is None:
        return int(inherited)
    if isinstance(raw, int):
        return int(raw)
    return parse_uvm_verbosity(str(raw), int(inherited))


class uvm_reporter:
    """Centralized UVM-style reporter."""

    def __init__(
        self,
        logger: logging.Logger,
        verbosity: int = UVM_LOW,
        full_name: str = "",
    ) -> None:
        self._logger = logger
        self._verbosity = int(verbosity)
        self._full_name = str(full_name)
        self._local_catcher = uvm_report_catcher("uvm_report_catcher")
        self._sync_with_manager()

    @property
    def verbosity(self) -> int:
        return self._verbosity

    @property
    def catcher(self) -> uvm_report_catcher:
        manager = uvm_report_server.get_or_none()
        if manager is not None:
            return manager.catcher
        return self._local_catcher

    def set_logger(self, logger: logging.Logger) -> None:
        self._logger = logger
        self._sync_with_manager()

    def set_full_name(self, full_name: str) -> None:
        self._full_name = str(full_name)
        self._sync_with_manager()

    def _sync_with_manager(self) -> None:
        manager = uvm_report_server.get_or_none()
        if manager is not None:
            manager.register_logger(self._logger, self._full_name)

    def set_verbosity(self, verbosity: int) -> None:
        self._verbosity = int(verbosity)
        manager = uvm_report_server.get_or_none()
        if manager is not None:
            manager.register_logger(self._logger, self._full_name)
            manager.set_verbosity(self._verbosity)

    def should_log(self, msg_verbosity: int = UVM_LOW) -> bool:
        return int(msg_verbosity) <= self._verbosity

    def _format_fallback_message(self, report_id: str, msg: str) -> str:
        if report_id:
            return f"[{report_id}] {msg}"
        return msg

    def _emit(self, level: str, msg: str, stacklevel: int = 2) -> None:
        log_fn = getattr(self._logger, level)
        try:
            log_fn(msg, stacklevel=stacklevel)
        except TypeError:
            # Fallback for logger adapters that do not accept stacklevel.
            log_fn(msg)

    def _normalize_severity(self, severity: Any) -> str:
        text = str(severity).strip().upper()
        if text.endswith(".INFO"):
            return UVM_INFO
        if text.endswith(".WARNING"):
            return UVM_WARNING
        if text.endswith(".ERROR"):
            return UVM_ERROR
        if text.endswith(".FATAL") or text.endswith(".CRITICAL"):
            return UVM_FATAL
        if text in {UVM_INFO, UVM_WARNING, UVM_ERROR, UVM_FATAL}:
            return text
        return UVM_INFO

    def _apply_local_catcher(self, severity: str, report_id: str, msg: str) -> str:
        _action, new_severity = self._local_catcher.catch_fields(
            report_id, msg, severity
        )
        return self._normalize_severity(new_severity)

    def add_change_sev(self, report_id: str, msg_regex: str, sev: Any) -> None:
        manager = uvm_report_server.get_or_none()
        if manager is not None:
            manager.add_change_sev(report_id, msg_regex, sev)
        else:
            self._local_catcher.add_change_sev(report_id, msg_regex, sev)

    def remove_change_sev(self, report_id: str, msg_regex: str = "") -> None:
        manager = uvm_report_server.get_or_none()
        if manager is not None:
            manager.remove_change_sev(report_id, msg_regex)
        else:
            self._local_catcher.remove_change_sev(report_id, msg_regex)

    def info(self, report_id: str, msg: str, verbosity: int) -> None:
        manager = uvm_report_server.get_or_none()
        if manager is None:
            if not self.should_log(verbosity):
                return
            severity = self._apply_local_catcher(UVM_INFO, report_id, msg)
            level = "info"
            if severity == UVM_WARNING:
                level = "warning"
            elif severity == UVM_ERROR:
                level = "error"
            elif severity == UVM_FATAL:
                level = "critical"
            self._emit(level, self._format_fallback_message(report_id, msg), 4)
            if severity == UVM_FATAL:
                raise RuntimeError(f"UVM_FATAL: {msg}")
            return
        self._sync_with_manager()
        manager.emit_uvm(
            UVM_INFO,
            msg,
            report_id=report_id,
            verbosity=verbosity,
            logger=self._logger,
            stacklevel=3,
            uvm_full_name=self._full_name,
        )

    def warning(self, report_id: str, msg: str) -> None:
        manager = uvm_report_server.get_or_none()
        if manager is None:
            severity = self._apply_local_catcher(UVM_WARNING, report_id, msg)
            level = "warning"
            if severity == UVM_INFO:
                level = "info"
            elif severity == UVM_ERROR:
                level = "error"
            elif severity == UVM_FATAL:
                level = "critical"
            self._emit(level, self._format_fallback_message(report_id, msg), 4)
            if severity == UVM_FATAL:
                raise RuntimeError(f"UVM_FATAL: {msg}")
            return
        self._sync_with_manager()
        manager.emit_uvm(
            UVM_WARNING,
            msg,
            report_id=report_id,
            logger=self._logger,
            stacklevel=3,
            uvm_full_name=self._full_name,
        )

    def error(self, report_id: str, msg: str) -> None:
        manager = uvm_report_server.get_or_none()
        if manager is None:
            severity = self._apply_local_catcher(UVM_ERROR, report_id, msg)
            level = "error"
            if severity == UVM_INFO:
                level = "info"
            elif severity == UVM_WARNING:
                level = "warning"
            elif severity == UVM_FATAL:
                level = "critical"
            self._emit(level, self._format_fallback_message(report_id, msg), 4)
            if severity == UVM_FATAL:
                raise RuntimeError(f"UVM_FATAL: {msg}")
            return
        self._sync_with_manager()
        manager.emit_uvm(
            UVM_ERROR,
            msg,
            report_id=report_id,
            logger=self._logger,
            stacklevel=3,
            uvm_full_name=self._full_name,
        )

    def fatal(self, report_id: str, msg: str) -> None:
        manager = uvm_report_server.get_or_none()
        if manager is None:
            severity = self._apply_local_catcher(UVM_FATAL, report_id, msg)
            level = "critical"
            if severity == UVM_INFO:
                level = "info"
            elif severity == UVM_WARNING:
                level = "warning"
            elif severity == UVM_ERROR:
                level = "error"
            self._emit(level, self._format_fallback_message(report_id, msg), 4)
            if severity == UVM_FATAL:
                raise RuntimeError(f"UVM_FATAL: {msg}")
            return
        self._sync_with_manager()
        manager.emit_uvm(
            UVM_FATAL,
            msg,
            report_id=report_id,
            logger=self._logger,
            stacklevel=3,
            uvm_full_name=self._full_name,
        )
