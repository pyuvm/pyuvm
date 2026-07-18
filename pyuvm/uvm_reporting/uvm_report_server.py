# Copyright zeroRISC Inc.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

"""Centralized SV-UVM style reporting server."""

from __future__ import annotations

import logging
import textwrap
from dataclasses import dataclass
from typing import Any

from pyuvm.uvm_reporting.uvm_report_catcher import (
    uvm_report_catcher,
    uvm_report_message,
)

UVM_INFO = "INFO"
UVM_WARNING = "WARNING"
UVM_ERROR = "ERROR"
UVM_FATAL = "FATAL"


@dataclass
class uvm_report_policy:
    """End-of-test fail policy."""

    fail_on_warning: bool = False
    fail_on_error: bool = True
    fail_on_fatal: bool = True
    max_quit_count: int = 1
    test_status_label: str = "TEST_STATUS"


@dataclass
class uvm_report_stats:
    """Aggregated severities for the current test run."""

    info_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    fatal_count: int = 0
    error_quit_count: int = 0

    def clear(self) -> None:
        self.info_count = 0
        self.warning_count = 0
        self.error_count = 0
        self.fatal_count = 0
        self.error_quit_count = 0

    def total_fails(self, policy: uvm_report_policy) -> int:
        total = 0
        if policy.fail_on_warning:
            total += self.warning_count
        if policy.fail_on_error:
            total += self.error_count
        if policy.fail_on_fatal:
            total += self.fatal_count
        return total

    def error_quit_reached(self, policy: uvm_report_policy) -> bool:
        return int(policy.max_quit_count) > 0 and self.error_quit_count >= int(
            policy.max_quit_count
        )


