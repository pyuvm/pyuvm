# Copyright zeroRISC Inc.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

"""Composed reporting helper for UVM objects."""

from __future__ import annotations

from typing import Any

from pyuvm.uvm_reporting.uvm_verbosity import (
    UVM_LOW,
    resolve_uvm_verbosity,
    uvm_reporter,
)


class uvm_base_core_report:
    """Owns logger, effective verbosity, and the bound UVM reporter."""

    def __init__(
        self,
        owner: Any,
        parent: Any | None = None,
        default_verbosity: int = UVM_LOW,
    ) -> None:
        self.owner = owner
        self.logger = getattr(owner, "logger")
        inherited = getattr(parent, "uvm_verbosity", default_verbosity)
        self.verbosity: int = int(inherited)
        self.uvm_report = uvm_reporter(self.logger, self.verbosity)

    def apply_cfg(self, cfg: Any | None = None) -> int:
        """Resolve effective verbosity with an optional cfg override."""
        self.verbosity = resolve_uvm_verbosity(self.verbosity, cfg)
        self.uvm_report.set_logger(self.logger)
        self.uvm_report.set_verbosity(self.verbosity)
        return self.verbosity

    def set_verbosity(self, verbosity: int) -> int:
        self.verbosity = int(verbosity)
        self.uvm_report.set_verbosity(self.verbosity)
        return self.verbosity

    def set_logger(self, logger: Any) -> None:
        self.logger = logger
        self.uvm_report.set_logger(logger)
