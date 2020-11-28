from pyuvm import *
import random
import logging
from enum import Enum, unique, auto

@unique
class ALUOps(Enum):
    ADD = auto()
    AND = auto()
    XOR = auto()
    MUL = auto()


class command_transaction(uvm_sequence_item):

    def __init__(self, name, A=0, B=0, op=ALUOps.ADD):
        super().__init__(name)
        self.A = A
        self.B = B
        self.op = op

    def __str__(self):
        return f"{self.A} {self.op} {self.B}"

class result_transaction(uvm_transaction):
    def __init__(self, name, r):
        super().__init__(name)
        self.result = r

    def __str__(self):
        return str(self.result)

    def __eq__(self, other):
        return self.result == other.result


# Driver
class driver(uvm_driver):

    def run_phase(self):
        self.bfm = self.config_db_get("DUT")
        while True:
            command = self.seq_item_port.get_next_item()
            self.bfm.send_op(command.A, command.B, command.op)
            self.seq_item_port.item_done()


class command_monitor(uvm_component):

        def build_phase(self, phase = None):
            self.ap = uvm_analysis_port("ap", self)

        def run_phase(self):
            self.monitor_bfm = self.config_db_get("DUT")
            while True:
                (A, B, op) = self.monitor_bfm.get_cmd()
                mon_tr = command_transaction("mon_tr", A, B, op)
                self.ap.write(mon_tr)


class result_monitor(uvm_component):

    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    def run_phase(self):
        self.result_mon = self.config_db_get("DUT")
        while True:
            result = self.result_mon.get_result()
            result_t = result_transaction("result", result)
            self.ap.write(result_t)


class scoreboard(uvm_subscriber):

    def build_phase(self):
        self.cmd_f = uvm_tlm_analysis_fifo("cmd_f", self)
        self.cmd_p =  uvm_get_port("cmd_p", self)

    def connect_phase(self):
        self.cmd_p.connect(self.cmd_f.get_export)

    @staticmethod
    def predict_result(cmd):
        result = None
        if cmd.op == ALUOps.ADD:
            result = cmd.A + cmd.B
        elif cmd.op == ALUOps.AND:
            result = cmd.A & cmd.B
        elif cmd.op == ALUOps.XOR:
            result = cmd.A ^ cmd.B
        elif cmd.op == ALUOps.MUL:
            result = cmd.A * cmd.B
        else:
            print(f"Got illegal operation {cmd.op}")
        return result_transaction("predicted", result)

    def write(self, result_t):
        success, cmd = self.cmd_p.try_get()
        if not success:
            raise error_classes.UVMFatalError(f"Got result: {result_t} with no cmd in queue")
        predicted_t = self.predict_result(cmd)
        if predicted_t != result_t:
            print(f"Avast! Bug here! {cmd} should make {predicted_t}, made {result_t}")
        else:
            print(f"Test passed: {cmd} = {result_t}")


class tinyalu_agent(uvm_agent):

    def build_phase(self):
        self.cm_h = command_monitor("cm_h",self)
        self.dr_h = driver("dr_h", self)
        self.seqr = uvm_sequencer("seqr", self)
        self.config_db_set(self.seqr, "SEQR", "*")

        # Make with the factory
        self.rm_h = self.create_component("result_monitor", "rm_h")
        self.sb_h = self.create_component("scoreboard", "sb")

        self.cmd_mon_ap = uvm_analysis_port("cmd_mon_ap", self)
        self.result_ap = uvm_analysis_port("result_ap", self)

    def connect_phase(self):
        self.cm_h.ap.connect(self.cmd_mon_ap)
        self.rm_h.ap.connect(self.result_ap)
        self.dr_h.seq_item_port.connect(self.seqr.seq_item_export)
        self.cm_h.ap.connect(self.sb_h.cmd_f.analysis_export)
        self.rm_h.ap.connect(self.sb_h)


class tinyalu_dut(uvm_component):
    """
    The DUT pretends to be some sort of TLM interface. It exposes
    function calls that deliver te operation and results to the
    associated monitors.
    send_op--Starts an operation
    get_op--Waits for an operation to be available and returns it
    get_result--Waits for a result to be available and returns it
    """

    def build_phase(self):
        # Use FIFOs to send data to ALU and
        # Monitors
        self.cmd_put_p = uvm_blocking_put_port("op_put_p", self)
        self.cmd_fifo = uvm_tlm_fifo("fifo", self)
        self.cmd_get_p = uvm_get_port("op_p", self)

        self.cmd_mon_put_p = uvm_blocking_put_port("op_mon_put_p", self)
        self.cmd_mon_fifo  = uvm_tlm_analysis_fifo("op_mon_fifo", self)
        self.cmd_mon_get_p = uvm_blocking_get_port("op_mon_get_p", self)

        self.result_mon_put_p = uvm_blocking_put_port("result_mon_put_p", self)
        self.result_mon_fifo  = uvm_tlm_analysis_fifo("result_mon_fifo", self)
        self.result_mon_get_p = uvm_blocking_get_port("result_mon_get_p", self)

        # Store the DUT where people can get it
        self.config_db_set(self, "DUT", "*")

    def connect_phase(self):
        self.cmd_get_p.connect(self.cmd_fifo.get_export)
        self.cmd_put_p.connect(self.cmd_fifo.put_export)

        self.cmd_mon_put_p.connect(self.cmd_mon_fifo.put_export)
        self.cmd_mon_get_p.connect(self.cmd_mon_fifo.get_export)

        self.result_mon_put_p.connect(self.result_mon_fifo.put_export)
        self.result_mon_get_p.connect(self.result_mon_fifo.get_export)

    def send_op(self, A, B, op):
        cmd_t = command_transaction("cmd_t", A, B, op)
        self.cmd_put_p.put(cmd_t)

    def get_cmd(self):
        cmd = self.cmd_mon_get_p.get()
        return cmd

    def get_result(self):
        result = self.result_mon_get_p.get()
        return result

    def run_phase(self):
        while True:
            cmd = self.cmd_get_p.get()
            self.cmd_mon_put_p.put((cmd.A, cmd.B, cmd.op))
            time.sleep(0.5)
            result = None
            if cmd.op == ALUOps.ADD:
                result = cmd.A + cmd.B
            elif cmd.op == ALUOps.AND:
                result = cmd.A & cmd.B
            elif cmd.op == ALUOps.XOR:
                result = cmd.A ^ cmd.B
            elif cmd.op == ALUOps.MUL:
                result = cmd.A * cmd.B
            self.result_mon_put_p.put(result)


class env(uvm_env):

    def build_phase(self):
        self.agent = tinyalu_agent("agent",self)

class alu_sequence(uvm_sequence):
    def body(self):
        cmd_tr = command_transaction("cmd_tr")
        for ii in range(10):
            self.start_item(cmd_tr)
            cmd_tr.A = random.randint(0,255)
            cmd_tr.B = random.randint(0,255)
            cmd_tr.op = random.choice(list(ALUOps))
            self.finish_item(cmd_tr)
        time.sleep(1) # give the last transaction time to go through



class alu_test(uvm_test):

    def build_phase(self):
        self.env = env("env", self)
        self.dut = tinyalu_dut("dut", self)

    def run_phase(self):
        self.raise_objection()
        seq = alu_sequence("seq")
        seqr = self.config_db_get("SEQR")
        seq.start(seqr)
        time.sleep(1)
        self.drop_objection()


if __name__ == '__main__':
    uvm_root().run_test("alu_test")

