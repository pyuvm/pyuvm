import cocotb
from pyuvm import *

class my_test(uvm_test):
    async def run_phase(self):
        self.raise_objection()
        print("Hey, I'm here")
        self.drop_objection()

@cocotb.test()
async def run_test(dut):
    """Test the various nowait flavors"""
    await uvm_root().run_test("my_test")
    assert True







