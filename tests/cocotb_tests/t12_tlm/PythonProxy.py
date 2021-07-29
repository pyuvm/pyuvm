#!/usr/bin/env python
# coding: utf-8

# In[ ]:


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


class PythonProxy(uvm_component):
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

    def send_op(self, A, B, op):
        self.stim_put.put((A, B, op))
    
    def get_cmd(self):
        cmd  = self.cmd_get.get()
        return cmd
    
    def get_result(self):
        result = self.result_get.get()
        return result        
        
    def run_phase(self):
        while not ObjectionHandler().run_phase_complete():
            (A, B, op) = self.stim_get.get()
            result = self.alu_op(A, B, op)
            self.cmd_put.put((A, B, op))
            self.result_put.put(result)
            

