import asyncio
from unittest.mock import AsyncMock

import pytest
from async_helpers import run_pytest_coro

import pyuvm
from pyuvm import (
    UVMSequenceError,
    uvm_access_e,
    uvm_check_e,
    uvm_door_e,
    uvm_mem,
    uvm_reg,
    uvm_reg_frontdoor,
    uvm_reg_item,
    uvm_reg_sequence,
    uvm_status_e,
)
from pyuvm._reg.uvm_reg_sequence import (
    uvm_reg_frontdoor as sequence_uvm_reg_frontdoor,
)
from pyuvm._s05_base_classes import uvm_object


class StopTranslation(Exception):
    pass


class OneItemUpstream:
    def __init__(self, item):
        self.item = item
        self.item_done_calls = 0
        self.get_calls = 0

    async def get_next_item(self):
        self.get_calls += 1
        if self.get_calls == 1:
            return self.item
        raise StopTranslation

    def item_done(self):
        self.item_done_calls += 1


class RecordingMap:
    def __init__(self):
        self.calls = []

    async def do_bus_write(self, rw, sequencer, adapter):
        self.calls.append(("write", rw, sequencer, adapter))

    async def do_bus_read(self, rw, sequencer, adapter):
        self.calls.append(("read", rw, sequencer, adapter))


class AsyncLock:
    def __init__(self):
        self.acquire_calls = 0
        self.release_calls = 0
        self._locked = False

    async def acquire(self):
        self.acquire_calls += 1
        self._locked = True

    def release(self):
        self.release_calls += 1
        self._locked = False

    def locked(self):
        return self._locked


class LegacyAsyncLock(AsyncLock):
    @property
    def locked(self):
        return self._locked


class RecordingFrontdoor(uvm_reg_frontdoor):
    def __init__(self):
        super().__init__("recording_frontdoor")
        self.body_calls = 0
        self.task = object()
        self._current_task = lambda: self.task

    async def body(self):
        self.body_calls += 1


def test_sequence_and_frontdoor_construct_with_expected_defaults():
    sequence = uvm_reg_sequence()
    frontdoor = uvm_reg_frontdoor()

    assert sequence.model is None
    assert sequence.adapter is None
    assert sequence.reg_seqr is None
    assert frontdoor.rw_info is None


def test_top_level_frontdoor_is_sequence_implementation():
    assert pyuvm.uvm_reg_frontdoor is sequence_uvm_reg_frontdoor


def test_translation_body_processes_and_finishes_upstream_item():
    original_parent = object()
    rw = uvm_reg_item("rw")
    rw.set_parent_sequence(original_parent)
    upstream = OneItemUpstream(rw)
    sequence = uvm_reg_sequence()
    sequence.reg_seqr = upstream
    seen_parents = []

    async def record_item(item):
        seen_parents.append(item.get_parent_sequence())

    sequence.do_reg_item = record_item

    with pytest.raises(StopTranslation):
        run_pytest_coro(sequence.body())

    assert seen_parents == [sequence]
    assert rw.get_parent_sequence() is original_parent
    assert upstream.item_done_calls == 1


def test_translation_body_restores_parent_and_finishes_after_failure():
    original_parent = object()
    rw = uvm_reg_item("rw")
    rw.set_parent_sequence(original_parent)
    upstream = OneItemUpstream(rw)
    sequence = uvm_reg_sequence()
    sequence.reg_seqr = upstream

    async def fail_item(_item):
        raise RuntimeError("bus failure")

    sequence.do_reg_item = fail_item

    with pytest.raises(RuntimeError, match="bus failure"):
        run_pytest_coro(sequence.body())

    assert rw.get_parent_sequence() is original_parent
    assert upstream.item_done_calls == 1


def test_translation_body_rejects_non_register_item_and_finishes_it():
    upstream = OneItemUpstream(object())
    sequence = uvm_reg_sequence()
    sequence.reg_seqr = upstream

    with pytest.raises(UVMSequenceError, match="not a uvm_reg_item"):
        run_pytest_coro(sequence.body())

    assert upstream.item_done_calls == 1


def test_translation_body_without_upstream_reports_and_returns(caplog):
    sequence = uvm_reg_sequence()

    run_pytest_coro(sequence.body())

    assert "no upstream register sequencer" in caplog.text


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        (uvm_access_e.UVM_WRITE, "write"),
        (uvm_access_e.UVM_READ, "read"),
    ],
)
def test_do_reg_item_uses_selected_map_bus_path(kind, expected):
    sequence = uvm_reg_sequence()
    sequence.sequencer = object()
    sequence.adapter = object()
    local_map = RecordingMap()
    rw = uvm_reg_item("rw")
    rw.set_kind(kind)
    rw.set_local_map(local_map)

    run_pytest_coro(sequence.do_reg_item(rw))

    assert local_map.calls == [(expected, rw, sequence.sequencer, sequence.adapter)]


