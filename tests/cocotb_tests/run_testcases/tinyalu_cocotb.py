from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
import cocotb
import pyuvm.utility_classes as utility_classes
import time
import asyncio.queues
from pyuvm import *
import test_08_factory_classes as t08



@cocotb.test()
async def factory_tests(dut):
    """Tests different aspects of the factory"""
    try:
        run_test(test_set_inst_override_by_type_8_3_1_4_1)
    except AssertionError:
        assert False
    assert True
