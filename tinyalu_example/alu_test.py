from pyuvm import *
import pytlm
from enum import Enum
import random

@unique
class ALUOps(Enum):
    ADD = auto()
    AND = auto()
    XOR = auto()
    MUL = auto()

# Command Transaction
class command_transaction(uvm_sequence_item):
    def __init__(self, name, A, B, op):
        super().__init__(name)
        self.A = A
        self.B = B
        self.op = op

class result_transaction(uvm_transaction):
    def __init__(self, name, r):
        super().__init__()
        self.result = r


# Driver
class tinyalu_driver(uvm_driver):

    def build_phase(self, phase = None):
        self.bfm = pytlm.Proxy("xrtl_top.tinyalu_bfm")
        self.command_port = uvm_get_port("command_port", self)

    def run_phase(self, phase = None):
        while True:
            command = self.command_port.get()
            self.bfm.send_op(command.A, command.B, command.op)
            self.bfm.wait_for()
# Monitor
class command_monitor(test_comp):

        def build_phase(self, phase = None):
            self.ap = uvm_analysis_port("ap")
            self.monitor_bfm = pytlm.MonitorProxy("xrtl_top.tinyalu_monitor", self)

        def run_phase(self):
            while True:
                (A, B, op) = self.monitor_bfm.wait_for()
                mon_tr = command_transaction(A, B, op)
                self.ap.write(mon_tr)

# Result Monitor
class result_monitor(test_comp):

    def build_phase(self):
        self.ap = uvm_analysis_port("ap")
        self.bfm = pytlm.MonitorProxy("xrtl_top.result_monitor", self)

    def run_phase(self):
        while True:
            result = self.bfm.wait_for()
            result_t = result_transaction(result)
            self.ap.write(result_t)

# Scoreboard
class scoreboard(uvm_subscriber):

    def build_phase(self,phase=None):
        self.cmd_f = uvm_tlm_analysis_fifo("cmd_f", self)

    def write(self, result_transaction):
        cmd = self.cmd_f.get()
        pred_r = predict_result(cmd_f)
        if pred_r != result_transaction:
            self.logger.error(f"Avast! Bug here! {cmd} should make {pred_r}, made {result_transaction}")

class tinyalu_agent(uvm_agent):

    def build_phase(self,phase):
        self.cm_h = command_monitor("cm_h",self)
        self.dr_h = tinyalu_driver("dr_h",self)
        self.seqr = uvm_sequencer("seqr", self)

        # Fifos
        self.cmd_f = uvm_tlm_fifo("cmd_f",self)
        self.rslt_f= uvm_tlm_fifo("rslt_f",self)
        # Make with the factory
        self.rm_h = result_monitor.create("rm_h",self)
        self.sb = scoreboard.create("sb",self)

        self.cmd_mon_ap = uvm_analysis_port("cmd_mon_ap", self)
        self.result_ap = uvm_analysis_port("result_ap", self)

    def connect_phase(self, phase=None):
        self.dr_h.command_port.connect(self.cmd_f.get_export)
        self.rm_h.ap.connect(self.cmd_f.put_export)
        self.cm_h.ap.connect(self.cmd_mon_ap)
        self.rm_h.ap.connect(self.result_ap)

        self.dr_h.command_port(self.cmd_f.get_export)
        self.dr_h.sequence_item_port(self.seqr.seq_item_export)

class env(uvm_env):

    def build_phase(self,phase=None):
        self.agent = tinyalu_agent("agent",self)

class uvm_sequence:...
class alu_sequence(uvm_sequence):
    def body(self):
        A = random.randint(0,255)
        B = random.randint(0,255)
        op = random.choice(ALUOps)
        cmd_tr = command_transaction(A, B, op)
        self.start_item(cmd_tr)
        self.finish_item(cmd_tr)





class test_top(uvm_test):

    def build_phase(self,phase=None):
        self.env = env("env",self)

    def run_phase(self,phase=None):
        myseq = alu_sequence("myseq")
        self.env.agent.se


