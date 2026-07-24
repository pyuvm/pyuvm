import logging

from async_helpers import run_pytest_coro

from pyuvm import (
    uvm_endianness_e,
    uvm_predict_e,
    uvm_reg,
    uvm_reg_block,
    uvm_reg_field,
)


class BytePairReg(uvm_reg):
    def __init__(self, name="byte_pair"):
        super().__init__(name, 16)
        self.high = uvm_reg_field("high")
        self.low = uvm_reg_field("low")

        # Configure out of order to prove the register stores fields by LSB.
        self.high.configure(self, 8, 8, "RW", False, 0, True, False, False)
        self.low.configure(self, 8, 0, "RW", False, 0, True, False, False)


def make_block_with_map(name, base_addr=0):
    block = uvm_reg_block(name)
    reg_map = block.create_map(
        "csr", base_addr, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True
    )
    return block, reg_map


def add_reg(block, reg_map, reg, offset, rights="RW"):
    reg.configure(block)
    reg_map.add_reg(reg, offset, rights)
    return reg


def test_block_map_construction_default_map_and_lock_model():
    block = uvm_reg_block("reg_model_construct")
    main_map = block.create_map(
        "main", 0x1000, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True
    )
    alias_map = block.create_map(
        "alias", 0x2000, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True
    )

    assert block.get_maps() == [main_map, alias_map]
    assert block.get_default_map() is main_map

    block.set_default_map(alias_map)
    assert block.get_default_map() is alias_map

    control = BytePairReg("control")
    control.configure(block)
    main_map.add_reg(control, 0x10, "RW")
    alias_map.add_reg(control, 0x4, "RO")

    assert not block.is_locked()
    block.lock_model()

    assert block.is_locked()
    assert control.get_default_map() is alias_map
    assert control.get_address() == 0x2004
    assert control.get_address(main_map) == 0x1010


def test_block_construction_after_asyncio_run_clears_event_loop():
    async def noop():
        return None

    run_pytest_coro(noop())

    block = uvm_reg_block("reg_model_after_asyncio_run")
    block.lock_model()

    run_pytest_coro(block.wait_for_lock())


def test_map_add_reg_info_and_address_lookup_after_lock():
    block, reg_map = make_block_with_map("reg_model_lookup", 0x80)
    control = add_reg(block, reg_map, BytePairReg("control"), 0x0, "RW")
    status = add_reg(block, reg_map, BytePairReg("status"), 0x8, "RO")

    block.lock_model()

    control_info = reg_map.get_reg_map_info(control)
    status_info = reg_map.get_reg_map_info(status)

    assert control_info.offset == 0x0
    assert control_info.rights == "RW"
    assert not control_info.unmapped
    assert control_info.addr == [0x80]
    assert control_info.is_initialized

    assert status_info.offset == 0x8
    assert status_info.rights == "RO"
    assert status_info.addr == [0x88]

    assert reg_map.get_reg_by_offset(0x80) is control
    assert reg_map.get_reg_by_offset(0x88) is status
    assert reg_map.get_reg_by_offset(0x84) is None

    n_bytes, addresses = control.get_addresses(reg_map)
    assert n_bytes == 4
    assert addresses == [0x80]
    assert control.get_address(reg_map) == 0x80


def test_field_order_overlap_reporting_and_register_packing(caplog):
    block, reg_map = make_block_with_map("reg_model_packing")
    packed = add_reg(block, reg_map, BytePairReg("packed"), 0x0)
    block.lock_model()

    assert packed.get_fields() == [packed.low, packed.high]

    packed.set(0xABCD)
    assert packed.low.get() == 0xCD
    assert packed.high.get() == 0xAB
    assert packed.get() == 0xABCD

    packed.low.set(0x12)
    packed.high.set(0x34)
    assert packed.get() == 0x3412

    overlap = uvm_reg("overlap", 16)
    first = uvm_reg_field("first")
    second = uvm_reg_field("second")

    with caplog.at_level(logging.ERROR, logger="RegModel"):
        first.configure(overlap, 8, 0, "RW", False, 0, True, False, False)
        second.configure(overlap, 8, 4, "RW", False, 0, True, False, False)

    assert "first overlaps field second in register overlap" in caplog.text
    assert overlap.get_fields() == [first, second]


def test_simple_rw_prediction_updates_field_and_register_mirrors():
    block, reg_map = make_block_with_map("reg_model_prediction")
    reg = add_reg(block, reg_map, BytePairReg("predictable"), 0x0)
    block.lock_model()

    reg.reset()
    assert reg.get_mirrored_value() == 0

    assert reg.predict(0xA55A, kind=uvm_predict_e.UVM_PREDICT_WRITE, map=reg_map)
    assert reg.low.get_mirrored_value() == 0x5A
    assert reg.high.get_mirrored_value() == 0xA5
    assert reg.get_mirrored_value() == 0xA55A
    assert reg.get() == 0xA55A

    assert reg.predict(0x00FF, kind=uvm_predict_e.UVM_PREDICT_READ, map=reg_map)
    assert reg.low.get_mirrored_value() == 0xFF
    assert reg.high.get_mirrored_value() == 0x00
    assert reg.get_mirrored_value() == 0x00FF
