import logging

import pytest

from pyuvm import (
    uvm_endianness_e,
    uvm_mem,
    uvm_reg,
    uvm_reg_block,
)
from pyuvm._reg.uvm_reg_map import (
    _first_progression_overlap,
    _uvm_mem_address_set,
)


def make_map(name="top", base=0, n_bytes=4, byte_addressing=True):
    block = uvm_reg_block(name)
    reg_map = block.create_map(
        "map",
        base,
        n_bytes,
        uvm_endianness_e.UVM_LITTLE_ENDIAN,
        byte_addressing,
    )
    return block, reg_map


def add_memory(block, reg_map, name="mem", size=4, n_bits=16, offset=0x10):
    mem = uvm_mem(name, size, n_bits)
    mem.configure(block)
    reg_map.add_mem(mem, offset)
    return mem


def test_add_mem_records_map_info_and_membership():
    block, reg_map = make_map(base=0x100)
    mem = add_memory(block, reg_map, offset=0x20)

    block.lock_model()
    info = reg_map.get_mem_map_info(mem)

    assert mem.get_maps([]) == [reg_map]
    assert mem.get_n_maps() == 1
    assert mem.is_in_map(reg_map)
    assert reg_map.get_memories() == [mem]
    assert info.offset == 0x20
    assert info.rights == "RW"
    assert info.stride == 2
    assert info.addr == [0x120]
    assert info.mem_range.min == 0x120
    assert info.mem_range.max == 0x126
    assert info.is_initialized


def test_byte_addressed_memory_offsets_addresses_and_stride_holes():
    block, reg_map = make_map(base=0x100, byte_addressing=True)
    mem = add_memory(block, reg_map, size=3, n_bits=16, offset=0x20)
    block.lock_model()

    assert mem.get_offset(0, reg_map) == 0x20
    assert mem.get_offset(2, reg_map) == 0x24
    assert mem.get_address(0, reg_map) == 0x120
    assert mem.get_address(1, reg_map) == 0x122
    assert mem.get_addresses(2, reg_map) == (2, [0x124])
    assert reg_map.get_mem_by_offset(0x120) is mem
    assert reg_map.get_mem_by_offset(0x122) is mem
    assert reg_map.get_mem_by_offset(0x121) is None
    assert reg_map.get_mem_by_offset(0x123) is None


def test_memory_address_introspection_rejects_negative_offset(caplog):
    block, reg_map = make_map()
    mem = add_memory(block, reg_map)
    block.lock_model()

    with caplog.at_level(logging.WARNING, logger="RegModel"):
        assert mem.get_offset(-1, reg_map) is None
        assert mem.get_address(-1, reg_map) is None
        assert mem.get_addresses(-1, reg_map) == (None, [])

    assert "Offset 0x-1 lies outside of memory 'mem'" in caplog.text


def test_word_addressed_memory_uses_map_address_units():
    block, reg_map = make_map(base=0x40, n_bytes=4, byte_addressing=False)
    mem = add_memory(block, reg_map, size=3, n_bits=32, offset=0x8)
    block.lock_model()

    assert reg_map.get_mem_map_info(mem).stride == 1
    assert mem.get_offset(2, reg_map) == 0xA
    assert mem.get_address(0, reg_map) == 0x48
    assert mem.get_address(2, reg_map) == 0x4A
    assert reg_map.get_mem_by_offset(0x49) is mem


def test_wide_memory_elements_occupy_each_bus_address():
    block, reg_map = make_map(base=0x100, n_bytes=4, byte_addressing=False)
    mem = add_memory(block, reg_map, size=2, n_bits=64, offset=0x4)
    block.lock_model()

    assert reg_map.get_mem_map_info(mem).stride == 2
    assert mem.get_addresses(0, reg_map) == (4, [0x104, 0x105])
    assert mem.get_addresses(1, reg_map) == (4, [0x106, 0x107])
    for address in range(0x104, 0x108):
        assert reg_map.get_mem_by_offset(address) is mem


def test_unmapped_memory_has_no_addresses_or_lookup_entries():
    block, reg_map = make_map()
    mem = uvm_mem("unmapped", 4, 32)
    mem.configure(block)
    reg_map.add_mem(mem, 0x10, unmapped=True)
    block.lock_model()

    info = reg_map.get_mem_map_info(mem)
    assert info.unmapped
    assert info.addr == []
    assert info.mem_range is None
    assert mem.get_offset(0, reg_map) is None
    assert mem.get_addresses(0, reg_map) == (None, [])
    assert reg_map.get_mem_by_offset(0x10) is None


