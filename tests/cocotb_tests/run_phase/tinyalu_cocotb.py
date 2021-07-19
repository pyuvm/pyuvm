from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
import cocotb
from tinyalu_uvm import *
import pyuvm.utility_classes as utility_classes
import time
import asyncio.queues
from pyuvm import *

class my_test(uvm_test):
    async def run_phase(self):
        print("Hey, I'm here")

@cocotb.test()
async def run_test(dut):
    """Test the various nowait flavors"""
    await uvm_root().run_test("my_test")
    assert True







