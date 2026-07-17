"""Tests for uvm_tlm interface fixes (IEEE 1800.2 section 12.2).

These exercise the non-blocking / structural TLM paths that can be driven
without a running simulation. The blocking transport() round-trip (12.2.9.2.2)
requires a coroutine and is covered by the t12_tlm cocotb test.
"""

import pytest

from pyuvm import (
    uvm_blocking_peek_export,
    uvm_nonblocking_get_peek_export,
    uvm_nonblocking_master_export,
    uvm_nonblocking_put_export,
    uvm_tlm_fifo,
    uvm_tlm_req_rsp_channel,
    uvm_tlm_transport_channel,
)

pytestmark = pytest.mark.usefixtures("initialize_pyuvm")


def test_nonblocking_get_export_uses_get_ap():
    """
    12.2.8 A get export must broadcast consumed items on the get analysis port,
    not the put analysis port. Regression: it was constructed with put_ap.
    """
    fifo = uvm_tlm_fifo("fifo", None)
    assert fifo.nonblocking_get_export.ap is fifo.get_ap
    assert fifo.nonblocking_get_export.ap is not fifo.put_ap


def test_master_slave_try_get_returns_tuple():
    """
    12.2.4.2.7 try_get returns an (ok, item) tuple. Regression: the master/slave
    export returned the bound method object (missing call parentheses), so
    callers unpacking (success, item) got a method instead of a result.
    """
    ch = uvm_tlm_req_rsp_channel("ch", None)
    result = ch.master_export.try_get()
    assert isinstance(result, tuple)
    ok, item = result
    assert ok is False
    assert item is None


def test_master_slave_peek_family_delegates():
    """
    12.2.4.2.x The master/slave export must implement peek/can_peek/try_peek by
    delegating to its internal get_peek export. Regression: these were inherited
    from the port base and dereferenced an unset self.export.
    """
    ch = uvm_tlm_req_rsp_channel("ch", None)
    # Empty response FIFO: can_peek False, try_peek a (False, None) tuple.
    assert ch.master_export.can_peek() is False
    result = ch.master_export.try_peek()
    assert isinstance(result, tuple)
    ok, item = result
    assert ok is False
    assert item is None


def test_nb_transport_returns_tuple_on_full():
    """
    12.2.9.2.2 nb_transport returns a consistent (ok, item) tuple shape on both
    the success and failure paths. Regression: the full/failure path returned a
    bare False, which raised TypeError when the caller unpacked the result.
    """
    tc = uvm_tlm_transport_channel("tc", None)
    # Fill the size-1 request FIFO so the request try_put fails.
    assert tc.req_tlm_fifo.put_export.try_put("req") is True
    result = tc.transport_export.nb_transport("req2")
    assert result == (False, None)


def test_nonblocking_master_export_composition():
    """
    A nonblocking master export composes nonblocking put + nonblocking
    get_peek. Regression: it inherited uvm_blocking_peek_export instead of
    uvm_nonblocking_put_export.
    """
    assert issubclass(uvm_nonblocking_master_export, uvm_nonblocking_put_export)
    assert issubclass(uvm_nonblocking_master_export, uvm_nonblocking_get_peek_export)
    assert not issubclass(uvm_nonblocking_master_export, uvm_blocking_peek_export)
