from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
import cocotb
import pyuvm.utility_classes as utility_classes
import time
import asyncio.queues
import inspect
import test_12_uvm_tlm_interfaces as test_mod


async def run_tlm(dut):
    tests_pass = {}
    t12 = test_mod.s12_uvm_tlm_interfaces_TestCase()
    methods = inspect.getmembers(test_mod.s12_uvm_tlm_interfaces_TestCase)#, predicate=inspect.ismethod)
    for mm in methods:
        (name,_) = mm
        if name.startswith("test_"):
            test = getattr(t12, name)
            t12.setUp()
            try:
                if inspect.iscoroutinefunction(test):
                    await test()
                else:
                    test()
                tests_pass[name] = True
            except AssertionError:
                tests_pass[name] = False
            t12.tearDown()
    any_failed = False
    for test in tests_pass:
        if tests_pass[test]:
            pf = "Pass"
        else:
            pf = "FAILED"
            any_failed = True
        print (f"{test:<20} {pf} . . . ")
    assert not any_failed

@cocotb.test() # pylint: disable=no-value-for-parameter
async def test_12_tlm(dut):
    """Tests the TLM FIFOS"""
    await run_tlm(dut)




