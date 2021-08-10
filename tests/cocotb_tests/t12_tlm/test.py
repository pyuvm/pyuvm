from cocotb.clock import Clock
import cocotb
import inspect
import test_12_uvm_tlm_interfaces as test_mod


async def run_tests(dut):
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
            pf = "Pass   "
        else:
            pf = "FAILED "
            any_failed = True
        print (f"{pf} {test}")
    assert not any_failed

@cocotb.test() # pylint: disable=no-value-for-parameter
async def test_12_tlm(dut):
    """Tests the TLM FIFOS"""
    await run_tests(dut)




