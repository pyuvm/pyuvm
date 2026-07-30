import asyncio
from itertools import count

import pytest
from async_helpers import run_pytest_coro
from test_uvm_mem_frontdoor import build_memory as build_builtin_memory
from test_uvm_reg_frontdoor_adapter import (
    AsyncNoopLock,
    FrontdoorReg,
    MockSequencer,
    RecordingAdapter,
    build_model,
)

from pyuvm import (
    uvm_access_e,
    uvm_door_e,
    uvm_elem_kind_e,
    uvm_endianness_e,
    uvm_mem,
    uvm_object,
    uvm_reg_block,
    uvm_reg_frontdoor,
    uvm_reg_item,
    uvm_sequence_item,
    uvm_sequencer,
    uvm_status_e,
)


class PhysicalItem(uvm_sequence_item):
    def __init__(self, rw):
        super().__init__("physical_item")
        self.element = rw.get_element()
        self.kind = rw.get_kind()
        self.offset = rw.get_offset()
        self.data = rw.get_value()
        self.status = uvm_status_e.UVM_IS_OK


class StorageSequencer(uvm_sequencer):
    _instance_ids = count()

    def __init__(self, name, storage=None, status=uvm_status_e.UVM_IS_OK):
        super().__init__(f"{name}_{next(self._instance_ids)}")
        self.storage = {} if storage is None else storage
        self.status = status
        self.items = []

    @staticmethod
    def _key(item):
        offset = 0 if item.offset is None else item.offset
        return item.element, offset

    async def start_item(self, item):
        self.items.append(item)

    async def finish_item(self, item):
        await asyncio.sleep(0)
        item.status = self.status
        if item.kind == uvm_access_e.UVM_WRITE:
            self.storage[self._key(item)] = item.data
        else:
            item.data = self.storage.get(self._key(item), 0)


class FrontdoorTestLock:
    """Non-scheduling lock double for simulator-free routing tests."""

    def __init__(self):
        self._locked = False

    async def acquire(self):
        self._locked = True

    def release(self):
        self._locked = False

    def locked(self):
        return self._locked


class StorageFrontdoor(uvm_reg_frontdoor):
    def __init__(self, name="storage_frontdoor"):
        super().__init__(name)
        self.snapshots = []
        self._atomic = FrontdoorTestLock()
        self._current_task = asyncio.current_task

    async def body(self):
        rw = self.rw_info
        self.snapshots.append(
            {
                "item": rw,
                "element": rw.get_element(),
                "element_kind": rw.get_element_kind(),
                "kind": rw.get_kind(),
                "offset": rw.get_offset(),
                "map": rw.get_map(),
                "local_map": rw.get_local_map(),
                "parent": rw.get_parent_sequence(),
                "priority": rw.get_priority(),
                "extension": rw.get_extension(),
                "fname": rw.get_fname(),
                "lineno": rw.get_line(),
                "sequencer": self.sequencer,
            }
        )
        item = PhysicalItem(rw)
        await self.start_item(item)
        await self.finish_item(item)
        rw.set_status(item.status)
        if rw.get_kind() == uvm_access_e.UVM_READ:
            rw.set_value(item.data)


class FailingFrontdoor(StorageFrontdoor):
    async def body(self):
        raise RuntimeError("frontdoor failed")


def build_register(
    *,
    rights="RW",
    unmapped=False,
    frontdoor=None,
    sequencer=None,
    auto_predict=False,
):
    block = uvm_reg_block("reg_block")
    reg_map = block.create_map(
        "map", 0x1000, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True
    )
    reg = FrontdoorReg()
    reg.configure(block)
    reg_map.add_reg(reg, 0x20, rights=rights, unmapped=unmapped, frontdoor=frontdoor)
    block.lock_model()
    reg._atomic = AsyncNoopLock()
    reg_map.set_auto_predict(auto_predict)
    if sequencer is not None:
        reg_map.set_sequencer(sequencer)
    return reg_map, reg


def build_memory(
    *,
    n_bits=16,
    access="RW",
    rights="RW",
    unmapped=False,
    frontdoor=None,
    sequencer=None,
):
    block = uvm_reg_block("mem_block")
    reg_map = block.create_map(
        "map", 0x1000, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True
    )
    mem = uvm_mem("storage", 4, n_bits, access)
    mem.configure(block)
    reg_map.add_mem(mem, 0x20, rights=rights, unmapped=unmapped, frontdoor=frontdoor)
    block.lock_model()
    mem._atomic = AsyncNoopLock()
    if sequencer is not None:
        reg_map.set_sequencer(sequencer)
    return reg_map, mem


