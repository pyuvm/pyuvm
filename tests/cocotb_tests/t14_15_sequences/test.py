from cocotb.clock import Clock
import cocotb
import inspect
import test_14_15_python_sequences as test_mod


async def run_tests(dut):
    tests_pass = {}
    t14 = test_mod.py1415_sequence_TestCase()
    methods = inspect.getmembers(test_mod.py1415_sequence_TestCase)
    for mm in methods:
        (name, _) = mm
        if name.startswith("test_"):
            test = getattr(t14, name)
            t14.setUp()
            try:
                if inspect.iscoroutinefunction(test):
                    await test()
                else:
                    test()
                tests_pass[name] = True
            except (AssertionError, RuntimeWarning) as doh:
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
        print(f"{pf}{test:<20}")
    assert not any_failed


@cocotb.test()  # pylint: disable=no-value-for-parameter
async def test_14_sequences(dut):
    """Tests the Sequences"""
    clock = Clock(dut.clk, 2, "us")
    cocotb.start_soon(clock.start())
    await run_tests(dut)
