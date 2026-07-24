import itertools
import logging

import pytest
from async_helpers import run_pytest_coro

from pyuvm._reg.uvm_reg import uvm_reg
from pyuvm._reg.uvm_reg_block import uvm_reg_block
from pyuvm._reg.uvm_reg_field import uvm_reg_field
from pyuvm._reg.uvm_reg_model import (
    uvm_access_e,
    uvm_check_e,
    uvm_door_e,
    uvm_endianness_e,
    uvm_predict_e,
    uvm_status_e,
)


class AsyncNoopLock:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def locked(self):
        return False

    def release(self):
        pass


class FieldAccessReg(uvm_reg):
    def __init__(self, name="field_access_reg"):
        super().__init__(name, 16)
        self.low = uvm_reg_field("low")
        self.high = uvm_reg_field("high")
        self.low.configure(self, 8, 0, "RW", False, 0x34, True, False, False)
        self.high.configure(self, 8, 8, "RW", False, 0x12, True, False, False)


class SpyFieldAccessReg(FieldAccessReg):
    def __init__(self, name="field_access_reg"):
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
        rw.set_value(self.read_value & self.get_mask())
        rw.set_status(self.next_status)


class PolicyReg(uvm_reg):
    def __init__(self, name, access, reset):
        super().__init__(name, 4)
        self.field = uvm_reg_field("field")
        self.field.configure(self, 4, 0, access, False, reset, True, False, False)


class MixedAccessReg(uvm_reg):
    def __init__(self, name="mixed_access_reg"):
        super().__init__(name, 12)
        self.target = uvm_reg_field("target")
        self.read_only = uvm_reg_field("read_only")
        self.write_zero_clear = uvm_reg_field("write_zero_clear")
        self.target.configure(self, 4, 0, "RW", False, 0, True, False, False)
        self.read_only.configure(self, 4, 4, "RO", False, 0xA, True, False, False)
        self.write_zero_clear.configure(
            self, 4, 8, "W0C", False, 0x5, True, False, False
        )


class SpyPolicyReg(PolicyReg):
    def __init__(self, name, access, reset):
        super().__init__(name, access, reset)
        self.write_items = []

    async def do_write(self, rw):
        self.write_items.append(rw)
        rw.set_value(rw.get_value() & self.get_mask())
        rw.set_status(uvm_status_e.UVM_IS_OK)
        self.do_predict(rw, uvm_predict_e.UVM_PREDICT_WRITE)


_policy_ids = itertools.count()


def build_reg(reg=None):
    block = uvm_reg_block("field_access_block")
    reg_map = block.create_map(
        "csr", 0x100, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True
    )
    reg = reg or FieldAccessReg()
    reg.configure(block)
    reg_map.add_reg(reg, 0x20, "RW")
    block.lock_model()
    reg._atomic = AsyncNoopLock()
    return block, reg_map, reg


def build_policy_field(access, reset=0xA):
    idx = next(_policy_ids)
    block = uvm_reg_block(f"policy_block_{idx}")
    reg_map = block.create_map("csr", 0, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True)
    reg = PolicyReg(f"policy_reg_{idx}", access, reset)
    reg.configure(block)
    reg_map.add_reg(reg, 0, "RW")
    block.lock_model()
    reg.reset()
    return reg_map, reg.field


def build_spy_policy_reg(access, reset=0xA):
    idx = next(_policy_ids)
    block = uvm_reg_block(f"policy_block_{idx}")
    reg_map = block.create_map("csr", 0, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True)
    reg = SpyPolicyReg(f"policy_reg_{idx}", access, reset)
    reg.configure(block)
    reg_map.add_reg(reg, 0, "RW")
    block.lock_model()
    reg._atomic = AsyncNoopLock()
    reg.reset()
    return reg_map, reg


def test_field_mask_and_register_packing_helpers():
    _, _, reg = build_reg()
    high = reg.high

    assert high.get_mask() == 0xFF
    assert high.get_register_mask() == 0xFF00
    assert high.extract_from_register(0xABCD) == 0xAB
    assert high.insert_into_register(0x1234, 0xCD) == 0xCD34
    assert high.insert_into_register(0x1234, 0x1AB) == 0xAB34


