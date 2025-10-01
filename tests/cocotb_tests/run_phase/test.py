import cocotb
from cocotb.triggers import Timer
from cocotb.utils import get_sim_time

from pyuvm import *


class my_test(uvm_test):
    async def run_phase(self):
        self.raise_objection()
        self.drop_objection()


class my_error(uvm_test):
    async def run_phase(self):
        self.raise_objection()
        raise UVMError("This is an error")


class my_no_objection(uvm_test):
    async def run_phase(self):
        print("Running without using objections")


class nested_parent(uvm_test):
    async def run_phase(self):
        self.raise_objection()
        await Timer(1, "ms")
        self.drop_objection()


class nested_objections(nested_parent):
    async def run_phase(self):
        self.raise_objection()
        await super().run_phase()
        await Timer(10, "ms")
        self.drop_objection()

    def check_phase(self):
        assert get_sim_time("ms") > 10


class TopTest(uvm_test):
    def build_phase(self):
        # super().build_phase()
        self.sub_component = SubComponent("sub_component", self)

    async def run_phase(self):
        self.raise_objection()
        await Timer(10, "ms")
        self.drop_objection()


class SubComponent(uvm_component):
    def __init__(self, name, parent):
        super().__init__(name, parent)

    async def run_phase(self):
        self.raise_objection()

        # sub component takes longer than TopTest
        await Timer(50, "ms")

        self.drop_objection()

    def check_phase(self):
        assert get_sim_time("ms") >= 50


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


@cocotb.test()
async def test_nested_objections(_):
    await uvm_root().run_test(nested_objections)


@cocotb.test()
async def test_sub_component_objections(_):
    """
    Test that all objections from all components are waited for
    regardless of the order in which they are raised or dropped.
    """
    await uvm_root().run_test(TopTest)