@pytest.mark.parametrize(
    ("configure", "message"),
    [
        (lambda seq, rw: setattr(seq, "sequencer", None), "downstream sequencer"),
        (lambda seq, rw: setattr(seq, "adapter", None), "no adapter"),
        (lambda seq, rw: rw.set_local_map(None), "no selected local map"),
        (
            lambda seq, rw: rw.set_kind(uvm_access_e.UVM_BURST_WRITE),
            "Unsupported register translation access kind",
        ),
    ],
)
def test_do_reg_item_rejects_incomplete_or_unsupported_requests(configure, message):
    sequence = uvm_reg_sequence()
    sequence.sequencer = object()
    sequence.adapter = object()
    rw = uvm_reg_item("rw")
    rw.set_kind(uvm_access_e.UVM_WRITE)
    rw.set_local_map(RecordingMap())
    configure(sequence, rw)

    with pytest.raises(UVMSequenceError, match=message):
        run_pytest_coro(sequence.do_reg_item(rw))


def test_do_reg_item_rejects_non_register_item():
    sequence = uvm_reg_sequence()

    with pytest.raises(UVMSequenceError, match="requires a uvm_reg_item"):
        run_pytest_coro(sequence.do_reg_item(object()))


def test_register_convenience_helpers_delegate_all_arguments():
    sequence = uvm_reg_sequence("helper_sequence")
    reg = uvm_reg("reg", 32)
    reg.write = AsyncMock(return_value=uvm_status_e.UVM_IS_OK)
    reg.read = AsyncMock(return_value=(uvm_status_e.UVM_IS_OK, 0x55))
    reg.update = AsyncMock(return_value=uvm_status_e.UVM_HAS_X)
    reg.mirror = AsyncMock(return_value=uvm_status_e.UVM_NOT_OK)
    reg_map = object()
    extension = uvm_object("extension")

    write_status = run_pytest_coro(
        sequence.write_reg(
            reg, 0xAA, uvm_door_e.UVM_FRONTDOOR, reg_map, 7, extension, "a.py", 9
        )
    )
    read_result = run_pytest_coro(
        sequence.read_reg(
            reg, uvm_door_e.UVM_FRONTDOOR, reg_map, 8, extension, "b.py", 10
        )
    )
    update_status = run_pytest_coro(
        sequence.update_reg(
            reg, uvm_door_e.UVM_FRONTDOOR, reg_map, 9, extension, "c.py", 11
        )
    )
    mirror_status = run_pytest_coro(
        sequence.mirror_reg(
            reg,
            uvm_check_e.UVM_CHECK,
            uvm_door_e.UVM_FRONTDOOR,
            reg_map,
            10,
            extension,
            "d.py",
            12,
        )
    )

    assert write_status == uvm_status_e.UVM_IS_OK
    assert read_result == (uvm_status_e.UVM_IS_OK, 0x55)
    assert update_status == uvm_status_e.UVM_HAS_X
    assert mirror_status == uvm_status_e.UVM_NOT_OK
    reg.write.assert_awaited_once_with(
        0xAA, uvm_door_e.UVM_FRONTDOOR, reg_map, sequence, 7, extension, "a.py", 9
    )
    reg.read.assert_awaited_once_with(
        uvm_door_e.UVM_FRONTDOOR, reg_map, sequence, 8, extension, "b.py", 10
    )
    reg.update.assert_awaited_once_with(
        uvm_door_e.UVM_FRONTDOOR, reg_map, sequence, 9, extension, "c.py", 11
    )
    reg.mirror.assert_awaited_once_with(
        uvm_check_e.UVM_CHECK,
        uvm_door_e.UVM_FRONTDOOR,
        reg_map,
        sequence,
        10,
        extension,
        "d.py",
        12,
    )


def test_memory_convenience_helpers_delegate_all_arguments():
    sequence = uvm_reg_sequence("helper_sequence")
    mem = uvm_mem("mem", 4, 16, "RW")
    mem.write = AsyncMock(return_value=uvm_status_e.UVM_IS_OK)
    mem.read = AsyncMock(return_value=(uvm_status_e.UVM_HAS_X, 0x1234))
    reg_map = object()
    extension = uvm_object("extension")

    write_status = run_pytest_coro(
        sequence.write_mem(
            mem,
            2,
            0x5678,
            uvm_door_e.UVM_FRONTDOOR,
            reg_map,
            3,
            extension,
            "mem.py",
            14,
        )
    )
    read_result = run_pytest_coro(
        sequence.read_mem(
            mem,
            1,
            uvm_door_e.UVM_FRONTDOOR,
            reg_map,
            4,
            extension,
            "mem.py",
            15,
        )
    )

    assert write_status == uvm_status_e.UVM_IS_OK
    assert read_result == (uvm_status_e.UVM_HAS_X, 0x1234)
    mem.write.assert_awaited_once_with(
        2,
        0x5678,
        uvm_door_e.UVM_FRONTDOOR,
        reg_map,
        sequence,
        3,
        extension,
        "mem.py",
        14,
    )
    mem.read.assert_awaited_once_with(
        1,
        uvm_door_e.UVM_FRONTDOOR,
        reg_map,
        sequence,
        4,
        extension,
        "mem.py",
        15,
    )


