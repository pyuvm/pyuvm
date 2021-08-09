from cocotb.clock import Clock
import cocotb
import inspect
import test_config_db as test_mod


async def run_tests(dut):
    tests_pass = {}
    tcfgdb = test_mod.config_db_TestCase(dut.clk)
    methods = inspect.getmembers(test_mod.config_db_TestCase)#, predicate=inspect.ismethod)
    for mm in methods:
        (name,_) = mm
        if name.startswith("test_"):
            test = getattr(tcfgdb, name)
            tcfgdb.setUp()
            try:
                if inspect.iscoroutinefunction(test):
                    await test()
                else:
                    test()
                tests_pass[name] = True
            except AssertionError:
                tests_pass[name] = False
            tcfgdb.tearDown()
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
async def test_12_tlm(dut):
    """Tests the TLM FIFOS"""
    clock = Clock(dut.clk, 2, units="us")    
    cocotb.fork(clock.start())
    await run_tests(dut)




