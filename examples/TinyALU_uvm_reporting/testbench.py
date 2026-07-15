import random

# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it.
import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Combine

import pyuvm
from pyuvm import *

set_sv_uvm_style_reporting_enabled(True)

sys.path.append(str(Path("../TinyALU").resolve()))
from tinyalu_utils import Ops, TinyAluBfm, alu_prediction  # noqa: E402

# Sequence classes


class AluSeqItem(uvm_sequence_item):
    def __init__(self, name, aa, bb, op):
        super().__init__(name)
        self.A = aa
        self.B = bb
        self.op = Ops(op)

    def randomize_operands(self):
        self.A = random.randint(0, 255)
        self.B = random.randint(0, 255)

    def randomize(self):
        self.randomize_operands()
        self.op = random.choice(list(Ops))

    def __eq__(self, other):
        same = self.A == other.A and self.B == other.B and self.op == other.op
        return same

    __hash__: None  # type: ignore

    def __str__(self):
        return f"{self.get_name()} : A: 0x{self.A:02x} \
        OP: {self.op.name} ({self.op.value}) B: 0x{self.B:02x}"


class RandomSeq(uvm_sequence):
    async def body(self):
        for op in list(Ops):
            cmd_tr = AluSeqItem("cmd_tr", None, None, op)
            await self.start_item(cmd_tr)
            cmd_tr.randomize_operands()
            await self.finish_item(cmd_tr)


class MaxSeq(uvm_sequence):
    async def body(self):
        for op in list(Ops):
            cmd_tr = AluSeqItem("cmd_tr", 0xFF, 0xFF, op)
            await self.start_item(cmd_tr)
            await self.finish_item(cmd_tr)


class TestAllSeq(uvm_sequence):
    async def body(self):
        seqr = ConfigDB().get(None, "", "SEQR")
        random = RandomSeq("random")
        max = MaxSeq("max")
        await random.start(seqr)
        await max.start(seqr)


class TestAllForkSeq(uvm_sequence):
    async def body(self):
        seqr = ConfigDB().get(None, "", "SEQR")
        random = RandomSeq("random")
        max = MaxSeq("max")
        random_task = cocotb.start_soon(random.start(seqr))
        max_task = cocotb.start_soon(max.start(seqr))
        await Combine(random_task, max_task)


# Sequence library example


class OpSeq(uvm_sequence):
    def __init__(self, name, aa, bb, op):
        super().__init__(name)
        self.aa = aa
        self.bb = bb
        self.op = Ops(op)

    async def body(self):
        seq_item = AluSeqItem("seq_item", self.aa, self.bb, self.op)
        await self.start_item(seq_item)
        await self.finish_item(seq_item)
        self.result = seq_item.result


async def do_add(seqr, aa, bb):
    seq = OpSeq("seq", aa, bb, Ops.ADD)
    await seq.start(seqr)
    return seq.result


async def do_and(seqr, aa, bb):
    seq = OpSeq("seq", aa, bb, Ops.AND)
    await seq.start(seqr)
    return seq.result


async def do_xor(seqr, aa, bb):
    seq = OpSeq("seq", aa, bb, Ops.XOR)
    await seq.start(seqr)
    return seq.result


async def do_mul(seqr, aa, bb):
    seq = OpSeq("seq", aa, bb, Ops.MUL)
    await seq.start(seqr)
    return seq.result


class FibonacciSeq(uvm_sequence):
    def __init__(self, name):
        super().__init__(name)
        self.seqr = ConfigDB().get(None, "", "SEQR")

    async def body(self):
        prev_num = 0
        cur_num = 1
        fib_list = [prev_num, cur_num]
        for _ in range(7):
            sum = await do_add(self.seqr, prev_num, cur_num)
            fib_list.append(sum)
            prev_num = cur_num
            cur_num = sum
        self.uvm_report.info(
            self.get_name(), "Fibonacci Sequence: " + str(fib_list), UVM_LOW
        )


class Driver(uvm_driver):
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    def start_of_simulation_phase(self):
        self.bfm = TinyAluBfm()

    async def launch_tb(self):
        await self.bfm.reset()
        self.bfm.start_bfm()

    async def run_phase(self):
        await self.launch_tb()
        while True:
            cmd = await self.seq_item_port.get_next_item()
            await self.bfm.send_op(cmd.A, cmd.B, cmd.op)
            result = await self.bfm.get_result()
            self.ap.write(result)
            cmd.result = result
            self.seq_item_port.item_done()


class Coverage(uvm_subscriber):
    def end_of_elaboration_phase(self):
        self.cvg = set()

    def write(self, cmd):
        (_, _, op) = cmd
        self.cvg.add(op)

    def report_phase(self):
        try:
            disable_errors = ConfigDB().get(self, "", "DISABLE_COVERAGE_ERRORS")
        except UVMConfigItemNotFound:
            disable_errors = False
        if not disable_errors:
            if len(set(Ops) - self.cvg) > 0:
                self.uvm_report.error(
                    self.get_name(),
                    f"Functional coverage error. Missed: {set(Ops) - self.cvg}",
                )
            else:
                self.uvm_report.info(self.get_name(), "Covered all operations", UVM_LOW)


