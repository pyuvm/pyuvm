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

class my_no_objection(uvm_test):
    async def run_phase(self):
        print("Running without using objections")

@cocotb.test()
async def run_test(dut):
    """Test basic run_phase operation with objection"""
    await uvm_root().run_test("my_test")
    assert True


@cocotb.test(expect_error=UVMError)
async def error(dut):
    """Test that raising exceptions creates cocotb errors"""
    await uvm_root().run_test("my_error")

@cocotb.test()
async def run_after_error(dut):
    """Test run_phase operation after previous test raised exception"""
    await uvm_root().run_test("my_test")
    assert True

@cocotb.test()
async def run_no_objection(dut):
    """Test using no objections, after a test that did use them"""
    # Expect a warning message. Can that be tested for?
    await uvm_root().run_test("my_no_objection")