def test_set_mem_offset_rebuilds_locked_lookup():
    block, reg_map = make_map()
    mem = add_memory(block, reg_map, size=2, n_bits=32, offset=0x10)
    block.lock_model()

    mem.set_offset(reg_map, 0x20)

    assert reg_map.get_mem_by_offset(0x10) is None
    assert reg_map.get_mem_by_offset(0x20) is mem
    assert mem.get_address(1, reg_map) == 0x24


def test_actual_memory_and_register_overlap_is_reported(caplog):
    block, reg_map = make_map()
    add_memory(block, reg_map, size=2, n_bits=16, offset=0x10)
    reg = uvm_reg("overlap", 32)
    reg.configure(block)
    reg_map.add_reg(reg, 0x12)

    with caplog.at_level(logging.WARNING, logger="RegModel"):
        block.lock_model()

    assert "overlaps register" in caplog.text
    # The stride hole at 0x11 remains unoccupied and produces no false overlap.
    assert reg_map.get_mem_by_offset(0x11) is None


def test_non_overlapping_memories_can_share_bounding_interval_without_warning(caplog):
    block, reg_map = make_map()
    even = add_memory(block, reg_map, "even", size=3, n_bits=16, offset=0x10)
    odd = add_memory(block, reg_map, "odd", size=3, n_bits=16, offset=0x11)

    with caplog.at_level(logging.WARNING, logger="RegModel"):
        block.lock_model()

    assert "overlaps memory" not in caplog.text
    assert reg_map.get_mem_by_offset(0x10) is even
    assert reg_map.get_mem_by_offset(0x11) is odd


def test_memory_lookup_translates_through_hierarchical_submap():
    top, root_map = make_map("top", base=0x100, n_bytes=4, byte_addressing=False)
    child = uvm_reg_block("child")
    child.configure(top)
    child_map = child.create_map(
        "child_map",
        0,
        4,
        uvm_endianness_e.UVM_LITTLE_ENDIAN,
        False,
    )
    root_map.add_submap(child_map, 0x20)
    mem = add_memory(child, child_map, size=2, n_bits=32, offset=0x4)

    top.lock_model()

    assert mem.get_address(0, root_map) == 0x124
    assert mem.get_address(1, root_map) == 0x125
    assert root_map.get_mem_by_offset(0x124) is mem
    assert root_map.get_mem_by_offset(0x125) is mem


def test_add_mem_rejects_duplicate_and_different_parent_and_repairs_rights(caplog):
    block, reg_map = make_map()
    mem = uvm_mem("mem", 2, 8)
    mem.configure(block)

    with caplog.at_level(logging.ERROR, logger="RegModel"):
        reg_map.add_mem(mem, 0, rights="invalid")
        reg_map.add_mem(mem, 4)

        other_block = uvm_reg_block("other")
        other_mem = uvm_mem("other_mem", 2, 8)
        other_mem.configure(other_block)
        reg_map.add_mem(other_mem, 8)

    assert reg_map.get_mem_map_info(mem).rights == "RW"
    assert "invalid map rights" in caplog.text
    assert "has already been added" in caplog.text
    assert "not in the same block" in caplog.text


def test_overlapping_memories_are_reported(caplog):
    block, reg_map = make_map()
    first = add_memory(block, reg_map, "first", size=2, n_bits=32, offset=0x10)
    second = add_memory(block, reg_map, "second", size=2, n_bits=32, offset=0x14)

    with caplog.at_level(logging.WARNING, logger="RegModel"):
        block.lock_model()

    assert "overlaps memory" in caplog.text
    assert reg_map.get_mem_by_offset(0x10) is first
    assert reg_map.get_mem_by_offset(0x14) is second


def test_set_offset_for_unmapped_memory_and_memory_absent_from_map(caplog):
    block, reg_map = make_map()
    mem = add_memory(block, reg_map, offset=0x10)
    absent = uvm_mem("absent", 2, 8)
    absent.configure(block)

    with caplog.at_level(logging.ERROR, logger="RegModel"):
        reg_map._set_mem_offset(absent, 0x20, False)

    mem.set_offset(reg_map, 0, unmapped=True)

    assert "memory is not mapped" in caplog.text
    assert reg_map.get_mem_map_info(mem).unmapped
    assert reg_map.get_mem_by_offset(0x10) is None


