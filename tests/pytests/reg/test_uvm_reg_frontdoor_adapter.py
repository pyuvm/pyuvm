import asyncio
from dataclasses import replace

import pytest

from pyuvm._error_classes import UVMFatalError
from pyuvm._reg.uvm_reg import uvm_reg
from pyuvm._reg.uvm_reg_adapter import uvm_reg_adapter
from pyuvm._reg.uvm_reg_block import uvm_reg_block
from pyuvm._reg.uvm_reg_field import uvm_reg_field
from pyuvm._reg.uvm_reg_model import (
    uvm_access_e,
    uvm_door_e,
    uvm_endianness_e,
    uvm_status_e,
)
from pyuvm._s14_15_python_sequences import uvm_sequence, uvm_sequence_item


class AsyncNoopLock:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def locked(self):
        return False

    def release(self):
        pass


class FrontdoorReg(uvm_reg):
    def __init__(self, name="frontdoor_reg"):
        super().__init__(name, 32)
        self.data = uvm_reg_field("data")
        self.data.configure(self, 32, 0, "RW", False, 0, True, False, False)


class MockBusItem(uvm_sequence_item):
    def __init__(
        self,
        name,
        kind=None,
        addr=0,
        data=0,
        n_bits=0,
        byte_en=0,
        status=uvm_status_e.UVM_IS_OK,
    ):
        super().__init__(name)
        self.kind = kind
        self.addr = addr
        self.data = data
        self.n_bits = n_bits
        self.byte_en = byte_en
        self.status = status


class MockSequencer:
    def __init__(
        self,
        read_data=0,
        read_status=uvm_status_e.UVM_IS_OK,
        write_status=uvm_status_e.UVM_IS_OK,
        use_response=False,
    ):
        self.read_data = read_data
        self.read_status = read_status
        self.write_status = write_status
        self.use_response = use_response
        self.started = []
        self.finished = []
        self.responses = []
        self.response_txn_ids = []

    async def start_item(self, item):
        self.started.append(item)

    async def finish_item(self, item):
        self.finished.append(item)
        if item.kind == uvm_access_e.UVM_READ:
            data = self.read_data
            status = self.read_status
        else:
            data = item.data
            status = self.write_status

        if self.use_response:
            self.responses.append(
                MockBusItem(
                    "bus_rsp",
                    item.kind,
                    item.addr,
                    data,
                    item.n_bits,
                    item.byte_en,
                    status,
                )
            )
        else:
            item.data = data
            item.status = status

    async def get_response(self, txn_id=None):
        self.response_txn_ids.append(txn_id)
        return self.responses.pop(0)


class RecordingAdapter(uvm_reg_adapter):
    def __init__(self, name="recording_adapter", supports_byte_enable=True):
        super().__init__(name)
        self.supports_byte_enable = supports_byte_enable
        self.reg2bus_ops = []
        self.reg2bus_parent_sequences = []
        self.bus2reg_items = []

    def reg2bus(self, rw):
        self.reg2bus_ops.append(replace(rw))
        self.reg2bus_parent_sequences.append(self.get_item().get_parent_sequence())
        return MockBusItem(
            "bus_req",
            rw.kind,
            rw.addr,
            rw.data,
            rw.n_bits,
            rw.byte_en,
            rw.status,
        )

    def bus2reg(self, bus_item, rw):
        self.bus2reg_items.append(bus_item)
        rw.kind = bus_item.kind
        rw.addr = bus_item.addr
        rw.data = bus_item.data
        rw.n_bits = bus_item.n_bits
        rw.byte_en = bus_item.byte_en
        rw.status = bus_item.status


def build_model(adapter=None, sequencer=None, auto_predict=True):
    block = uvm_reg_block("phase4_block")
    reg_map = block.create_map(
        "csr", 0x1000, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True
    )
    reg = FrontdoorReg()
    reg.configure(block)
    reg_map.add_reg(reg, 0x20, "RW")
    block.lock_model()
    reg._atomic = AsyncNoopLock()
    reg.reset()
    reg_map.set_auto_predict(auto_predict)
    if sequencer is not None:
        reg_map.set_sequencer(sequencer, adapter)
    return block, reg_map, reg


