import cocotb
from pyuvm import *


class my_test(uvm_test):
    async def run_phase(self):
        self.raise_objection()
        print("Hey, I'm here")
        self.drop_objection()


class my_error(uvm_test):
    async def run_phase(self):
        self.raise_objection()
        raise UVMError("This is an error")


@cocotb.test()
async def run_test(dut):
    """Test the various nowait flavors"""
    await uvm_root().run_test("my_test")
    assert True


@cocotb.test(expect_error=True)
async def error(dut):
    """Test that raising exceptions creates cocotb errors"""
    await uvm_root().run_test("my_error")
