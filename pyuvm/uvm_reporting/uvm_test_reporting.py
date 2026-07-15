# Copyright zeroRISC Inc.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

"""Automatic SV-UVM-style reporting setup for ``uvm_test``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pyuvm.uvm_reporting import get_sv_uvm_style_reporting_enabled
from pyuvm.uvm_reporting.uvm_report_server import (
    uvm_report_policy,
    uvm_report_server,
)
from pyuvm.uvm_reporting.uvm_runtime_options import (
    get_runtime_bool,
    get_runtime_int,
    get_runtime_option,
)
from pyuvm.uvm_reporting.uvm_verbosity import UVM_LOW, parse_uvm_verbosity


@dataclass(frozen=True)
class uvm_test_reporting_config:
    """Runtime reporting configuration resolved for a ``uvm_test``."""

    verbosity: int
    policy: uvm_report_policy
    print_char_len: int


def get_uvm_test_reporting_config() -> uvm_test_reporting_config:
    """Resolve report-server configuration from plusargs, env vars, defaults."""
    verbosity = parse_uvm_verbosity(
        get_runtime_option("UVM_VERBOSITY", None), UVM_LOW
    )
    policy = uvm_report_policy(
        fail_on_warning=get_runtime_bool("UVM_FAIL_ON_WARNING", False),
        fail_on_error=get_runtime_bool("UVM_FAIL_ON_ERROR", True),
        fail_on_fatal=get_runtime_bool("UVM_FAIL_ON_FATAL", True),
        max_quit_count=get_runtime_int(
            ("max_quit_count", "MAX_QUIT_COUNT", "UVM_MAX_QUIT_COUNT"), 1
        ),
        test_status_label=str(
            get_runtime_option(
                ("test_status_label", "TEST_STATUS_LABEL"), "TEST_STATUS"
            )
        ),
    )
    return uvm_test_reporting_config(
        verbosity=verbosity,
        policy=policy,
        print_char_len=get_runtime_int(
            ("print_char_len", "PRINT_CHAR_LEN", "UVM_PRINT_CHAR_LEN"), 300
        ),
    )


def configure_uvm_test_reporting(test_obj: Any) -> uvm_report_server | None:
    """Create and configure the shared report server for an opted-in test."""
    if not get_sv_uvm_style_reporting_enabled():
        return None

    config = get_uvm_test_reporting_config()
    manager = uvm_report_server.create(
        root_logger=test_obj.logger,
        verbosity=config.verbosity,
        policy=config.policy,
        print_char_len=config.print_char_len,
    )
    test_obj.set_report_verbosity(config.verbosity)
    manager.register_logger(test_obj.logger, test_obj.get_full_name())
    test_obj.add_message_demotes(manager.catcher)
    return manager
