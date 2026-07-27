import pytest
from async_helpers import run_pytest_coro
from test_uvm_reg_frontdoor_adapter import (
    AsyncNoopLock,
    MockSequencer,
    RecordingAdapter,
)

from pyuvm import (
    uvm_access_e,
    uvm_door_e,
    uvm_endianness_e,
    uvm_mem,
    uvm_reg_block,
    uvm_status_e,
)


def build_memory(
    *,
    size=4,
    n_bits=16,
    access="RW",
    rights="RW",
    unmapped=False,
    adapter=None,
    sequencer=None,
):
    block = uvm_reg_block("mem_block")
    reg_map = block.create_map(
        "map", 0x1000, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True
    )
    mem = uvm_mem("storage", size, n_bits, access)
    mem.configure(block)
    reg_map.add_mem(mem, 0x20, rights=rights, unmapped=unmapped)
    block.lock_model()
    mem._atomic = AsyncNoopLock()
    if sequencer is not None:
        reg_map.set_sequencer(sequencer, adapter)
    return reg_map, mem


def test_memory_write_and_read_use_selected_element_address():
    adapter = RecordingAdapter()
    sequencer = MockSequencer(read_data=0xBEEF)
    reg_map, mem = build_memory(adapter=adapter, sequencer=sequencer)

    write_status = run_pytest_coro(
        mem.write(2, 0x1234, uvm_door_e.UVM_FRONTDOOR, reg_map)
    )
    read_status, value = run_pytest_coro(
        mem.read(1, uvm_door_e.UVM_FRONTDOOR, reg_map)
    )

    assert write_status == uvm_status_e.UVM_IS_OK
    assert read_status == uvm_status_e.UVM_IS_OK
    assert value == 0xBEEF
    write_op, read_op = adapter.reg2bus_ops
    assert write_op.kind == uvm_access_e.UVM_WRITE
    assert write_op.addr == 0x1024
    assert write_op.data == 0x1234
    assert write_op.n_bits == 16
    assert write_op.byte_en == 0x3
    assert read_op.kind == uvm_access_e.UVM_READ
    assert read_op.addr == 0x1022
    assert read_op.n_bits == 16


@pytest.mark.parametrize("offset", [-1, 4])
def test_out_of_range_access_does_not_reach_adapter(offset):
    adapter = RecordingAdapter()
    sequencer = MockSequencer()
    reg_map, mem = build_memory(adapter=adapter, sequencer=sequencer)

    status = run_pytest_coro(
        mem.write(offset, 1, uvm_door_e.UVM_FRONTDOOR, reg_map)
    )

    assert status == uvm_status_e.UVM_NOT_OK
    assert adapter.reg2bus_ops == []


def test_unmapped_access_does_not_reach_adapter():
    adapter = RecordingAdapter()
    sequencer = MockSequencer()
    reg_map, mem = build_memory(
        unmapped=True, adapter=adapter, sequencer=sequencer
    )

    status, value = run_pytest_coro(
        mem.read(0, uvm_door_e.UVM_FRONTDOOR, reg_map)
    )

    assert status == uvm_status_e.UVM_NOT_OK
    assert value == 0
    assert adapter.reg2bus_ops == []


def test_read_only_memory_rejects_write_before_adapter():
    adapter = RecordingAdapter()
    sequencer = MockSequencer()
    reg_map, mem = build_memory(
        access="RO", adapter=adapter, sequencer=sequencer
    )

    status = run_pytest_coro(
        mem.write(0, 1, uvm_door_e.UVM_FRONTDOOR, reg_map)
    )

    assert status == uvm_status_e.UVM_NOT_OK
    assert adapter.reg2bus_ops == []


def test_read_only_map_rights_reject_write_before_adapter():
    adapter = RecordingAdapter()
    sequencer = MockSequencer()
    reg_map, mem = build_memory(
        rights="RO", adapter=adapter, sequencer=sequencer
    )

    status = run_pytest_coro(
        mem.write(0, 1, uvm_door_e.UVM_FRONTDOOR, reg_map)
    )

    assert mem.get_rights(reg_map) == "RO"
    assert mem.get_access(reg_map) == "RO"
    assert status == uvm_status_e.UVM_NOT_OK
    assert adapter.reg2bus_ops == []


def test_wide_memory_rejects_unsupported_multibeat_access():
    adapter = RecordingAdapter()
    sequencer = MockSequencer()
    reg_map, mem = build_memory(
        n_bits=64, adapter=adapter, sequencer=sequencer
    )

    status = run_pytest_coro(
        mem.write(0, 1, uvm_door_e.UVM_FRONTDOOR, reg_map)
    )

    assert status == uvm_status_e.UVM_NOT_OK
    assert adapter.reg2bus_ops == []


def test_adapter_status_and_read_mask_are_propagated():
    adapter = RecordingAdapter()
    sequencer = MockSequencer(
        read_data=0x1FFFF, read_status=uvm_status_e.UVM_NOT_OK
    )
    reg_map, mem = build_memory(adapter=adapter, sequencer=sequencer)

    status, value = run_pytest_coro(
        mem.read(0, uvm_door_e.UVM_FRONTDOOR, reg_map)
    )

    assert status == uvm_status_e.UVM_NOT_OK
    assert value == 0xFFFF


def test_default_door_and_default_map_are_resolved():
    adapter = RecordingAdapter()
    sequencer = MockSequencer(read_data=0x1234)
    reg_map, mem = build_memory(adapter=adapter, sequencer=sequencer)

    status, value = run_pytest_coro(mem.read(0))

    assert status == uvm_status_e.UVM_IS_OK
    assert value == 0x1234
    assert adapter.reg2bus_ops[-1].addr == 0x1020


def test_non_frontdoor_access_is_rejected_before_adapter():
    adapter = RecordingAdapter()
    sequencer = MockSequencer()
    reg_map, mem = build_memory(adapter=adapter, sequencer=sequencer)

    status = run_pytest_coro(
        mem.write(0, 1, uvm_door_e.UVM_BACKDOOR, reg_map)
    )

    assert status == uvm_status_e.UVM_NOT_OK
    assert adapter.reg2bus_ops == []


def test_access_through_unrelated_map_is_rejected():
    adapter = RecordingAdapter()
    sequencer = MockSequencer()
    reg_map, mem = build_memory(adapter=adapter, sequencer=sequencer)
    other_block = uvm_reg_block("other")
    other_map = other_block.create_map(
        "other_map", 0, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True
    )

    status = run_pytest_coro(
        mem.write(0, 1, uvm_door_e.UVM_FRONTDOOR, other_map)
    )

    assert status == uvm_status_e.UVM_NOT_OK
    assert adapter.reg2bus_ops == []


def test_write_only_map_rights_reject_read_before_adapter():
    adapter = RecordingAdapter()
    sequencer = MockSequencer()
    reg_map, mem = build_memory(
        rights="WO", adapter=adapter, sequencer=sequencer
    )

    status, value = run_pytest_coro(
        mem.read(0, uvm_door_e.UVM_FRONTDOOR, reg_map)
    )

    assert status == uvm_status_e.UVM_NOT_OK
    assert value == 0
    assert adapter.reg2bus_ops == []
