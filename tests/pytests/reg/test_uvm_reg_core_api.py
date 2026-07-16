import asyncio
import io
import logging

import pytest

from pyuvm._reg.uvm_reg import uvm_reg
from pyuvm._reg.uvm_reg_backdoor import uvm_reg_backdoor
from pyuvm._reg.uvm_reg_block import uvm_reg_block
from pyuvm._reg.uvm_reg_field import uvm_reg_field
from pyuvm._reg.uvm_reg_item import uvm_reg_item
from pyuvm._reg.uvm_reg_model import (
    uvm_access_e,
    uvm_check_e,
    uvm_door_e,
    uvm_endianness_e,
    uvm_predict_e,
    uvm_status_e,
)
from pyuvm.uvm_reporting import set_sv_uvm_style_reporting_enabled
from pyuvm.uvm_reporting.uvm_report_server import uvm_report_server


class AsyncNoopLock:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def locked(self):
        return False

    def release(self):
        pass


class CoreApiReg(uvm_reg):
    def __init__(self, name="core_api_reg"):
        super().__init__(name, 16)
        self.low = uvm_reg_field("low")
        self.high = uvm_reg_field("high")
        self.low.configure(self, 8, 0, "RW", False, 0x12, True, False, False)
        self.high.configure(self, 8, 8, "RW", False, 0x34, True, False, False)


class SpyReg(CoreApiReg):
    def __init__(self, name="spy_reg"):
        super().__init__(name)
        self.write_items = []
        self.read_items = []
        self.read_value = 0
        self.next_status = uvm_status_e.UVM_IS_OK

    async def do_write(self, rw):
        self.write_items.append(rw)
        rw.set_value(rw.get_value() & self.get_mask())
        rw.set_status(self.next_status)
        if rw.get_status() != uvm_status_e.UVM_NOT_OK:
            self.do_predict(rw, uvm_predict_e.UVM_PREDICT_WRITE)

    async def do_read(self, rw):
        self.read_items.append(rw)
        rw.set_value(self.read_value)
        rw.set_status(self.next_status)


def build_reg(reg=None):
    block = uvm_reg_block("core_api_block")
    reg_map = block.create_map(
        "csr", 0x100, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True
    )
    reg = reg or CoreApiReg()
    reg.configure(block)
    reg_map.add_reg(reg, 0x20, "RW")
    block.lock_model()
    reg._atomic = AsyncNoopLock()
    return block, reg_map, reg


def test_register_helpers_reset_and_needs_update():
    _, reg_map, reg = build_reg()

    assert reg.get_field_by_name("low") is reg.low
    assert reg.get_field_by_name("missing") is None
    assert reg.get_offset() == 0x20
    assert reg.get_offset(reg_map) == 0x20
    assert reg.get_mask() == 0xFFFF

    assert reg.get_reset() == 0x3412
    reg.reset()
    assert reg.get_mirrored_value() == 0x3412
    assert not reg.needs_update()

    reg.low.set(0x13)
    assert reg.needs_update()

    reg.set_reset(0xABCD, "SOFT")
    assert reg.get_reset("SOFT") == 0xABCD
    assert reg.has_reset("SOFT")
    assert reg.has_reset("SOFT", delete=True)
    assert not reg.has_reset("SOFT")


