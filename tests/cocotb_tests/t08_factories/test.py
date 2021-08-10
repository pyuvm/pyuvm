from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
import cocotb
import pyuvm.utility_classes as utility_classes
import time
import asyncio.queues
import inspect
import test_08_factory_classes as t08


@cocotb.test() # pylint: disable=no-value-for-parameter
async def test_08_factory(dut):
    """Tests different aspects of the factory"""
    print("HEY WHAT IS GOING ON")
    tc08 = t08.s08_factory_classes_TestCase()
    methods = inspect.getmembers(t08.s08_factory_classes_TestCase)#, predicate=inspect.ismethod)
    for mm in methods:
        (name,_) = mm
        if name.startswith("test_"):
            print(name)
            test = getattr(tc08, name)
            tc08.setUp()
            if inspect.iscoroutinefunction(test):
                await test()
            else:
                test()
            tc08.tearDown()
    assert True


