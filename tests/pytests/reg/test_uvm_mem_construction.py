import io
import logging

import pytest

from pyuvm import uvm_hier_e, uvm_mem, uvm_reg_block
from pyuvm._error_classes import UVMFatalError
from pyuvm.uvm_reporting import set_sv_uvm_style_reporting_enabled
from pyuvm.uvm_reporting.uvm_report_server import (
    uvm_report_policy,
    uvm_report_server,
)


def test_memory_construction_normalizes_shape_access_and_width():
    mem = uvm_mem("storage", 16, 13, "ro")

    assert mem.get_name() == "storage"
    assert mem.get_size() == 16
    assert mem.get_n_bits() == 13
    assert mem.get_n_bytes() == 2
    assert mem.get_access() == "RO"
    assert mem.get_max_size() >= 13


@pytest.mark.parametrize(
    ("size", "n_bits", "expected_message"),
    [
        (0, 8, "cannot have fewer than 1 location"),
        (4, 0, "cannot have fewer than 1 bit"),
    ],
)
def test_memory_construction_repairs_non_positive_dimensions(
    size, n_bits, expected_message, caplog
):
    with caplog.at_level(logging.ERROR, logger="RegModel"):
        mem = uvm_mem("invalid_shape", size, n_bits)

    assert mem.get_size() >= 1
    assert mem.get_n_bits() >= 1
    assert expected_message in caplog.text


def test_memory_construction_repairs_unsupported_access(caplog):
    with caplog.at_level(logging.ERROR, logger="RegModel"):
        mem = uvm_mem("invalid_access", 4, 8, "write_once")

    assert mem.get_access() == "RW"
    assert "can only have 'RW' or 'RO' access" in caplog.text


def test_memory_configure_requires_a_parent():
    mem = uvm_mem("orphan", 4, 8)

    with pytest.raises(UVMFatalError, match="parent is None"):
        mem.configure(None)


def test_memory_configure_registers_with_block_and_name_lookup():
    block = uvm_reg_block("top")
    mem = uvm_mem("storage", 16, 32)

    mem.configure(block)

    assert mem.get_parent() is block
    assert mem.get_block() is block
    assert mem.get_full_name() == "top.storage"
    assert block.get_memories(uvm_hier_e.UVM_NO_HIER) == [mem]
    assert block.get_mem_by_name("storage") is mem
    assert mem._mam is None


def test_memory_enumeration_honors_hierarchy():
    top = uvm_reg_block("top")
    child = uvm_reg_block("child")
    child.configure(top)
    local_mem = uvm_mem("local", 2, 8)
    child_mem = uvm_mem("nested", 2, 8)
    local_mem.configure(top)
    child_mem.configure(child)

    assert top.get_memories(uvm_hier_e.UVM_NO_HIER) == [local_mem]
    assert top.get_memories() == [local_mem, child_mem]
    assert top.get_mem_by_name("nested") is child_mem


def test_lock_model_locks_memory():
    block = uvm_reg_block("top")
    mem = uvm_mem("storage", 4, 8)
    mem.configure(block)

    block.lock_model()

    assert block.is_locked()
    assert mem._locked


def test_configuring_memory_into_locked_block_is_rejected(caplog):
    block = uvm_reg_block("top")
    block.lock_model()
    mem = uvm_mem("late", 4, 8)

    with caplog.at_level(logging.ERROR, logger="RegModel"):
        mem.configure(block)

    assert block.get_memories() == []
    assert "Cannot add memory to a locked block model" in caplog.text


def test_configuring_same_memory_twice_is_rejected(caplog):
    block = uvm_reg_block("top")
    mem = uvm_mem("duplicate", 4, 8)
    mem.configure(block)

    with caplog.at_level(logging.ERROR, logger="RegModel"):
        mem.configure(block)

    assert block.get_memories() == [mem]
    assert "has already been registered" in caplog.text


def test_memory_constructor_errors_use_sv_uvm_reporting_when_enabled():
    root_logger = logging.getLogger("uvm")
    old_level = root_logger.level
    old_propagate = root_logger.propagate
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))

    set_sv_uvm_style_reporting_enabled(True)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)
    root_logger.propagate = False
    manager = uvm_report_server.create(
        policy=uvm_report_policy(max_quit_count=0),
        root_logger=root_logger,
    )

    try:
        mem = uvm_mem("invalid", 0, 0, "unsupported")

        assert mem.get_size() == 1
        assert mem.get_n_bits() == 1
        assert mem.get_access() == "RW"
        output = stream.getvalue()
        assert "[MEM_SIZE] Memory 'invalid' cannot have fewer than 1 location" in output
        assert "[MEM_WIDTH] Memory 'invalid' cannot have fewer than 1 bit" in output
        assert "[MEM_ACCESS] Memory 'invalid' can only have 'RW' or 'RO'" in output
        assert manager.get_stats().error_count == 3
    finally:
        manager.shutdown()
        manager.clear_counts()
        manager.catcher.clear()
        root_logger.removeHandler(handler)
        root_logger.setLevel(old_level)
        root_logger.propagate = old_propagate
        set_sv_uvm_style_reporting_enabled(False)
