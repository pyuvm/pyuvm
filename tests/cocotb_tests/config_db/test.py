import inspect

import cocotb
import test_config_db as test_mod
from cocotb.clock import Clock

from pyuvm import *


async def run_tests(dut):
    tests_pass = {}
    tcfgdb = test_mod.config_db_TestCase()
    methods = inspect.getmembers(test_mod.config_db_TestCase)
    for mm in methods:
        (name, _) = mm
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
    for test, passed in tests_pass.items():
        if passed:
            pf = "Pass   "
        else:
            pf = "FAILED "
            any_failed = True
        print(f"{pf}{test:<20}")
    assert not any_failed


@cocotb.test()  # pylint: disable=no-value-for-parameter
async def test_12_tlm(dut):
    """Tests the TLM FIFOS"""
    clock = Clock(dut.clk, 2, "us")
    cocotb.start_soon(clock.start())
    await run_tests(dut)


class Test(uvm_test):
    async def run_phase(self):
        self.raise_objection()
        self.drop_objection()


@cocotb.test()
async def create_config_db(_):
    config_db_id = id(ConfigDB())
    await uvm_root().run_test("Test")
    second_id = id(ConfigDB())
    assert config_db_id is not second_id
