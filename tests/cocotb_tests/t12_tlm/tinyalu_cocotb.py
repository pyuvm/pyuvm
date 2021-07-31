from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
import cocotb
import pyuvm.utility_classes as utility_classes
import time
import asyncio.queues
import inspect
import test_12_uvm_tlm_interfaces as test_mod


@cocotb.test() # pylint: disable=no-value-for-parameter
async def test_12_tlm(dut):
    """Tests the TLM FIFOS"""
    t12 = test_mod.s12_uvm_tlm_interfaces_TestCase()
    methods = inspect.getmembers(test_mod.s12_uvm_tlm_interfaces_TestCase)#, predicate=inspect.ismethod)
    for mm in methods:
        (name,_) = mm
        if name.startswith("test_"):
            print(name)
            test = getattr(t12, name)
            t12.setUp()
            if inspect.iscoroutinefunction(test):
                await test()
            else:
                test()
            t12.tearDown()
    assert True