class Scoreboard(uvm_component):
    def build_phase(self):
        self.cmd_fifo = uvm_tlm_analysis_fifo("cmd_fifo", self)
        self.result_fifo = uvm_tlm_analysis_fifo("result_fifo", self)
        self.cmd_get_port = uvm_get_port("cmd_get_port", self)
        self.result_get_port = uvm_get_port("result_get_port", self)
        self.cmd_export = self.cmd_fifo.analysis_export
        self.result_export = self.result_fifo.analysis_export

    def connect_phase(self):
        self.cmd_get_port.connect(self.cmd_fifo.get_export)
        self.result_get_port.connect(self.result_fifo.get_export)

    def _quit_count_reached(self):
        report_server = uvm_report_server.get_or_none()
        return report_server is not None and report_server.error_quit_count_reached()

    def check_phase(self):
        try:
            self.errors = ConfigDB().get(self, "", "CREATE_ERRORS")
        except UVMConfigItemNotFound:
            self.errors = False
        try:
            self.fatals = ConfigDB().get(self, "", "CREATE_FATALS")
        except UVMConfigItemNotFound:
            self.fatals = False
        while self.result_get_port.can_get():
            _, actual_result = self.result_get_port.try_get()
            cmd_success, cmd = self.cmd_get_port.try_get()
            if not cmd_success:
                self.uvm_report.fatal(
                    self.get_name(), f"result {actual_result} had no command"
                )
            else:
                (A, B, op_numb) = cmd
                op = Ops(op_numb)
                predicted_result = alu_prediction(A, B, op, self.errors)
                if predicted_result == actual_result:
                    self.uvm_report.info(
                        self.get_name(),
                        f"PASSED: 0x{A:02x} {op.name} 0x{B:02x} = 0x{actual_result:04x}",
                        UVM_LOW,
                    )
                else:
                    mismatch_msg = (
                        f"FAILED: 0x{A:02x} {op.name} 0x{B:02x} "
                        f"= 0x{actual_result:04x} "
                        f"expected 0x{predicted_result:04x}"
                    )
                    if self.fatals:
                        self.uvm_report.fatal(self.get_name(), mismatch_msg)
                    else:
                        self.uvm_report.error(self.get_name(), mismatch_msg)
                    if self._quit_count_reached():
                        break


class Monitor(uvm_component):
    def __init__(self, name, parent, method_name):
        super().__init__(name, parent)
        self.method_name = method_name

    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)
        self.bfm = TinyAluBfm()
        self.get_method = getattr(self.bfm, self.method_name)

    async def run_phase(self):
        while True:
            datum = await self.get_method()
            self.uvm_report.info(self.get_name(), f"MONITORED {datum}", UVM_DEBUG)
            self.ap.write(datum)


class AluEnv(uvm_env):
    def build_phase(self):
        self.clk_drv = Clock(cocotb.top.clk, 2, "us")
        cocotb.start_soon(self.clk_drv.start())
        self.seqr = uvm_sequencer("seqr", self)
        ConfigDB().set(None, "*", "SEQR", self.seqr)
        self.driver = Driver.create("driver", self)
        self.cmd_mon = Monitor("cmd_mon", self, "get_cmd")
        self.coverage = Coverage("coverage", self)
        self.scoreboard = Scoreboard("scoreboard", self)

    def connect_phase(self):
        self.driver.seq_item_port.connect(self.seqr.seq_item_export)
        self.cmd_mon.ap.connect(self.scoreboard.cmd_export)
        self.cmd_mon.ap.connect(self.coverage.analysis_export)
        self.driver.ap.connect(self.scoreboard.result_export)


@pyuvm.test()
class AluTest(uvm_test):
    """Test ALU with random and max values"""

    def build_phase(self):
        self.env = AluEnv("env", self)

    def end_of_elaboration_phase(self):
        self.test_all = TestAllSeq.create("test_all")

    async def run_phase(self):
        self.raise_objection("Keep simulation alive")
        await self.test_all.start()
        self.drop_objection("Simulation may end now")

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
    """Test ALU random and max forked"""

    def build_phase(self):
        uvm_factory().set_type_override_by_type(TestAllSeq, TestAllForkSeq)
        super().build_phase()


@pyuvm.test()
class FibonacciTest(AluTest):
    """Run Fibonacci program"""

    def build_phase(self):
        ConfigDB().set(None, "*", "DISABLE_COVERAGE_ERRORS", True)
        uvm_factory().set_type_override_by_type(TestAllSeq, FibonacciSeq)
        return super().build_phase()


@pyuvm.test(expect_error=(AssertionError,))
class AluTestErrors(AluTest):
    """Test ALU with errors on all operations"""

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