def test_frontdoor_write_and_read_through_adapter():
    adapter = RecordingAdapter()
    sequencer = MockSequencer(read_data=0xCAFE_BABE)
    _, reg_map, reg = build_model(adapter, sequencer)

    write_status = asyncio.run(
        reg.write(0x1234_5678, uvm_door_e.UVM_FRONTDOOR, reg_map)
    )
    read_status, read_data = asyncio.run(
        reg.read(uvm_door_e.UVM_FRONTDOOR, reg_map)
    )

    assert write_status == uvm_status_e.UVM_IS_OK
    assert read_status == uvm_status_e.UVM_IS_OK
    assert read_data == 0xCAFE_BABE

    write_op, read_op = adapter.reg2bus_ops
    assert write_op.kind == uvm_access_e.UVM_WRITE
    assert write_op.addr == 0x1020
    assert write_op.data == 0x1234_5678
    assert write_op.n_bits == 32
    assert write_op.byte_en == 0xF
    assert write_op.status == uvm_status_e.UVM_IS_OK

    assert read_op.kind == uvm_access_e.UVM_READ
    assert read_op.addr == 0x1020
    assert read_op.data == 0
    assert read_op.n_bits == 32
    assert read_op.byte_en == 0xF
    assert read_op.status == uvm_status_e.UVM_IS_OK

    assert [item.kind for item in sequencer.started] == [
        uvm_access_e.UVM_WRITE,
        uvm_access_e.UVM_READ,
    ]
    assert reg.get_mirrored_value() == 0xCAFE_BABE


def test_frontdoor_status_controls_auto_prediction():
    adapter = RecordingAdapter()
    sequencer = MockSequencer(write_status=uvm_status_e.UVM_NOT_OK)
    _, reg_map, reg = build_model(adapter, sequencer)

    status = asyncio.run(reg.write(0x1111_2222, uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert status == uvm_status_e.UVM_NOT_OK
    assert reg.get_mirrored_value() == 0


def test_adapter_without_byte_enable_uses_all_bytes_sentinel():
    adapter = RecordingAdapter(supports_byte_enable=False)
    sequencer = MockSequencer()
    _, reg_map, reg = build_model(adapter, sequencer)

    status = asyncio.run(reg.write(0xA5A5_A5A5, uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert status == uvm_status_e.UVM_IS_OK
    assert adapter.reg2bus_ops[-1].byte_en == -1


def test_adapter_parent_sequence_and_responses_are_used():
    adapter = RecordingAdapter()
    adapter.provides_responses = True
    adapter.parent_sequence = uvm_sequence("adapter_parent_seq")
    sequencer = MockSequencer(read_data=0x1357_9BDF, use_response=True)
    _, reg_map, reg = build_model(adapter, sequencer)

    status, value = asyncio.run(reg.read(uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert status == uvm_status_e.UVM_IS_OK
    assert value == 0x1357_9BDF
    assert adapter.reg2bus_parent_sequences[-1] is adapter.parent_sequence
    assert adapter.bus2reg_items[-1].get_name() == "bus_rsp"
    assert sequencer.response_txn_ids


def test_map_creates_parent_sequence_when_adapter_does_not_supply_one():
    adapter = RecordingAdapter()
    sequencer = MockSequencer()
    _, reg_map, reg = build_model(adapter, sequencer)

    status = asyncio.run(reg.write(0x55AA_55AA, uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert status == uvm_status_e.UVM_IS_OK
    assert adapter.parent_sequence is None
    assert adapter.reg2bus_parent_sequences[-1].get_name() == "base_seq"


def test_missing_adapter_and_sequencer_raise_useful_errors():
    _, reg_map, reg = build_model()

    with pytest.raises(UVMFatalError, match="no adapter configured"):
        asyncio.run(reg.write(0x1, uvm_door_e.UVM_FRONTDOOR, reg_map))

    adapter = RecordingAdapter()
    _, reg_map, reg = build_model()
    with pytest.warns(DeprecationWarning):
        reg_map.set_adapter(adapter)

    with pytest.raises(UVMFatalError, match="no sequencer configured"):
        asyncio.run(reg.read(uvm_door_e.UVM_FRONTDOOR, reg_map))


def test_legacy_response_spelling_updates_canonical_property():
    adapter = RecordingAdapter()

    adapter.provides_response = True

    assert adapter.provides_responses