def test_register_custom_frontdoor_write_and_read_match_bus_results():
    frontdoor = StorageFrontdoor()
    sequencer = StorageSequencer("reg_seqr")
    reg_map, reg = build_register(frontdoor=frontdoor, sequencer=sequencer)

    write_status = run_pytest_coro(
        reg.write(0x1234_5678, uvm_door_e.UVM_FRONTDOOR, reg_map)
    )
    read_status, value = run_pytest_coro(reg.read(uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert write_status == uvm_status_e.UVM_IS_OK
    assert read_status == uvm_status_e.UVM_IS_OK
    assert value == 0x1234_5678
    assert [item.kind for item in sequencer.items] == [
        uvm_access_e.UVM_WRITE,
        uvm_access_e.UVM_READ,
    ]
    assert frontdoor.sequencer is None


def test_memory_custom_frontdoor_write_and_read_match_bus_results():
    frontdoor = StorageFrontdoor()
    sequencer = StorageSequencer("mem_seqr")
    reg_map, mem = build_memory(frontdoor=frontdoor, sequencer=sequencer)

    write_status = run_pytest_coro(
        mem.write(2, 0xBEEF, uvm_door_e.UVM_FRONTDOOR, reg_map)
    )
    read_status, value = run_pytest_coro(mem.read(2, uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert write_status == uvm_status_e.UVM_IS_OK
    assert read_status == uvm_status_e.UVM_IS_OK
    assert value == 0xBEEF
    assert frontdoor.snapshots[0]["element_kind"] == uvm_elem_kind_e.UVM_MEM
    assert frontdoor.snapshots[0]["offset"] == 2


@pytest.mark.parametrize("element_kind", ["reg", "mem"])
def test_custom_and_builtin_frontdoors_have_equivalent_results(element_kind):
    write_value = 0x1234
    read_value = 0xBEEF
    adapter = RecordingAdapter()
    builtin_sequencer = MockSequencer(read_data=read_value)

    if element_kind == "reg":
        _, builtin_map, builtin_element = build_model(adapter, builtin_sequencer)
        builtin_write = run_pytest_coro(
            builtin_element.write(write_value, uvm_door_e.UVM_FRONTDOOR, builtin_map)
        )
        builtin_read = run_pytest_coro(
            builtin_element.read(uvm_door_e.UVM_FRONTDOOR, builtin_map)
        )
    else:
        builtin_map, builtin_element = build_builtin_memory(
            adapter=adapter, sequencer=builtin_sequencer
        )
        builtin_write = run_pytest_coro(
            builtin_element.write(1, write_value, uvm_door_e.UVM_FRONTDOOR, builtin_map)
        )
        builtin_read = run_pytest_coro(
            builtin_element.read(1, uvm_door_e.UVM_FRONTDOOR, builtin_map)
        )

    frontdoor = StorageFrontdoor()
    custom_sequencer = StorageSequencer("equivalence_seqr")
    if element_kind == "reg":
        custom_map, custom_element = build_register(
            frontdoor=frontdoor, sequencer=custom_sequencer
        )
        custom_sequencer.storage[(custom_element, 0)] = read_value
        custom_write = run_pytest_coro(
            custom_element.write(write_value, uvm_door_e.UVM_FRONTDOOR, custom_map)
        )
        custom_sequencer.storage[(custom_element, 0)] = read_value
        custom_read = run_pytest_coro(
            custom_element.read(uvm_door_e.UVM_FRONTDOOR, custom_map)
        )
    else:
        custom_map, custom_element = build_memory(
            frontdoor=frontdoor, sequencer=custom_sequencer
        )
        custom_write = run_pytest_coro(
            custom_element.write(1, write_value, uvm_door_e.UVM_FRONTDOOR, custom_map)
        )
        custom_sequencer.storage[(custom_element, 1)] = read_value
        custom_read = run_pytest_coro(
            custom_element.read(1, uvm_door_e.UVM_FRONTDOOR, custom_map)
        )

    assert custom_write == builtin_write == uvm_status_e.UVM_IS_OK
    assert custom_read == builtin_read == (uvm_status_e.UVM_IS_OK, read_value)


def test_memory_frontdoor_setter_and_getter_use_selected_map():
    initial = StorageFrontdoor("initial")
    replacement = StorageFrontdoor("replacement")
    reg_map, mem = build_memory(frontdoor=initial)

    assert mem.get_frontdoor(reg_map) is initial
    assert mem.get_frontdoor() is initial

    mem.set_frontdoor(replacement, reg_map, "frontdoor.py", 12)

    assert mem.get_frontdoor(reg_map) is replacement
    assert mem._fname == "frontdoor.py"
    assert mem._lineno == 12


def test_memory_frontdoor_helpers_handle_missing_map_and_map_info():
    loose = uvm_mem("loose_mem", 1, 8)

    assert loose.get_frontdoor() is None
    loose.set_frontdoor(StorageFrontdoor("loose_frontdoor"))

    block = uvm_reg_block("incomplete_block")
    reg_map = block.create_map("map", 0, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True)
    incomplete = uvm_mem("incomplete_mem", 1, 8)
    incomplete.configure(block)
    incomplete.add_map(reg_map)

    assert incomplete.get_frontdoor(reg_map) is None
    incomplete.set_frontdoor(StorageFrontdoor("incomplete_frontdoor"), reg_map)
    assert incomplete.get_frontdoor(reg_map) is None


def test_rw_info_propagates_complete_originating_operation():
    frontdoor = StorageFrontdoor()
    sequencer = StorageSequencer("info_seqr")
    reg_map, mem = build_memory(frontdoor=frontdoor, sequencer=sequencer)
    parent = object()
    extension = uvm_object("extension")

    status = run_pytest_coro(
        mem.write(
            3,
            0x1234,
            uvm_door_e.UVM_FRONTDOOR,
            reg_map,
            parent,
            17,
            extension,
            "source.py",
            42,
        )
    )

    info = frontdoor.snapshots[0]
    assert status == uvm_status_e.UVM_IS_OK
    assert info["item"] is frontdoor.rw_info
    assert info["element"] is mem
    assert info["element_kind"] == uvm_elem_kind_e.UVM_MEM
    assert info["kind"] == uvm_access_e.UVM_WRITE
    assert info["offset"] == 3
    assert info["map"] is reg_map
    assert info["local_map"] is reg_map
    assert info["parent"] is parent
    assert info["priority"] == 17
    assert info["extension"] is extension
    assert info["fname"] == "source.py"
    assert info["lineno"] == 42
    assert info["sequencer"] is sequencer


def test_explicit_frontdoor_sequencer_precedes_root_map_sequencer():
    frontdoor = StorageFrontdoor()
    explicit = StorageSequencer("explicit")
    root = StorageSequencer("root")
    frontdoor.sequencer = explicit
    reg_map, reg = build_register(frontdoor=frontdoor, sequencer=root)
    explicit.storage[(reg, 0)] = 0xA5A5
    root.storage[(reg, 0)] = 0x5A5A

    status, value = run_pytest_coro(reg.read(uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert status == uvm_status_e.UVM_IS_OK
    assert value == 0xA5A5
    assert len(explicit.items) == 1
    assert root.items == []
    assert frontdoor.sequencer is explicit


def test_missing_custom_frontdoor_sequencer_reports_failure(caplog):
    frontdoor = StorageFrontdoor()
    reg_map, reg = build_register(frontdoor=frontdoor)

    status = run_pytest_coro(reg.write(1, uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert status == uvm_status_e.UVM_NOT_OK
    assert frontdoor.snapshots == []
    assert "has no sequencer" in caplog.text


def test_missing_sequencer_diagnostic_handles_item_without_element(caplog):
    frontdoor = StorageFrontdoor()
    reg_map, _ = build_register()
    rw = uvm_reg_item("standalone_item")

    result = run_pytest_coro(reg_map.do_frontdoor(rw, frontdoor))

    assert result is False
    assert rw.get_status() == uvm_status_e.UVM_NOT_OK
    assert "standalone_item" in caplog.text


def test_invalid_custom_frontdoor_sequencer_is_rejected_before_activity(caplog):
    frontdoor = StorageFrontdoor()
    frontdoor.sequencer = object()
    reg_map, reg = build_register(frontdoor=frontdoor)

    status = run_pytest_coro(reg.write(1, uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert status == uvm_status_e.UVM_NOT_OK
    assert frontdoor.snapshots == []
    assert frontdoor.rw_info is None
    assert "is not a uvm_sequencer" in caplog.text


@pytest.mark.parametrize("element_kind", ["reg", "mem"])
def test_intentionally_unmapped_element_uses_custom_frontdoor(element_kind):
    frontdoor = StorageFrontdoor()
    sequencer = StorageSequencer(f"{element_kind}_seqr")
    if element_kind == "reg":
        reg_map, element = build_register(
            unmapped=True, frontdoor=frontdoor, sequencer=sequencer
        )
        result = run_pytest_coro(element.write(0x55, uvm_door_e.UVM_FRONTDOOR, reg_map))
    else:
        reg_map, element = build_memory(
            unmapped=True, frontdoor=frontdoor, sequencer=sequencer
        )
        result = run_pytest_coro(
            element.write(1, 0x55, uvm_door_e.UVM_FRONTDOOR, reg_map)
        )

    assert result == uvm_status_e.UVM_IS_OK
    assert len(sequencer.items) == 1


@pytest.mark.parametrize("element_kind", ["reg", "mem"])
def test_intentionally_unmapped_element_without_frontdoor_is_rejected(
    element_kind,
):
    sequencer = StorageSequencer(f"{element_kind}_seqr")
    if element_kind == "reg":
        reg_map, element = build_register(unmapped=True, sequencer=sequencer)
        result = run_pytest_coro(element.write(0x55, uvm_door_e.UVM_FRONTDOOR, reg_map))
    else:
        reg_map, element = build_memory(unmapped=True, sequencer=sequencer)
        result = run_pytest_coro(
            element.write(1, 0x55, uvm_door_e.UVM_FRONTDOOR, reg_map)
        )

    assert result == uvm_status_e.UVM_NOT_OK
    assert sequencer.items == []


def test_wider_than_bus_memory_uses_custom_frontdoor():
    frontdoor = StorageFrontdoor()
    sequencer = StorageSequencer("wide_seqr")
    reg_map, mem = build_memory(n_bits=64, frontdoor=frontdoor, sequencer=sequencer)
    value = 0x1234_5678_9ABC_DEF0

    write_status = run_pytest_coro(
        mem.write(1, value, uvm_door_e.UVM_FRONTDOOR, reg_map)
    )
    read_status, read_value = run_pytest_coro(
        mem.read(1, uvm_door_e.UVM_FRONTDOOR, reg_map)
    )

    assert write_status == uvm_status_e.UVM_IS_OK
    assert read_status == uvm_status_e.UVM_IS_OK
    assert read_value == value


def test_custom_frontdoor_status_and_read_mask_are_propagated():
    frontdoor = StorageFrontdoor()
    sequencer = StorageSequencer(
        "status_seqr",
        status=uvm_status_e.UVM_HAS_X,
    )
    reg_map, mem = build_memory(frontdoor=frontdoor, sequencer=sequencer)
    sequencer.storage[(mem, 0)] = 0x1FFFF

    status, value = run_pytest_coro(mem.read(0, uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert status == uvm_status_e.UVM_HAS_X
    assert value == 0xFFFF


@pytest.mark.parametrize(
    ("rights", "operation", "report"),
    [
        ("RO", "write", "read-only register"),
        ("WO", "read", "write-only register"),
    ],
)
def test_register_map_rights_apply_before_custom_frontdoor(
    rights, operation, report, caplog
):
    frontdoor = StorageFrontdoor()
    sequencer = StorageSequencer("rights_seqr")
    reg_map, reg = build_register(
        rights=rights, frontdoor=frontdoor, sequencer=sequencer
    )

    if operation == "write":
        result = run_pytest_coro(reg.write(1, uvm_door_e.UVM_FRONTDOOR, reg_map))
    else:
        result, _ = run_pytest_coro(reg.read(uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert result == uvm_status_e.UVM_NOT_OK
    assert sequencer.items == []
    assert report in caplog.text


def test_register_non_frontdoor_path_is_rejected_before_custom_activity():
    frontdoor = StorageFrontdoor()
    sequencer = StorageSequencer("path_seqr")
    reg_map, reg = build_register(frontdoor=frontdoor, sequencer=sequencer)

    status = run_pytest_coro(reg.write(1, uvm_door_e.UVM_PREDICT, reg_map))

    assert status == uvm_status_e.UVM_NOT_OK
    assert sequencer.items == []
    assert frontdoor.snapshots == []


def test_memory_validation_applies_before_custom_frontdoor(caplog):
    frontdoor = StorageFrontdoor()
    sequencer = StorageSequencer("validation_seqr")
    reg_map, mem = build_memory(access="RO", frontdoor=frontdoor, sequencer=sequencer)

    bounds_status = run_pytest_coro(mem.write(4, 1, uvm_door_e.UVM_FRONTDOOR, reg_map))
    rights_status = run_pytest_coro(mem.write(0, 1, uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert bounds_status == uvm_status_e.UVM_NOT_OK
    assert rights_status == uvm_status_e.UVM_NOT_OK
    assert sequencer.items == []
    assert "outside" in caplog.text
    assert "read-only memory" in caplog.text


@pytest.mark.parametrize("element_kind", ["reg", "mem"])
def test_frontdoor_exception_restores_state_and_is_reraised(element_kind):
    frontdoor = FailingFrontdoor()
    sequencer = StorageSequencer(f"{element_kind}_seqr")
    if element_kind == "reg":
        reg_map, element = build_register(frontdoor=frontdoor, sequencer=sequencer)
        operation = element.write(1, uvm_door_e.UVM_FRONTDOOR, reg_map)
    else:
        reg_map, element = build_memory(frontdoor=frontdoor, sequencer=sequencer)
        operation = element.write(0, 1, uvm_door_e.UVM_FRONTDOOR, reg_map)

    with pytest.raises(RuntimeError, match="frontdoor failed"):
        run_pytest_coro(operation)

    assert frontdoor.rw_info.get_status() == uvm_status_e.UVM_NOT_OK
    assert frontdoor.sequencer is None
    assert not frontdoor._atomic.locked()
    assert not element._write_in_progress
    if element_kind == "reg":
        assert not element.is_busy()
