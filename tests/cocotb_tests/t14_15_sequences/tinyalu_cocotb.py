from test_14_15_python_sequences import DataHolder
from pyuvm.s13_uvm_component import ConfigDB
from cocotb.clock import Clock
import cocotb
import inspect
import test_14_15_python_sequences as test_mod
"""
import debugpy

listen_host, listen_port = debugpy.listen(("localhost", 5678))
cocotb.log.info("Waiting for Python debugger attach on {}:{}".format(listen_host, listen_port))
# Suspend execution until debugger attaches
debugpy.wait_for_client()
# Break into debugger for user control
breakpoint()  # or debugpy.breakpoint() on 3.6 and below
"""

async def run_tests(dut):
    tests_pass = {}
    t14 = test_mod.py1415_sequence_TestCase()
    methods = inspect.getmembers(test_mod.py1415_sequence_TestCase)#, predicate=inspect.ismethod)
    for mm in methods:
        (name,_) = mm
        if name.startswith("test_"):
            test = getattr(t14, name)
            t14.setUp()
            try:
                if inspect.iscoroutinefunction(test):
                    await test()
                else:
                    test()
                tests_pass[name] = True
            except (AssertionError , RuntimeWarning) as doh:
                tests_pass[name] = False
                print("ERROR", doh)
            t14.tearDown()
    any_failed = False
    for test in tests_pass:
        if tests_pass[test]:
            pf = "Pass   "
        else:
            pf = "FAILED "
            any_failed = True
        print (f"{pf}{test:<20}")
    assert not any_failed

@cocotb.test() # pylint: disable=no-value-for-parameter
async def test_14_sequences(dut):
    """Tests the Sequences"""
    DataHolder.clock = dut.clk
    ConfigDB().set(None, "*", "UVM_RTL_CLOCK", dut.clk)

    await run_tests(dut)