def test_map_info_and_lookup_diagnostics_before_lock(caplog):
    block, reg_map = make_map()
    mem = add_memory(block, reg_map)
    absent = uvm_mem("absent", 2, 8)
    absent.configure(block)

    with caplog.at_level(logging.WARNING, logger="RegModel"):
        assert reg_map.get_mem_map_info(mem) is not None
    assert "does not seem to be initialized" in caplog.text

    caplog.clear()
    with caplog.at_level(logging.ERROR, logger="RegModel"):
        assert reg_map.get_mem_map_info(absent) is None
        assert reg_map.get_mem_map_info(absent, error=False) is None
        assert reg_map.get_mem_by_offset(0x10) is None
    assert "not in map" in caplog.text
    assert "is not locked" in caplog.text


@pytest.mark.parametrize("offset", [-1, 4])
def test_get_offset_out_of_range_returns_minus_one(offset, caplog):
    block, reg_map = make_map()
    mem = add_memory(block, reg_map, size=4)
    block.lock_model()

    with caplog.at_level(logging.WARNING, logger="RegModel"):
        assert mem.get_offset(offset, reg_map) is None
    assert "lies outside of memory" in caplog.text


def test_get_offset_returns_minus_one_when_memory_has_no_map():
    mem = uvm_mem("loose", 2, 8)

    assert mem.get_offset() is None


def test_memory_map_selection_and_incompatible_rights_diagnostics(caplog):
    block = uvm_reg_block("top")
    first_map = block.create_map(
        "first", 0, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True
    )
    second_map = block.create_map(
        "second", 0x100, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True
    )
    mem = uvm_mem("storage", 2, 8, "RO")
    mem.configure(block)
    first_map.add_mem(mem, 0, rights="WO")
    second_map.add_mem(mem, 0, rights="RW")

    with caplog.at_level(logging.ERROR, logger="RegModel"):
        mem.set_offset(None, 4)
        assert mem.get_access(first_map) == "RO"
        mem._access = "INVALID"
        assert mem.get_access(first_map) == "INVALID"

    assert "Set offset requires a map" in caplog.text
    assert "restricted to WO" in caplog.text
    assert "invalid access mode" in caplog.text


def test_large_memory_uses_one_compact_lookup_descriptor():
    block, reg_map = make_map(base=0x100, byte_addressing=True)
    size = 10_000_000
    mem = add_memory(
        block,
        reg_map,
        name="large",
        size=size,
        n_bits=16,
        offset=0x20,
    )

    block.lock_model()

    assert len(reg_map._mems_by_offset) == 1
    descriptor = reg_map._mems_by_offset[mem]
    assert descriptor.size == size
    assert descriptor.first_addresses == (0x120,)
    assert descriptor.element_strides == (2,)
    last_address = 0x120 + (size - 1) * 2
    assert descriptor.max == last_address
    assert reg_map.get_mem_by_offset(last_address) is mem
    assert reg_map.get_mem_by_offset(last_address - 1) is None


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        ((0, 2, 2, 10, 2, 2), None),
        ((5, 0, 1, 5, 0, 1), 5),
        ((5, 0, 1, 6, 0, 1), None),
        ((6, 0, 1, 0, 2, 5), 6),
        ((5, 0, 1, 0, 2, 5), None),
        ((6, 2, 5, 6, 0, 1), 6),
        ((6, 2, 5, 5, 0, 1), None),
        ((0, 4, 5, 2, 4, 5), None),
        ((0, 4, 10, 6, 6, 10), 12),
        ((0, 4, 10, 0, 6, 10), 0),
        ((4, 2, 10, 8, 4, 5), 8),
        ((0, 4, 2, 6, 6, 1), None),
    ],
)
def test_finite_progression_overlap_cases(args, expected):
    assert _first_progression_overlap(*args) == expected


def test_single_element_address_descriptor_membership_and_disjoint_overlap():
    mem = uvm_mem("single", 1, 64)
    descriptor = _uvm_mem_address_set.create(mem, [0x10, 0x11], None)
    other_mem = uvm_mem("other", 1, 8)
    other = _uvm_mem_address_set.create(other_mem, [0x20], None)

    assert descriptor.element_strides == (0, 0)
    assert descriptor.contains(0x10)
    assert descriptor.contains(0x11)
    assert not descriptor.contains(0x12)
    assert not descriptor.contains(0x0F)
    assert descriptor.first_overlap(other) is None


