import pytest

from pyuvm import (
    UVMSequenceError,
    uvm_root,
    uvm_seq_item_export,
    uvm_seq_item_port,
    uvm_sequence_item,
)

pytestmark = pytest.mark.usefixtures("initialize_pyuvm")


def make_connected_port():
    root = uvm_root()
    port = uvm_seq_item_port("seq_item_port", root)
    export = uvm_seq_item_export("seq_item_export", root)
    port.connect(export)
    return port, export


def test_try_next_item_returns_success_and_available_sequence_item():
    port, export = make_connected_port()
    item = uvm_sequence_item("item")
    export.req_q.put_nowait(item)

    success, result = port.try_next_item()

    assert success is True
    assert result is item
    assert export.current_item is item

    port.item_done()


def test_try_next_item_returns_failure_tuple_when_sequence_queue_is_empty():
    port, _export = make_connected_port()

    success, result = port.try_next_item()

    assert success is False
    assert result is None


def test_try_next_item_raises_error_if_called_twice_without_item_done():
    port, export = make_connected_port()
    item = uvm_sequence_item("item")
    export.req_q.put_nowait(item)

    success, result = port.try_next_item()

    assert success is True
    assert result is item

    with pytest.raises(
        UVMSequenceError,
        match="You must call item_done\\(\\) before calling try_next_item again",
    ):
        port.try_next_item()

    port.item_done()


def test_try_next_item_raises_assertion_error_if_export_is_disconnected():
    root = uvm_root()
    port = uvm_seq_item_port("seq_item_port", root)

    with pytest.raises(AssertionError, match="export is not connected"):
        port.try_next_item()
