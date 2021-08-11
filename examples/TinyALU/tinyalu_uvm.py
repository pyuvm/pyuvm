from pyuvm import *
from cocotb.triggers import ClockCycles
import enum
import random


@enum.unique
class Ops(enum.IntEnum):
    """Legal ops for the TinyALU"""
    ADD = 1
    AND = 2
    XOR = 3
    MUL = 4


def alu_prediction(A, B, op):
    result = None  # Make the linter happy
    assert op in list(Ops), "The tinyalu op must be of type ops"
    if op == Ops.ADD:
        result = A + B
    elif op == Ops.AND:
        result = A & B
    elif op == Ops.XOR:
        result = A ^ B
    elif op == Ops.MUL:
        result = A * B
    return result


class AluSeqItem(uvm_sequence_item):

    def __init__(self, name, aa=0, bb=0, op=Ops.ADD):
        super().__init__(name)
        self.A = aa
        self.B = bb
        self.op = Ops(op)

    def __eq__(self, other):
        same = self.A == other.A and self.B == other.B and self.op == other.op
        return same

    def __str__(self):
        return f"{self.get_name()} : A: 0x{self.A:02x} "
        f"OP: {self.op.name} ({self.op.value}) B: 0x{self.B:02x}"

    def randomize(self):
        self.A = random.randint(0, 255)
        self.B = random.randint(0, 255)
        self.op = random.choice(list(Ops))


class AluSeq(uvm_sequence):
    async def body(self):
        for op in list(Ops):
            cmd_tr = AluSeqItem("cmd_tr")
            await self.start_item(cmd_tr)
            cmd_tr.randomize()
            cmd_tr.op = op
            await self.finish_item(cmd_tr)


class Driver(uvm_driver):
    def connect_phase(self):
        self.proxy = self.cdb_get("PROXY")

    async def run_phase(self):
        while True:
            command = await self.seq_item_port.get_next_item()
            await self.proxy.send_op(command.A, command.B, command.op)
            self.logger.debug(f"Sent command: {command}")
            self.seq_item_port.item_done()


class Coverage(uvm_subscriber):

    def end_of_elaboration_phase(self):
        self.cvg = set()

    def write(self, cmd):
        (_, _, op) = cmd
        self.cvg.add(op)

    def check_phase(self):
        if len(set(Ops) - self.cvg) > 0:
            self.logger.error(f"Functional coverage error. "
                              f"Missed: {set(Ops)-self.cvg}")


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

    def check_phase(self):
        while self.result_get_port.can_get():
            _, actual_result = self.result_get_port.try_get()
            cmd_success, cmd = self.cmd_get_port.try_get()
            if not cmd_success:
                self.logger.critical(f"result {actual_result} had no command")
            else:
                (A, B, op_numb) = cmd
                op = Ops(op_numb)
                predicted_result = alu_prediction(A, B, op)
                if predicted_result == actual_result:
                    self.logger.info(f"PASSED: 0x{A:02x} {op.name} 0x{B:02x} ="
                                     f" 0x{actual_result:04x}")
                else:
                    self.logger.error(f"FAILED: 0x{A:02x} {op.name} 0x{B:02x} "
                                      f"= 0x{actual_result:04x} "
                                      f"expected 0x{predicted_result:04x}")


class Monitor(uvm_component):
    def __init__(self, name, parent, method_name):
        super().__init__(name, parent)
        self.method_name = method_name

    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    def connect_phase(self):
        self.proxy = self.cdb_get("PROXY")

    async def run_phase(self):
        while True:
            get_method = getattr(self.proxy, self.method_name)
            datum = await get_method()
            self.ap.write(datum)


class AluEnv(uvm_env):

    def build_phase(self):
        self.cmd_mon = Monitor("cmd_mon", self, "get_cmd")
        self.result_mon = Monitor("result_mon", self, "get_result")
        self.scoreboard = Scoreboard("scoreboard", self)
        self.coverage = Coverage("coverage", self)
        self.driver = Driver("driver", self)
        self.seqr = uvm_sequencer("seqr", self)
        ConfigDB().set(None, "*", "SEQR", self.seqr)

    def connect_phase(self):
        self.cmd_mon.ap.connect(self.scoreboard.cmd_export)
        self.cmd_mon.ap.connect(self.coverage)
        self.result_mon.ap.connect(self.scoreboard.result_export)
        self.driver.seq_item_port.connect(self.seqr.seq_item_export)


class AluTest(uvm_test):
    def build_phase(self):
        self.env = AluEnv.create("env", self)

    async def run_phase(self):
        self.raise_objection()
        seqr = ConfigDB().get(self, "", "SEQR")
        dut = ConfigDB().get(self, "", "DUT")
        seq = AluSeq("seq")
        await seq.start(seqr)
        await ClockCycles(dut.clk, 50)  # to do last transaction
        self.drop_objection()

    def end_of_elaboration_phase(self):
        self.set_logging_level_hier(logging.DEBUG)