def test_non_overlapping_register_and_memory_paths_are_ignored():
    block, reg_map = make_map()
    mem = add_memory(block, reg_map, size=2, n_bits=32, offset=0x10)
    reg = uvm_reg("reg", 32)
    reg.configure(block)
    reg_map.add_reg(reg, 0x30)
    block.lock_model()

    reg.set_offset(reg_map, 0x40)

    assert reg_map.get_mem_by_offset(0x10) is mem
    assert reg_map.get_reg_by_offset(0x40) is reg


def test_memory_lookup_diagnostic_paths_are_reported(caplog):
    mem = uvm_mem("mem", 2, 8)

    with caplog.at_level(logging.WARNING, logger="RegModel"):
        assert mem.get_vreg_by_name("missing") is None
        assert mem.get_vfield_by_name("missing") is None
        assert mem.get_addresses(0) == (None, [])

    assert "Unable to find virtual register" in caplog.text
    assert "Unable to find virtual field" in caplog.text
    assert "not found in map" in caplog.text


def test_register_map_diagnostic_paths_are_reported(caplog):
    block, reg_map = make_map(n_bytes=4)
    other_block, other_map = make_map(name="other", n_bytes=2)
    reg = uvm_reg("reg", 8)
    reg.configure(block)
    other_reg = uvm_reg("other_reg", 8)
    other_reg.configure(other_block)
    missing_reg = uvm_reg("missing_reg", 8)
    missing_reg.configure(block)
    mem = uvm_mem("mem", 1, 8)
    mem.configure(block)

    with caplog.at_level(logging.WARNING, logger="RegModel"):
        reg_map.add_reg(reg, 0)
        reg_map.add_reg(reg, 0)
        reg_map.add_reg(other_reg, 4)
        reg_map.get_reg_map_info(reg)
        reg_map.get_reg_map_info(missing_reg)
        reg_map.get_mem_map_info(mem)
        assert reg_map.get_reg_by_offset(0) is None
        assert reg_map.get_mem_by_offset(0) is None
        reg_map._set_reg_offset(missing_reg, 4, False)
        reg_map.set_sequencer(None)
        reg_map.set_submap_offset(None, 0)
        assert reg_map.get_submap_offset(other_map) == -1
        assert reg_map.get_submap_offset(None) == -1
        other_map._add_parent_map(None, 0)

        reg_map.add_submap(other_map, 0x10)
        reg_map.add_submap(other_map, 0x20)

        reg_map.add_submap(None, 0)

        reg_map._endian = None
        with pytest.raises(TypeError):
            reg_map.get_physical_addresses(0, 0, 1)

    assert "has already been added" in caplog.text
    assert "not in map" in caplog.text
    assert "None value specified for bus sequencer" in caplog.text
    assert "already a child" in caplog.text
    assert "Map has no specified endianness" in caplog.text


def test_register_overlap_diagnostics_are_reported(caplog):
    block, reg_map = make_map()
    first = uvm_reg("first", 32)
    second = uvm_reg("second", 32)
    third = uvm_reg("third", 32)
    first.configure(block)
    second.configure(block)
    third.configure(block)
    reg_map.add_reg(first, 0x10)
    reg_map.add_reg(second, 0x20)
    reg_map.add_reg(third, 0x10)

    with caplog.at_level(logging.WARNING, logger="RegModel"):
        block.lock_model()
        second.set_offset(reg_map, 0x10)

    assert "maps to same address" in caplog.text


def test_single_element_map_descriptor_and_register_remap_overlap(caplog):
    block, reg_map = make_map()
    mem = add_memory(block, reg_map, size=1, n_bits=32, offset=0x10)
    reg = uvm_reg("reg", 32)
    reg.configure(block)
    reg_map.add_reg(reg, 0x30)
    block.lock_model()

    with caplog.at_level(logging.WARNING, logger="RegModel"):
        reg.set_offset(reg_map, 0x10)

    descriptor = reg_map._mems_by_offset[mem]
    assert descriptor.element_strides == (0,)
    assert descriptor.contains(0x10)
    assert "overlaps with memory" in caplog.text
