import random
import sys
from pathlib import Path

import cocotb
from cocotb.triggers import Timer

import pyuvm
from pyuvm import *

sys.path.append(str(Path("..").resolve()))
from aoi_2_2_utils import aoi_prediction  # noqa: E402


# Sequence Item
class AoiSeqItem(uvm_sequence_item):
    def __init__(self, name, a=0, b=0, c=0, d=0):
        super().__init__(name)
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.result = None

    def randomize(self):
        """Randomize all inputs"""
        self.a = random.randint(0, 1)
        self.b = random.randint(0, 1)
        self.c = random.randint(0, 1)
        self.d = random.randint(0, 1)

    def __eq__(self, other):
        return (
            self.a == other.a
            and self.b == other.b
            and self.c == other.c
            and self.d == other.d
        )

    __hash__ = None  # type: ignore

    def __str__(self):
        return f"{self.get_name()}: A={self.a} B={self.b} C={self.c} D={self.d} -> Y={self.result}"


# Sequences
class RandomSeq(uvm_sequence):
    """Generate random input combinations"""

    async def body(self):
        for _ in range(20):  # 20 random tests
            item = AoiSeqItem("random_item")
            await self.start_item(item)
            item.randomize()
            await self.finish_item(item)


class ExhaustiveSeq(uvm_sequence):
    """Test all 16 possible input combinations"""

    async def body(self):
        for a in range(2):
            for b in range(2):
                for c in range(2):
                    for d in range(2):
                        item = AoiSeqItem("exhaustive_item", a, b, c, d)
                        await self.start_item(item)
                        await self.finish_item(item)


class CornerCaseSeq(uvm_sequence):
    """Test important corner cases"""

    async def body(self):
        # Test cases: (a, b, c, d)
        test_cases = [
            (0, 0, 0, 0),  # All zeros -> Y=1
            (1, 1, 1, 1),  # All ones -> Y=0
            (1, 1, 0, 0),  # First AND true -> Y=0
            (0, 0, 1, 1),  # Second AND true -> Y=0
            (1, 0, 0, 0),  # Only first input -> Y=1
            (0, 0, 0, 1),  # Only last input -> Y=1
            (1, 0, 1, 0),  # Alternating pattern -> Y=1
            (0, 1, 0, 1),  # Alternating pattern -> Y=1
        ]

        for a, b, c, d in test_cases:
            item = AoiSeqItem("corner_item", a, b, c, d)
            await self.start_item(item)
            await self.finish_item(item)


class TestAllSeq(uvm_sequence):
    """Run all test sequences"""

    async def body(self):
        seqr = ConfigDB().get(None, "", "SEQR")

        # Run exhaustive test first
        exhaustive = ExhaustiveSeq("exhaustive")
        await exhaustive.start(seqr)

        # Then random tests
        random_seq = RandomSeq("random")
        await random_seq.start(seqr)


# Driver - simplified for combinational logic
class Driver(uvm_driver):
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)
        self.dut = cocotb.top

    async def run_phase(self):
        while True:
            item = await self.seq_item_port.get_next_item()

            # Apply inputs to DUT
            swt_value = (item.d << 3) | (item.c << 2) | (item.b << 1) | item.a
            self.dut.SWT.value = swt_value

            # Wait for combinational logic to settle
            await Timer(2, unit="ns")

            # Read result from 7-segment display
            seg_value = int(self.dut.SEG.value)

            # Decode 7-segment to get Y value
            if seg_value in {64, 64}:
                result = 0
            elif seg_value in {121, 121}:
                result = 1
            else:
                self.logger.warning(f"Unexpected SEG value: 0x{seg_value:02x}")
                result = 0

            item.result = result

            # Send to analysis port (for scoreboard and coverage)
            cmd = (item.a, item.b, item.c, item.d, result)
            self.ap.write(cmd)

            self.seq_item_port.item_done()


