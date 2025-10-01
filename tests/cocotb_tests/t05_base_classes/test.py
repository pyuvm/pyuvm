import cocotb
import pytest

from pyuvm import *


@cocotb.test()
async def test_01_uvm_transaction_accept_time(dut):
    """
    Test uvm_transaction accept time
    """
    tr0 = uvm_transaction()
    tr1 = uvm_transaction()
    tr0.accept_tr(None)
    await cocotb.triggers.Timer(100, "ns")
    tr1.accept_tr(None)
    assert tr1.get_accept_time() > tr0.get_accept_time()
    assert tr1.get_accept_time() > 0


@cocotb.test()
async def test_01_uvm_transaction_begin_time(dut):
    """
    Test uvm_transaction begin time
    """
    tr0 = uvm_transaction()
    tr1 = uvm_transaction()
    tr0.accept_tr(1)
    assert tr0.get_accept_time() == 1
    await cocotb.triggers.Timer(100, "ns")
    tr1.accept_tr(2)
    assert tr1.get_accept_time() == 2
    with pytest.raises(error_classes.UVMFatalError):
        tr1.begin_tr(1)
    tr1.begin_tr(None, None)
    await cocotb.triggers.Timer(100, "ns")
    tr0.begin_tr()
    # Check time values
    # Check begin time between transactions
    assert tr0.get_begin_time() > tr1.get_begin_time()
    assert tr1.get_begin_time() > 0
    assert tr0.get_begin_time() > tr1.get_begin_time()


@cocotb.test()
async def test_01_uvm_transaction_end_time(dut):
    """
    Test uvm_transaction begin time
    """
    tr0 = uvm_transaction()
    tr1 = uvm_transaction()
    tr0.accept_tr(None)
    tr0.begin_tr(None, None)
    tr0.end_tr(None, None)
    await cocotb.triggers.Timer(100, "ns")
    tr1.accept_tr(None)
    assert tr1.get_accept_time() > tr0.get_accept_time()
    await cocotb.triggers.Timer(50, "ns")
    tr1.begin_tr(None, None)
    await cocotb.triggers.Timer(100, "ns")
    tr1.end_tr(None, None)
    assert tr1.get_accept_time() < tr1.get_end_time()
    assert tr1.get_accept_time() < tr1.get_begin_time()
    assert tr1.get_end_time() > tr0.get_end_time()
