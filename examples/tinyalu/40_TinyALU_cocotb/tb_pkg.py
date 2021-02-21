import enum
from pyuvm import *
import random

@enum.unique
class Ops(enum.IntEnum):
    """Legal ops for the TinyALU"""
    ADD = 1
    AND = 2
    XOR = 3
    MUL = 4

class AluCommand(uvm_transaction):

    def __init__(self, name, A=0, B=0, op=Ops.ADD):
        super().__init__(name)
        self.A = A
        self.B = B
        self.op = Ops(op)

    def __eq__(self, other):
        same = self.A == other.A \
               and self.B == other.B \
               and self.op == other.op
        return same

    def __str__(self):
        return f"{self.get_name()} : A: 0x{self.A:02x} OP: {self.op.name} ({self.op.value}) B: 0x{self.B:02x}"
    
    def randomize(self):
        self.A = random.randint(0,255)
        self.B = random.randint(0,255)
        self.op = random.choice(list(Ops))

class AluResult(uvm_transaction):
    def __init__(self, name, r):
        super().__init__(name)
        self.result = r

    def __str__(self):
        return f"{self.get_name()}: 0x{self.result:04x}"

    def __eq__(self, other):
        return self.result == other.result


class PythonProxy(uvm_component):
    def __init__(self, name, parent, label):
        super().__init__(name, parent)
        ConfigDB().set(None, "*", label, self)
    @staticmethod
    def alu_op(A, B, op):
        result = None # Make the linter happy
        assert op in list(Ops), "The tinyalu op must be of type ops"
        if op == Ops.ADD:
            result = A + B
        elif op == Ops.AND:
            result = A & B
        elif op == Ops.XOR:
            result = A ^ B
        elif op == Ops.MUL:
            result = A * B
        time.sleep(0.1)  # Takes time as a simulation would.
        return result
    
    def build_phase(self):
        # The FIFOs
        self.stim_f = uvm_tlm_fifo("stim_f", self)
        self.cmd_f = uvm_tlm_analysis_fifo("cmd_f", self)
        self.result_f = uvm_tlm_analysis_fifo("result_f", self)
        ConfigDB().set(None, "*", "PROXY", self)
        
        # The Stimulus Ports (for send_op())
        self.stim_put = uvm_put_port("stim_put", self)
        self.stim_get = uvm_get_port("stim_get", self)
        
        # The Command Ports (for get_cmd())
        self.cmd_put = uvm_put_port("cmd_put", self)
        self.cmd_get = uvm_get_port("cmd_get", self)
       
        # The Result Ports (for get_result())
        self.result_put = uvm_put_port("result_put",self)
        self.result_get = uvm_get_port("result_get", self)

    def connect_phase(self):
        self.stim_put.connect(self.stim_f.put_export)
        self.stim_get.connect(self.stim_f.get_export)
        
        self.cmd_put.connect(self.cmd_f.put_export)
        self.cmd_get.connect(self.cmd_f.get_export)
        
        self.result_put.connect(self.result_f.put_export)
        self.result_get.connect(self.result_f.get_export)

    def send_op(self, aa, bb, op):
        self.stim_put.put((aa, bb, op))
    
    def get_cmd(self):
        cmd  = self.cmd_get.get()
        return cmd
    
    def get_result(self):
        result = self.result_get.get()
        return result        
        
    def run_phase(self):
        while True:
            (aa, bb, op) = self.stim_get.get()
            result = self.alu_op(aa, bb, op)
            self.cmd_put.put((aa, bb, op))
            self.result_put.put(result)
            
