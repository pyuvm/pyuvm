"""Tests for common-phase traversal directions.

IEEE 1800.2 section 9.8.1 fixes the traversal direction of each common phase.
Only build and final are top-down; every other common phase is bottom-up.
This guards against the regression where end_of_elaboration,
start_of_simulation, extract, check, and report were declared top-down.
"""

import pytest

from pyuvm import (
    uvm_bottomup_phase,
    uvm_build_phase,
    uvm_check_phase,
    uvm_connect_phase,
    uvm_end_of_elaboration_phase,
    uvm_extract_phase,
    uvm_final_phase,
    uvm_report_phase,
    uvm_run_phase,
    uvm_start_of_simulation_phase,
    uvm_topdown_phase,
)


@pytest.mark.parametrize(
    "phase",
    [uvm_build_phase, uvm_final_phase],
)
def test_topdown_phases(phase):
    """9.8.1 build and final are the only top-down common phases."""
    assert issubclass(phase, uvm_topdown_phase)
    assert not issubclass(phase, uvm_bottomup_phase)


@pytest.mark.parametrize(
    "phase",
    [
        uvm_connect_phase,
        uvm_end_of_elaboration_phase,
        uvm_start_of_simulation_phase,
        uvm_run_phase,
        uvm_extract_phase,
        uvm_check_phase,
        uvm_report_phase,
    ],
)
def test_bottomup_phases(phase):
    """
    9.8.1 connect, end_of_elaboration, start_of_simulation, run, extract,
    check, and report are all bottom-up. A hierarchical scoreboard that
    aggregates child results in extract/check/report relies on children
    running first, which only holds for bottom-up traversal.
    """
    assert issubclass(phase, uvm_bottomup_phase)
    assert not issubclass(phase, uvm_topdown_phase)
