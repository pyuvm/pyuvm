import importlib.util
import sys
from pathlib import Path

import pyuvm
from pyuvm import *

set_sv_uvm_style_reporting_enabled(True)

_TINYALU_DIR = Path(__file__).resolve().parents[1] / "TinyALU"
if str(_TINYALU_DIR) not in sys.path:
    sys.path.insert(0, str(_TINYALU_DIR))

_BASE_MODULE_NAME = "_pyuvm_tinyalu_base_testbench"
_BASE_MODULE_PATH = _TINYALU_DIR / "testbench.py"

if _BASE_MODULE_NAME in sys.modules:
    tinyalu_base = sys.modules[_BASE_MODULE_NAME]
else:
    _base_spec = importlib.util.spec_from_file_location(
        _BASE_MODULE_NAME, _BASE_MODULE_PATH
    )
    if _base_spec is None or _base_spec.loader is None:
        raise ImportError(f"Could not load TinyALU testbench from {_BASE_MODULE_PATH}")
    tinyalu_base = importlib.util.module_from_spec(_base_spec)
    sys.modules[_BASE_MODULE_NAME] = tinyalu_base
    _base_spec.loader.exec_module(tinyalu_base)


class ReportingFibonacciSeq(tinyalu_base.FibonacciSeq):
    def report_fibonacci_sequence(self, fib_list):
        self.uvm_report.info(
            self.get_name(), "Fibonacci Sequence: " + str(fib_list), UVM_LOW
        )


class ReportingCommandMonitor(tinyalu_base.CommandMonitor):
    def report_monitored(self, datum):
        self.uvm_report.info(self.get_name(), f"MONITORED {datum}", UVM_DEBUG)


class ReportingCoverage(tinyalu_base.Coverage):
    def report_coverage_error(self, missed):
        self.uvm_report.error(
            self.get_name(),
            f"Functional coverage error. Missed: {missed}",
        )

    def report_coverage_pass(self):
        self.uvm_report.info(self.get_name(), "Covered all operations", UVM_LOW)


class ReportingScoreboard(tinyalu_base.Scoreboard):
    def report_missing_command(self, actual_result):
        self.uvm_report.fatal(self.get_name(), f"result {actual_result} had no command")

    def report_pass(self, A, B, op, actual_result):
        self.uvm_report.info(
            self.get_name(),
            self.pass_message(A, B, op, actual_result),
            UVM_LOW,
        )

    def report_mismatch(self, A, B, op, actual_result, predicted_result):
        try:
            fatals = ConfigDB().get(self, "", "CREATE_FATALS")
        except UVMConfigItemNotFound:
            fatals = False

        mismatch_msg = self.mismatch_message(A, B, op, actual_result, predicted_result)
        if fatals:
            self.uvm_report.fatal(self.get_name(), mismatch_msg)
        else:
            self.uvm_report.error(self.get_name(), mismatch_msg)

    def quit_count_reached(self):
        report_server = uvm_report_server.get_or_none()
        return report_server is not None and report_server.error_quit_count_reached()

    def finish_check(self, passed):
        pass


@pyuvm.test()
class AluTest(tinyalu_base.AluTest):
    """Test ALU with random and max values using UVM-style reporting."""

    def build_phase(self):
        factory = uvm_factory()
        factory.set_type_override_by_type(
            tinyalu_base.CommandMonitor, ReportingCommandMonitor
        )
        factory.set_type_override_by_type(tinyalu_base.Coverage, ReportingCoverage)
        factory.set_type_override_by_type(tinyalu_base.Scoreboard, ReportingScoreboard)
        super().build_phase()

    def final_phase(self):
        report_server = getattr(self, "report_server", None)
        if report_server is None:
            return
        fail_msg = None
        try:
            report_server.log_summary(self.logger, self.get_full_name())
            fail_msg = report_server.log_final_status(
                self.logger,
                self.get_name(),
                uvm_full_name=self.get_full_name(),
            )
        finally:
            report_server.shutdown()
        if fail_msg is not None:
            raise AssertionError(fail_msg) from None


@pyuvm.test()
class ParallelTest(AluTest):
    """Test ALU random and max forked with UVM style reporting."""

    def build_phase(self):
        uvm_factory().set_type_override_by_type(
            tinyalu_base.TestAllSeq, tinyalu_base.TestAllForkSeq
        )
        super().build_phase()


@pyuvm.test()
class FibonacciTest(AluTest):
    """Run Fibonacci program with UVM style reporting."""

    def build_phase(self):
        ConfigDB().set(None, "*", "DISABLE_COVERAGE_ERRORS", True)
        uvm_factory().set_type_override_by_type(
            tinyalu_base.TestAllSeq, ReportingFibonacciSeq
        )
        return super().build_phase()


@pyuvm.test(expect_error=(AssertionError,))
class AluTestErrors(AluTest):
    """Test ALU with errors on all operations with UVM style reporting."""

    def start_of_simulation_phase(self):
        ConfigDB().set(None, "*", "CREATE_ERRORS", True)


@pyuvm.test(expect_error=(RuntimeError,))
class FatalReportTest(AluTest):
    """Report a real ALU mismatch through self.uvm_report.fatal."""

    def start_of_simulation_phase(self):
        ConfigDB().set(None, "*", "CREATE_ERRORS", True)
        ConfigDB().set(None, "*", "CREATE_FATALS", True)


@pyuvm.test(expect_error=(AssertionError,))
class FatalDowngradeToErrorTest(AluTest):
    """Report a real fatal mismatch after downgrading it to UVM_ERROR."""

    def add_message_demotes(self, catcher):
        super().add_message_demotes(catcher)
        catcher.add_change_sev("scoreboard", "FAILED:", UVM_ERROR)

    def start_of_simulation_phase(self):
        ConfigDB().set(None, "*", "CREATE_ERRORS", True)
        ConfigDB().set(None, "*", "CREATE_FATALS", True)


@pyuvm.test()
class FatalDowngradeToInfoTest(AluTest):
    """Report real fatal mismatches after downgrading them to UVM_INFO."""

    def add_message_demotes(self, catcher):
        super().add_message_demotes(catcher)
        catcher.add_change_sev("scoreboard", "FAILED:", UVM_INFO)

    def start_of_simulation_phase(self):
        ConfigDB().set(None, "*", "CREATE_ERRORS", True)
        ConfigDB().set(None, "*", "CREATE_FATALS", True)


@pyuvm.test()
class ErrorDowngradeToInfoTest(AluTest):
    """Report real error mismatches after downgrading them to UVM_INFO."""

    def add_message_demotes(self, catcher):
        super().add_message_demotes(catcher)
        catcher.add_change_sev("scoreboard", "FAILED:", UVM_INFO)

    def start_of_simulation_phase(self):
        ConfigDB().set(None, "*", "CREATE_ERRORS", True)