class _uvm_wrapped_formatter(logging.Formatter):
    """Wrap rendered log lines without changing the underlying formatter layout."""

    def __init__(self, base_formatter: logging.Formatter, max_chars: int) -> None:
        super().__init__()
        self._base_formatter = base_formatter
        self._max_chars = int(max_chars)

    @property
    def base_formatter(self) -> logging.Formatter:
        return self._base_formatter

    def _is_uvm_report_record(self, record: logging.LogRecord) -> bool:
        return bool(getattr(record, "_uvm_report_record", False))

    def _source_name(self, record: logging.LogRecord) -> str:
        pathname = str(getattr(record, "pathname", "") or "")
        lineno = getattr(record, "lineno", 0)
        if pathname and lineno:
            return f"{pathname}({lineno})"
        return record.name

    def _display_message(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if not self._is_uvm_report_record(record):
            return message

        full_name = str(getattr(record, "uvm_full_name", "") or "")
        report_id = str(getattr(record, "report_id", "") or "")
        prefix = ""
        if full_name:
            prefix = f"[{full_name}]: "
        if report_id:
            return f"{prefix}[{report_id}] {message}"
        if prefix:
            return f"{prefix}{message}"
        return message

    def format(self, record: logging.LogRecord) -> str:
        display_message = self._display_message(record)
        clone = logging.makeLogRecord(record.__dict__.copy())
        clone.msg = display_message
        clone.args = ()
        if self._is_uvm_report_record(record):
            clone.name = self._source_name(record)

        rendered = self._base_formatter.format(clone)
        if self._max_chars <= 0 or len(rendered) <= self._max_chars:
            return rendered

        if not display_message:
            return rendered

        msg_start = rendered.rfind(display_message)
        if msg_start < 0:
            return rendered

        prefix = rendered[:msg_start]
        indent = " " * len(prefix)
        wrapped_lines: list[str] = []
        message_lines = display_message.splitlines() or [display_message]

        for idx, msg_line in enumerate(message_lines):
            line_prefix = prefix if idx == 0 else indent
            chunks = textwrap.wrap(
                msg_line,
                width=max(1, self._max_chars),
                break_long_words=False,
                break_on_hyphens=False,
                replace_whitespace=False,
                drop_whitespace=False,
            )
            if chunks:
                wrapped_lines.append(f"{line_prefix}{chunks[0]}")
                wrapped_lines.extend(f"{indent}{chunk}" for chunk in chunks[1:])
            else:
                wrapped_lines.append(line_prefix.rstrip())
        return "\n".join(wrapped_lines)


class uvm_report_server:
    """Singleton server that emulates SV report_server/report_catcher behavior."""

    _instance: uvm_report_server | None = None

    def __init__(self) -> None:
        self._root_logger: logging.Logger = logging.getLogger("uvm")
        self._verbosity: int = 100
        self._print_char_len: int = 300
        self._verbosity_hier: dict[str, int] = {}
        self._policy = uvm_report_policy()
        self._stats = uvm_report_stats()
        self._catcher = uvm_report_catcher("uvm_report_catcher")
        self._attached: list[tuple[logging.Handler, logging.Formatter | None]] = []
        self._attached_keys: set[int] = set()
        self._logger_full_names: dict[int, str] = {}
        self._quit_count_message_emitted = False
        self._initialized = False

    @classmethod
    def get(cls) -> uvm_report_server:
        if cls._instance is None:
            cls._instance = uvm_report_server()
        return cls._instance

    @classmethod
    def get_or_none(cls) -> uvm_report_server | None:
        if cls._instance is not None and cls._instance._initialized:
            return cls._instance
        return None

    @classmethod
    def create(
        cls,
        root_logger: logging.Logger | None = None,
        verbosity: int = 100,
        policy: uvm_report_policy | None = None,
        print_char_len: int = 300,
    ) -> uvm_report_server:
        manager = cls.get()
        manager.initialize(
            root_logger=root_logger,
            verbosity=verbosity,
            policy=policy,
            print_char_len=print_char_len,
        )
        return manager

    @property
    def catcher(self) -> uvm_report_catcher:
        return self._catcher

    @property
    def verbosity(self) -> int:
        return self._verbosity

    @property
    def policy(self) -> uvm_report_policy:
        return self._policy

    def get_stats(self) -> uvm_report_stats:
        return self._stats

    def clear_counts(self) -> None:
        self._stats.clear()
        self._quit_count_message_emitted = False

    def initialize(
        self,
        root_logger: logging.Logger | None = None,
        verbosity: int = 100,
        policy: uvm_report_policy | None = None,
        print_char_len: int = 300,
    ) -> None:
        self.shutdown()
        self._root_logger = (
            root_logger if root_logger is not None else logging.getLogger("uvm")
        )
        self._verbosity = int(verbosity)
        self._print_char_len = int(print_char_len)
        self._policy = policy if policy is not None else uvm_report_policy()
        self._stats.clear()
        self._quit_count_message_emitted = False
        self._logger_full_names.clear()
        self._catcher = uvm_report_catcher("uvm_report_catcher")
        self._attach_formatters()
        self._initialized = True

    def shutdown(self) -> None:
        for handler, formatter in self._attached:
            try:
                handler.setFormatter(formatter)
            except Exception:
                pass
        self._attached.clear()
        self._attached_keys.clear()
        self._logger_full_names.clear()
        self._initialized = False

    def set_verbosity(self, verbosity: int) -> None:
        self._verbosity = int(verbosity)

    def set_verbosity_hier(self, prefix: str, verbosity: int) -> None:
        self._verbosity_hier[str(prefix)] = int(verbosity)

    def add_change_sev(self, report_id: str, msg_regex: str, sev: Any) -> None:
        self._catcher.add_change_sev(report_id, msg_regex, sev)

    def remove_change_sev(self, report_id: str, msg_regex: str = "") -> None:
        self._catcher.remove_change_sev(report_id, msg_regex)

    def emit_uvm(
        self,
        severity: str,
        msg: str,
        report_id: str = "",
        verbosity: int = 100,
        logger: logging.Logger | None = None,
        stacklevel: int = 2,
        uvm_full_name: str = "",
    ) -> None:
        sev = self._normalize_severity(severity)
        log = logger if logger is not None else self._root_logger

        if sev == UVM_INFO:
            eff = self._effective_verbosity(log.name if hasattr(log, "name") else "")
            if int(verbosity) > eff:
                return

        original_sev = sev
        sev = self._apply_catcher(msg, sev, report_id)
        if self._should_suppress_for_quit_count(sev):
            return
        if sev != original_sev:
            self._log_severity_change(
                log,
                original_sev,
                sev,
                report_id,
                stacklevel + 1,
                uvm_full_name,
            )
        level = self._severity_to_level(sev)

        self._count_severity(sev)

        extra = self._uvm_record_extra(report_id, uvm_full_name)
        try:
            log.log(level, msg, extra=extra, stacklevel=stacklevel)
        except TypeError:
            log.log(level, msg, extra=extra)

        if sev == UVM_ERROR:
            self._maybe_log_quit_count_reached(log, stacklevel + 1, uvm_full_name)

        if sev == UVM_FATAL:
            raise RuntimeError(f"UVM_FATAL: {msg}")

    def assert_no_failures(self, context: str = "") -> None:
        msg = self.failure_message(context)
        if msg is not None:
            raise RuntimeError(msg)

    def failure_message(self, context: str = "") -> str | None:
        total_fails = self._stats.total_fails(self._policy)
        if total_fails <= 0:
            return None

        summary = (
            f"{self._stats.info_count} info(s), "
            f"{self._stats.warning_count} warning(s), "
            f"{self._stats.error_count} error(s), "
            f"{self._stats.fatal_count} fatal(s)"
        )
        prefix = f"{context}: " if context else ""
        if self._stats.error_quit_reached(self._policy):
            return (
                f"{prefix}Quit count reached: {self._stats.error_quit_count} "
                f"of {self._policy.max_quit_count} (UVM_ERROR). "
                f"Detected report failures at termination ({summary})"
            )
        return f"{prefix}Detected report failures at termination ({summary})"

    def log_summary(self, logger: logging.Logger, uvm_full_name: str = "") -> None:
        stats = self._stats
        full_name = str(uvm_full_name).strip() or self._logger_uvm_full_name(logger)
        self._log_uvm_info(logger, "--- UVM Report Summary ---", full_name)
        self._log_uvm_info(logger, "** Report counts by severity", full_name)
        self._log_uvm_info(logger, f"UVM_INFO    : {stats.info_count:4d}", full_name)
        self._log_uvm_info(logger, f"UVM_WARNING : {stats.warning_count:4d}", full_name)
        self._log_uvm_info(logger, f"UVM_ERROR   : {stats.error_count:4d}", full_name)
        self._log_uvm_info(logger, f"UVM_FATAL   : {stats.fatal_count:4d}", full_name)
        max_quit_count = self._max_quit_count_text()
        self._log_uvm_info(
            logger,
            f"Quit count : {stats.error_quit_count:5d} of {max_quit_count} (UVM_ERROR)",
            full_name,
        )

    def error_quit_count_reached(self) -> bool:
        return self._stats.error_quit_reached(self._policy)

    def log_final_status(
        self,
        logger: logging.Logger,
        context: str = "",
        prior_failure_msg: str | None = None,
        test_status_label: str | None = None,
        uvm_full_name: str = "",
    ) -> str | None:
        """Log final test status and return terminal failure message if present."""
        fail_msg = (
            prior_failure_msg
            if prior_failure_msg is not None
            else self.failure_message(context)
        )
        label = self._final_status_label(test_status_label)
        full_name = str(uvm_full_name).strip() or self._logger_uvm_full_name(logger)
        if fail_msg is not None:
            self._log_uvm_info(logger, f"{label}: FAILED", full_name)
            return fail_msg
        self._log_uvm_info(logger, f"{label}: PASSED", full_name)
        return None

    def _attach_formatters(self) -> None:
        loggers: list[logging.Logger] = []

        loggers.append(logging.getLogger())
        loggers.append(logging.getLogger("uvm"))
        loggers.append(self._root_logger)
        loggers.append(logging.getLogger("cocotb"))
        loggers.append(logging.getLogger("pyuvm"))
        loggers.append(logging.getLogger("test"))

        for logger_obj in logging.Logger.manager.loggerDict.values():
            if isinstance(logger_obj, logging.Logger):
                loggers.append(logger_obj)

        for log in loggers:
            self.register_logger(log)

    def register_logger(
        self, log: logging.Logger | None, uvm_full_name: str = ""
    ) -> None:
        if log is None:
            return

        full_name = str(uvm_full_name).strip()
        if full_name:
            self._logger_full_names[id(log)] = full_name

        for handler in log.handlers:
            hkey = id(handler)
            if hkey in self._attached_keys:
                continue
            original_formatter = handler.formatter
            base_formatter = original_formatter or logging.Formatter("%(message)s")
            if self._print_char_len > 0:
                if isinstance(base_formatter, _uvm_wrapped_formatter):
                    wrapped = _uvm_wrapped_formatter(
                        base_formatter.base_formatter,
                        self._print_char_len,
                    )
                    base_formatter = base_formatter.base_formatter
                else:
                    wrapped = _uvm_wrapped_formatter(
                        base_formatter, self._print_char_len
                    )
                handler.setFormatter(wrapped)
            self._attached.append((handler, original_formatter))
            self._attached_keys.add(hkey)

    def _effective_verbosity(self, logger_name: str) -> int:
        best = self._verbosity
        best_len = -1
        for prefix, level in self._verbosity_hier.items():
            if logger_name.startswith(prefix) and len(prefix) > best_len:
                best = level
                best_len = len(prefix)
        return best

    def _apply_catcher(self, msg: str, severity: str, report_id: str = "") -> str:
        report = uvm_report_message(report_id=report_id, message=msg, severity=severity)
        self._catcher.catch(report)
        return self._normalize_severity(report.severity)

    def _count_severity(self, severity: str) -> None:
        if severity == UVM_INFO:
            self._stats.info_count += 1
        elif severity == UVM_WARNING:
            self._stats.warning_count += 1
        elif severity == UVM_ERROR:
            self._stats.error_count += 1
            self._stats.error_quit_count += 1
        elif severity == UVM_FATAL:
            self._stats.fatal_count += 1

    def _should_suppress_for_quit_count(self, severity: str) -> bool:
        return self._normalize_severity(severity) == UVM_ERROR and (
            self.error_quit_count_reached()
        )

    def _maybe_log_quit_count_reached(
        self,
        logger: logging.Logger,
        stacklevel: int = 2,
        uvm_full_name: str = "",
    ) -> None:
        if self._quit_count_message_emitted:
            return
        if not self._stats.error_quit_reached(self._policy):
            return

        self._quit_count_message_emitted = True
        msg = (
            f"Quit count reached: {self._stats.error_quit_count} "
            f"of {self._policy.max_quit_count} (UVM_ERROR)"
        )
        extra = self._uvm_record_extra("MAXQUIT", uvm_full_name)
        try:
            logger.warning(msg, extra=extra, stacklevel=stacklevel)
        except TypeError:
            logger.warning(msg, extra=extra)

    def _log_severity_change(
        self,
        logger: logging.Logger,
        original_severity: str,
        new_severity: str,
        report_id: str = "",
        stacklevel: int = 2,
        uvm_full_name: str = "",
    ) -> None:
        msg = f"Severity changed from UVM_{original_severity} to UVM_{new_severity}"
        if report_id:
            msg = f"{msg} for report ID '{report_id}'"
        extra = self._uvm_record_extra("SEVCHG", uvm_full_name)
        try:
            logger.info(msg, extra=extra, stacklevel=stacklevel)
        except TypeError:
            logger.info(msg, extra=extra)

    def _uvm_record_extra(
        self, report_id: str = "", uvm_full_name: str = ""
    ) -> dict[str, str | bool]:
        extra: dict[str, str | bool] = {"_uvm_report_record": True}
        if report_id:
            extra["report_id"] = str(report_id)
        full_name = str(uvm_full_name).strip()
        if full_name:
            extra["uvm_full_name"] = full_name
        return extra

    def _log_uvm_info(
        self,
        logger: logging.Logger,
        msg: str,
        uvm_full_name: str = "",
        stacklevel: int = 2,
    ) -> None:
        extra = self._uvm_record_extra(uvm_full_name=uvm_full_name)
        try:
            logger.info(msg, extra=extra, stacklevel=stacklevel)
        except TypeError:
            logger.info(msg, extra=extra)

    def _logger_uvm_full_name(self, logger: logging.Logger) -> str:
        registered = self._logger_full_names.get(id(logger))
        if registered:
            return registered

        name = str(getattr(logger, "name", "") or "")
        if name == "uvm":
            return "uvm"
        if not name.startswith("uvm."):
            return ""
        return name[4:]

    def _max_quit_count_text(self) -> str:
        if int(self._policy.max_quit_count) == 0:
            return "UNLIMITED"
        return f"{self._policy.max_quit_count:5d}"

    def _final_status_label(self, override: str | None = None) -> str:
        label = self._policy.test_status_label if override is None else override
        label = str(label).strip()
        return label if label else "TEST_STATUS"

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

    def _severity_to_level(self, severity: str) -> int:
        sev = self._normalize_severity(severity)
        if sev == UVM_INFO:
            return logging.INFO
        if sev == UVM_WARNING:
            return logging.WARNING
        if sev == UVM_ERROR:
            return logging.ERROR
        return logging.CRITICAL