def test_update_writes_desired_value_only_when_needed():
    _, reg_map, reg = build_reg(SpyReg())
    reg.reset()

    status = asyncio.run(reg.update(uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert status == uvm_status_e.UVM_IS_OK
    assert reg.write_items == []

    reg.set(0x5678)
    status = asyncio.run(reg.update(uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert status == uvm_status_e.UVM_IS_OK
    assert len(reg.write_items) == 1
    rw = reg.write_items[0]
    assert rw.get_kind() == uvm_access_e.UVM_WRITE
    assert rw.get_door() == uvm_door_e.UVM_FRONTDOOR
    assert rw.get_map() is reg_map
    assert rw.get_value() == 0x5678
    assert reg.get_mirrored_value() == 0x5678
    assert not reg.needs_update()


def test_mirror_reads_predicts_and_compares(caplog):
    _, reg_map, reg = build_reg(SpyReg())
    reg.reset()
    reg.read_value = 0x4567

    with caplog.at_level(logging.ERROR, logger="RegModel"):
        status = asyncio.run(
            reg.mirror(uvm_check_e.UVM_CHECK, uvm_door_e.UVM_FRONTDOOR, reg_map)
        )

    assert status == uvm_status_e.UVM_IS_OK
    assert "does not match mirrored value" in caplog.text
    assert reg.get_mirrored_value() == 0x4567
    assert len(reg.read_items) == 1
    assert reg.read_items[0].get_kind() == uvm_access_e.UVM_READ
    assert reg.read_items[0].get_door() == uvm_door_e.UVM_FRONTDOOR

    caplog.clear()
    with caplog.at_level(logging.ERROR, logger="RegModel"):
        status = asyncio.run(
            reg.mirror(uvm_check_e.UVM_CHECK, uvm_door_e.UVM_FRONTDOOR, reg_map)
        )

    assert status == uvm_status_e.UVM_IS_OK
    assert "does not match mirrored value" not in caplog.text


def test_do_check_uses_field_compare_mask(caplog):
    _, _, reg = build_reg()
    reg.reset()
    reg.high.set_compare(uvm_check_e.UVM_NO_CHECK)

    with caplog.at_level(logging.ERROR, logger="RegModel"):
        assert reg.do_check(0x3412, 0xAB12, None)

    assert "does not match mirrored value" not in caplog.text

    with caplog.at_level(logging.ERROR, logger="RegModel"):
        assert not reg.do_check(0x3412, 0x3413, None)

    assert "does not match mirrored value" in caplog.text

    caplog.clear()
    reg.low.set_volatility(True)

    with caplog.at_level(logging.ERROR, logger="RegModel"):
        assert reg.do_check(0x3412, 0x3413, None)

    assert "does not match mirrored value" not in caplog.text


def test_peek_and_poke_use_backdoor_items_and_predict():
    _, _, reg = build_reg(SpyReg())
    reg.reset()

    status = asyncio.run(reg.poke(0x1A2B3, kind="RTL"))

    assert status == uvm_status_e.UVM_IS_OK
    assert reg.write_items[-1].get_door() == uvm_door_e.UVM_BACKDOOR
    assert reg.write_items[-1].get_bd_kind() == "RTL"
    assert reg.write_items[-1].get_value() == 0xA2B3
    assert reg.get_mirrored_value() == 0xA2B3

    reg.read_value = 0x15555
    status, value = asyncio.run(reg.peek(kind="RTL"))

    assert status == uvm_status_e.UVM_IS_OK
    assert value == 0x5555
    assert reg.read_items[-1].get_door() == uvm_door_e.UVM_BACKDOOR
    assert reg.read_items[-1].get_bd_kind() == "RTL"
    assert reg.get_mirrored_value() == 0x5555


def test_frontdoor_and_backdoor_setters_getters():
    block, reg_map, reg = build_reg()
    frontdoor = object()
    block_backdoor = uvm_reg_backdoor("block_bkdr")
    reg_backdoor = uvm_reg_backdoor("reg_bkdr")

    reg.set_frontdoor(frontdoor, reg_map)
    block.set_backdoor(block_backdoor, fname="block.sv", lineno=42)

    assert reg.get_frontdoor(reg_map) is frontdoor
    assert reg.get_frontdoor() is frontdoor
    assert block.get_backdoor() is block_backdoor
    assert block_backdoor.fname == "block.sv"
    assert block_backdoor.lineno == 42
    assert reg.get_backdoor(inherited=False) is None
    assert reg.get_backdoor() is block_backdoor

    reg.set_backdoor(reg_backdoor, fname="reg.sv", lineno=84)

    assert reg.get_backdoor() is reg_backdoor
    assert reg.get_backdoor(inherited=False) is reg_backdoor
    assert reg_backdoor.fname == "reg.sv"
    assert reg_backdoor.lineno == 84


def test_unimplemented_hooks_raise():
    block, _, reg = build_reg()
    item = uvm_reg_item()
    backdoor = uvm_reg_backdoor("bkdr")

    with pytest.raises(NotImplementedError):
        reg.sample(0, 0, False, None)
    with pytest.raises(NotImplementedError):
        reg.sample_values()
    with pytest.raises(NotImplementedError):
        asyncio.run(reg.pre_write(item))
    with pytest.raises(NotImplementedError):
        asyncio.run(reg.post_write(item))
    with pytest.raises(NotImplementedError):
        asyncio.run(reg.pre_read(item))
    with pytest.raises(NotImplementedError):
        asyncio.run(reg.post_read(item))

    with pytest.raises(NotImplementedError):
        reg.low.pre_randomize()
    with pytest.raises(NotImplementedError):
        reg.low.post_randomize()
    with pytest.raises(NotImplementedError):
        asyncio.run(reg.low.pre_write(item))
    with pytest.raises(NotImplementedError):
        asyncio.run(reg.low.post_write(item))
    with pytest.raises(NotImplementedError):
        asyncio.run(reg.low.pre_read(item))
    with pytest.raises(NotImplementedError):
        asyncio.run(reg.low.post_read(item))

    with pytest.raises(NotImplementedError):
        block.sample(0, False, None)
    with pytest.raises(NotImplementedError):
        block._sample(0, False, None)
    with pytest.raises(NotImplementedError):
        block.sample_values()

    with pytest.raises(NotImplementedError):
        asyncio.run(backdoor.do_pre_read(item))
    with pytest.raises(NotImplementedError):
        asyncio.run(backdoor.do_post_read(item))
    with pytest.raises(NotImplementedError):
        asyncio.run(backdoor.do_pre_write(item))
    with pytest.raises(NotImplementedError):
        asyncio.run(backdoor.do_post_write(item))
    with pytest.raises(NotImplementedError):
        asyncio.run(backdoor.pre_read(item))
    with pytest.raises(NotImplementedError):
        asyncio.run(backdoor.post_read(item))
    with pytest.raises(NotImplementedError):
        asyncio.run(backdoor.pre_write(item))
    with pytest.raises(NotImplementedError):
        asyncio.run(backdoor.post_write(item))

    assert not backdoor.is_auto_updated(reg.low)


def test_new_diagnostics_use_sv_uvm_reporting_when_enabled():
    root_logger = logging.getLogger("uvm")
    old_level = root_logger.level
    old_propagate = root_logger.propagate
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setLevel(logging.NOTSET)
    handler.setFormatter(logging.Formatter("%(levelname)s:%(message)s"))

    set_sv_uvm_style_reporting_enabled(True)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)
    root_logger.propagate = False
    manager = uvm_report_server.create(root_logger=root_logger)

    try:
        _, reg_map, reg = build_reg(SpyReg())
        assert reg.get_field_by_name("missing") is None

        reg.reset()
        reg.read_value = 0x4567
        status = asyncio.run(
            reg.mirror(uvm_check_e.UVM_CHECK, uvm_door_e.UVM_FRONTDOOR, reg_map)
        )

        assert status == uvm_status_e.UVM_IS_OK
        output = stream.getvalue()
        assert "[REG_FIELD_LOOKUP] Unable to locate field 'missing'" in output
        assert "[REG_COMPARE] Register 'core_api_block.spy_reg'" in output
        assert manager.get_stats().warning_count == 1
        assert manager.get_stats().error_count == 1
    finally:
        manager.shutdown()
        manager.clear_counts()
        manager.catcher.clear()
        root_logger.removeHandler(handler)
        root_logger.setLevel(old_level)
        root_logger.propagate = old_propagate
        set_sv_uvm_style_reporting_enabled(False)