# Coverage
class Coverage(uvm_subscriber):
    def end_of_elaboration_phase(self):
        self.cvg = set()

    def write(self, cmd):
        """Track coverage of all 16 input combinations"""
        (a, b, c, d, _) = cmd
        self.cvg.add((a, b, c, d))

    def report_phase(self):
        try:
            disable_errors = ConfigDB().get(self, "", "DISABLE_COVERAGE_ERRORS")
        except UVMConfigItemNotFound:
            disable_errors = False

        total_combinations = 16  # 2^4 possible inputs
        covered = len(self.cvg)
        coverage_percent = (covered / total_combinations) * 100

        self.logger.info(
            f"Coverage: {covered}/{total_combinations} combinations ({coverage_percent:.1f}%)"
        )

        if not disable_errors and covered < total_combinations:
            missing = []
            for a in range(2):
                for b in range(2):
                    for c in range(2):
                        for d in range(2):
                            if (a, b, c, d) not in self.cvg:
                                missing.append((a, b, c, d))
            self.logger.error(f"Coverage incomplete. Missing: {missing}")
            assert False
        else:
            self.logger.info("All input combinations covered!")
            assert True


# Scoreboard
class Scoreboard(uvm_component):
    def build_phase(self):
        self.cmd_fifo = uvm_tlm_analysis_fifo("cmd_fifo", self)
        self.cmd_get_port = uvm_get_port("cmd_get_port", self)
        self.cmd_export = self.cmd_fifo.analysis_export

    def connect_phase(self):
        self.cmd_get_port.connect(self.cmd_fifo.get_export)

    def check_phase(self):
        passed = True
        try:
            self.errors = ConfigDB().get(self, "", "CREATE_ERRORS")
        except UVMConfigItemNotFound:
            self.errors = False

        while self.cmd_get_port.can_get():
            _, cmd = self.cmd_get_port.try_get()
            (a, b, c, d, actual_result) = cmd

            predicted_result = aoi_prediction(a, b, c, d, self.errors)

            if predicted_result == actual_result:
                self.logger.info(
                    f"PASSED: A={a} B={b} C={c} D={d} -> Y={actual_result} "
                    f"[AB={a & b}, CD={c & d}, (AB|CD)={(a & b) | (c & d)}]"
                )
            else:
                self.logger.error(
                    f"FAILED: A={a} B={b} C={c} D={d} -> Y={actual_result} "
                    f"expected Y={predicted_result}"
                )
                passed = False

        assert passed


# Environment
class AoiEnv(uvm_env):
    def build_phase(self):
        self.seqr = uvm_sequencer("seqr", self)
        ConfigDB().set(None, "*", "SEQR", self.seqr)
        self.driver = Driver.create("driver", self)
        self.coverage = Coverage("coverage", self)
        self.scoreboard = Scoreboard("scoreboard", self)

    def connect_phase(self):
        self.driver.seq_item_port.connect(self.seqr.seq_item_export)
        self.driver.ap.connect(self.scoreboard.cmd_export)
        self.driver.ap.connect(self.coverage.analysis_export)


# Tests
@pyuvm.test()
class AoiTest(uvm_test):
    """Test AOI module with exhaustive and random patterns"""

    def build_phase(self):
        self.env = AoiEnv("env", self)

    def end_of_elaboration_phase(self):
        self.test_all = TestAllSeq.create("test_all")

    async def run_phase(self):
        self.raise_objection()
        await self.test_all.start()
        self.drop_objection()


@pyuvm.test()
class AoiExhaustiveTest(uvm_test):
    """Test all 16 input combinations"""

    def build_phase(self):
        self.env = AoiEnv("env", self)

    async def run_phase(self):
        self.raise_objection()
        seqr = ConfigDB().get(None, "", "SEQR")
        seq = ExhaustiveSeq("exhaustive")
        await seq.start(seqr)
        self.drop_objection()


@pyuvm.test()
class AoiCornerTest(uvm_test):
    """Test corner cases"""

    def build_phase(self):
        ConfigDB().set(None, "*", "DISABLE_COVERAGE_ERRORS", True)
        self.env = AoiEnv("env", self)

    async def run_phase(self):
        self.raise_objection()
        seqr = ConfigDB().get(None, "", "SEQR")
        seq = CornerCaseSeq("corner")
        await seq.start(seqr)
        self.drop_objection()


@pyuvm.test(expect_fail=True)
class AoiTestErrors(AoiTest):
    """Test AOI with intentional errors"""

    def start_of_simulation_phase(self):
        ConfigDB().set(None, "*", "CREATE_ERRORS", True)