def test_field_write_preserves_sibling_fields_from_mirror():
    _, reg_map, reg = build_reg(SpyFieldAccessReg())
    reg.reset()
    reg.high.set(0x77)

    status = run_pytest_coro(reg.low.write(0x1AB, uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert status == uvm_status_e.UVM_IS_OK
    assert len(reg.write_items) == 1
    rw = reg.write_items[0]
    assert rw.get_kind() == uvm_access_e.UVM_WRITE
    assert rw.get_door() == uvm_door_e.UVM_FRONTDOOR
    assert rw.get_map() is reg_map
    assert rw.get_value() == 0x12AB
    assert reg.low.get_mirrored_value() == 0xAB
    assert reg.high.get_mirrored_value() == 0x12


def test_field_read_delegates_to_parent_and_extracts_field_value():
    _, reg_map, reg = build_reg(SpyFieldAccessReg())
    reg.read_value = 0xABCD

    status, value = run_pytest_coro(reg.high.read(uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert status == uvm_status_e.UVM_IS_OK
    assert value == 0xAB
    assert len(reg.read_items) == 1
    assert reg.read_items[0].get_kind() == uvm_access_e.UVM_READ
    assert reg.read_items[0].get_door() == uvm_door_e.UVM_FRONTDOOR
    assert reg.read_items[0].get_map() is reg_map


def test_field_poke_and_peek_use_parent_backdoor_path():
    _, _, reg = build_reg(SpyFieldAccessReg())
    reg.reset()
    reg.read_value = 0x1234

    status = run_pytest_coro(reg.low.poke(0x1FE, kind="RTL"))

    assert status == uvm_status_e.UVM_IS_OK
    assert reg.read_items[-1].get_door() == uvm_door_e.UVM_BACKDOOR
    assert reg.read_items[-1].get_bd_kind() == "RTL"
    assert reg.write_items[-1].get_door() == uvm_door_e.UVM_BACKDOOR
    assert reg.write_items[-1].get_bd_kind() == "RTL"
    assert reg.write_items[-1].get_value() == 0x12FE
    assert reg.get_mirrored_value() == 0x12FE

    reg.read_value = 0xAB89
    status, value = run_pytest_coro(reg.low.peek(kind="RTL"))

    assert status == uvm_status_e.UVM_IS_OK
    assert value == 0x89
    assert reg.read_items[-1].get_door() == uvm_door_e.UVM_BACKDOOR
    assert reg.read_items[-1].get_bd_kind() == "RTL"
    assert reg.get_mirrored_value() == 0xAB89


def test_field_mirror_reads_compares_and_predicts(caplog):
    _, reg_map, reg = build_reg(SpyFieldAccessReg())
    reg.reset()
    reg.low.set_compare(uvm_check_e.UVM_CHECK)
    reg.read_value = 0x12AA

    with caplog.at_level(logging.ERROR, logger="RegModel"):
        status = run_pytest_coro(
            reg.low.mirror(uvm_check_e.UVM_CHECK, uvm_door_e.UVM_FRONTDOOR, reg_map)
        )

    assert status == uvm_status_e.UVM_IS_OK
    assert "Register 'field_access_block.field_access_reg'" in caplog.text
    assert "does not match mirrored value" in caplog.text
    assert reg.low.get_mirrored_value() == 0xAA
    assert reg.high.get_mirrored_value() == 0x12


def test_field_set_masks_oversized_values():
    _, _, reg = build_reg()

    reg.low.set(0x1AB)

    assert reg.low.get() == 0xAB
    assert reg.low.value == 0xAB


def test_field_set_honors_one_shot_write_policy():
    _, field = build_policy_field("W1", reset=0)

    field.set(0x5)
    assert field.get() == 0x5

    field._written = True
    field.set(0xA)
    assert field.get() == 0x5


def test_field_parent_write_value_applies_sibling_access_policies():
    _, reg_map, reg = build_reg(MixedAccessReg())

    assert reg.target._get_parent_write_value(0x3, reg_map) == 0xF03


def test_field_poke_returns_parent_peek_error_without_write():
    _, _, reg = build_reg(SpyFieldAccessReg())
    reg.reset()
    reg.next_status = uvm_status_e.UVM_NOT_OK

    status = run_pytest_coro(reg.low.poke(0x12, kind="RTL"))

    assert status == uvm_status_e.UVM_NOT_OK
    assert len(reg.read_items) == 1
    assert reg.write_items == []


def test_field_individual_accessibility_defaults_to_false():
    _, reg_map, reg = build_reg()

    assert not reg.low.is_indv_accessible(uvm_door_e.UVM_FRONTDOOR, reg_map)


@pytest.mark.parametrize(
    "access",
    ["W1C", "W1S", "W0C", "W0S", "W1T", "W0T", "RC", "RS"],
)
def test_field_direct_prediction_bypasses_access_policy(access):
    reg_map, field = build_policy_field(access)

    assert field.predict(
        0x13,
        kind=uvm_predict_e.UVM_PREDICT_DIRECT,
        path=uvm_door_e.UVM_FRONTDOOR,
        map=reg_map,
    )
    assert field.get_mirrored_value() == 0x3
    assert field.get() == 0x3


@pytest.mark.parametrize(
    ("access", "write_value", "expected"),
    [
        ("W1C", 0x6, 0x8),
        ("W1S", 0x5, 0xF),
        ("W0C", 0x6, 0x2),
        ("W0S", 0x6, 0xB),
        ("W1T", 0x6, 0xC),
        ("W0T", 0x6, 0x3),
    ],
)
def test_field_write_prediction_applies_access_policy(access, write_value, expected):
    reg_map, field = build_policy_field(access)

    assert field.predict(
        write_value,
        kind=uvm_predict_e.UVM_PREDICT_WRITE,
        path=uvm_door_e.UVM_FRONTDOOR,
        map=reg_map,
    )
    assert field.get_mirrored_value() == expected
    assert field.get() == expected


@pytest.mark.parametrize(
    ("access", "expected"),
    [
        ("RC", 0x0),
        ("RS", 0xF),
    ],
)
def test_field_read_prediction_applies_access_policy(access, expected):
    reg_map, field = build_policy_field(access)

    assert field.predict(
        0x6,
        kind=uvm_predict_e.UVM_PREDICT_READ,
        path=uvm_door_e.UVM_FRONTDOOR,
        map=reg_map,
    )
    assert field.get_mirrored_value() == expected
    assert field.get() == expected


@pytest.mark.parametrize(
    ("access", "mirrored", "desired", "expected"),
    [
        ("RW", 0xA, 0x5, 0x5),
        ("W1C", 0xF, 0xC, 0x3),
        ("W1S", 0x0, 0x3, 0x3),
        ("W1T", 0xA, 0x6, 0xC),
        ("W0C", 0xF, 0xC, 0xC),
        ("W0S", 0x0, 0x3, 0xC),
        ("W0T", 0xA, 0x6, 0x3),
        ("W1CRS", 0xF, 0xC, 0x3),
        ("W0SRC", 0x0, 0x3, 0xC),
    ],
)
def test_field_update_value_matches_sv_xupdate(access, mirrored, desired, expected):
    _, field = build_policy_field(access, reset=mirrored)
    field._desired = desired

    assert field.get_update_value() == expected
    assert field._update() == expected


def test_field_update_value_uses_desired_value_for_custom_policy():
    access = f"CUSTOM_{next(_policy_ids)}"
    assert uvm_reg_field.define_access(access)
    _, field = build_policy_field(access, reset=0)
    field._desired = 0xB

    assert field.get_update_value() == 0xB


def test_field_direct_prediction_fails_when_parent_is_busy():
    _, _, reg = build_reg()

    reg._set_is_busy(True)

    assert not reg.low.predict(
        0x44,
        kind=uvm_predict_e.UVM_PREDICT_DIRECT,
        path=uvm_door_e.UVM_FRONTDOOR,
    )


def test_register_update_uses_field_update_value_for_w1c():
    reg_map, reg = build_spy_policy_reg("W1C", reset=0xF)

    reg.field.set(0x3)
    status = run_pytest_coro(reg.update(uvm_door_e.UVM_FRONTDOOR, reg_map))

    assert status == uvm_status_e.UVM_IS_OK
    assert reg.write_items[-1].get_value() == 0x3
    assert reg.field.get_mirrored_value() == 0xC