def test_invalid_convenience_targets_report_and_return_failure(caplog):
    sequence = uvm_reg_sequence()

    write_status = run_pytest_coro(sequence.write_reg(None, 1))
    read_status = run_pytest_coro(sequence.read_reg(None))
    update_status = run_pytest_coro(sequence.update_reg(None))
    mirror_status = run_pytest_coro(sequence.mirror_reg(None))
    mem_write_status = run_pytest_coro(sequence.write_mem(None, 0, 1))
    mem_read_status = run_pytest_coro(sequence.read_mem(None, 0))

    assert write_status == uvm_status_e.UVM_NOT_OK
    assert read_status == (uvm_status_e.UVM_NOT_OK, 0)
    assert update_status == uvm_status_e.UVM_NOT_OK
    assert mirror_status == uvm_status_e.UVM_NOT_OK
    assert mem_write_status == uvm_status_e.UVM_NOT_OK
    assert mem_read_status == (uvm_status_e.UVM_NOT_OK, 0)
    assert caplog.text.count("requires a valid") == 6


@pytest.mark.parametrize(
    ("method", "args", "boundary"),
    [
        ("poke_reg", (None, 1), "register backdoor support"),
        ("peek_reg", (None,), "register backdoor support"),
        ("poke_mem", (None, 0, 1), "memory backdoor support"),
        ("peek_mem", (None, 0), "memory backdoor support"),
    ],
)
def test_peek_and_poke_helpers_are_explicit_backdoor_boundaries(method, args, boundary):
    sequence = uvm_reg_sequence()

    with pytest.raises(NotImplementedError, match=boundary):
        run_pytest_coro(getattr(sequence, method)(*args))


def test_base_frontdoor_body_requires_override():
    frontdoor = uvm_reg_frontdoor()
    frontdoor._atomic = AsyncLock()
    frontdoor._current_task = asyncio.current_task

    with pytest.raises(UVMSequenceError, match="must be overridden"):
        run_pytest_coro(frontdoor.start())

    assert frontdoor._atomic.acquire_calls == 1
    assert frontdoor._atomic.release_calls == 1


def test_frontdoor_start_awaits_body_and_automatically_locks():
    frontdoor = RecordingFrontdoor()
    frontdoor._atomic = AsyncLock()

    run_pytest_coro(frontdoor.start())

    assert frontdoor.body_calls == 1
    assert frontdoor._atomic.acquire_calls == 1
    assert frontdoor._atomic.release_calls == 1
    assert frontdoor._atomic_owner is None


def test_frontdoor_start_does_not_reacquire_task_owned_lock():
    frontdoor = RecordingFrontdoor()
    frontdoor._atomic = AsyncLock()

    async def run_locked():
        await frontdoor.atomic_lock()
        await frontdoor.atomic_lock()
        await frontdoor.start()
        assert frontdoor._atomic.locked()
        frontdoor.atomic_unlock()

    asyncio.run(run_locked())

    assert frontdoor.body_calls == 1
    assert frontdoor._atomic.acquire_calls == 1
    assert frontdoor._atomic.release_calls == 1


def test_frontdoor_unlock_supports_legacy_cocotb_lock_property():
    frontdoor = RecordingFrontdoor()
    frontdoor._atomic = LegacyAsyncLock()

    run_pytest_coro(frontdoor.start())

    assert frontdoor._atomic.acquire_calls == 1
    assert frontdoor._atomic.release_calls == 1
    assert frontdoor._atomic_owner is None


def test_frontdoor_current_task_uses_cocotb_task(monkeypatch):
    task = object()
    monkeypatch.setattr("pyuvm._reg.uvm_reg_sequence.current_task", lambda: task)

    assert uvm_reg_frontdoor._current_task() is task


def test_only_owning_task_can_unlock_frontdoor(caplog):
    frontdoor = RecordingFrontdoor()
    frontdoor._atomic = AsyncLock()

    async def exercise():
        await frontdoor.atomic_lock()

        async def other_task():
            frontdoor.task = object()
            frontdoor.atomic_unlock()

        await asyncio.create_task(other_task())
        assert frontdoor._atomic.locked()
        frontdoor.task = frontdoor._atomic_owner
        frontdoor.atomic_unlock()

    asyncio.run(exercise())

    assert "does not own it" in caplog.text
    assert frontdoor._atomic.release_calls == 1
