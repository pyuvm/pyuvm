import pytest

from pyuvm import uvm_root, uvm_seq_item_export, uvm_seq_item_port, uvm_sequence_item

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
