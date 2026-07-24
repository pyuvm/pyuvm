"""
Main Packages for the entire memory RAL model
"""

import pytest

from pyuvm._reg.uvm_mem import uvm_mem
from pyuvm._reg.uvm_reg_block import uvm_reg_block
from pyuvm._reg.uvm_reg_map import uvm_reg_map
from pyuvm._reg.uvm_reg_model import uvm_endianness_e

##############################################################################
# TIPS
##############################################################################
"""
Use this to execute the test which will not be counted into the entire
number of FAILING tests
@pytest.mark.xfail

Use this to just skip the execution of a specific test
@pytest.mark.skip

Use this to give a specific test method a name ID the execute it by
using py.test -m ID_NAME
@pytest.mark.ID_NAME

Use this to give a specific test parameters to be used
@pytest.mark.parametrize("name1, name2",value_type_1, value_type_2)

If pip install pytest-sugar is ran then pytest is gonna likely execute a bar
progression while
running tests (especially if in Parallel)
"""

##############################################################################
# TESTS UVM_MEM
##############################################################################


@pytest.fixture
def model():
    class MemA(uvm_mem):
        def __init__(self, name="MemA"):
            super().__init__(name, size=1024, n_bits=32)

    block = uvm_reg_block()
    map = block.create_map("map", 0x0, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, False)
    mem = MemA()
    mem.configure(block, "")
    map.add_mem(mem, 0x1000, "RW", False, None)
    block.lock_model()
    return block, map, mem


def test_get_name(model):
    _, _, mem = model
    assert mem.get_name() == "MemA"


def test_get_size(model):
    _, _, mem = model
    assert mem.get_size() == 1024


def test_get_n_bits(model):
    _, _, mem = model
    assert mem.get_n_bits() == 32


def test_get_n_bytes(model):
    _, _, mem = model
    assert mem.get_n_bytes() == 4


def test_get_access(model):
    _, _, mem = model
    assert mem.get_access() == "RW"


def test_get_parent(model):
    block, _, mem = model
    assert mem.get_parent() is block
    assert mem.get_block() is not uvm_reg_block()


def test_get_block(model):
    block, _, mem = model
    assert mem.get_block() is block


def test_get_address(model):
    _, _, mem = model
    assert mem.get_address() == 0x1000


def test_get_addresses(model):
    _, _, mem = model
    n_bytes, addresses = mem.get_addresses()
    assert n_bytes == 4
    assert addresses == [0x1000]


def test_get_addresses_with_offset(model):
    _, _, mem = model
    n_bytes, addresses = mem.get_addresses(offset=4)
    assert n_bytes == 4
    assert addresses == [0x1004]


def test_get_addresses_out_of_range(model):
    _, _, mem = model
    n_bytes, addresses = mem.get_addresses(offset=1024)
    assert n_bytes == -1
    assert addresses == []


def test_set_offset(model):
    _, map, mem = model
    mem.set_offset(map, 0x2000, unmapped=False)
    assert mem.get_address() == 0x2000


def test_get_n_maps(model):
    _, _, mem = model
    assert mem.get_n_maps() == 1


def test_is_in_map(model):
    _, map, mem = model
    assert mem.is_in_map(map)
    assert not mem.is_in_map(uvm_reg_map("other_map"))


def test_map_get_mem_by_offset(model):
    _, map, mem = model
    assert map.get_mem_by_offset(0x1000) is mem


def test_map_get_memories(model):
    _, map, mem = model
    assert map.get_memories() == [mem]


def test_block_get_memories(model):
    block, _, mem = model
    assert block.get_memories() == [mem]


def test_block_get_mem_by_name(model):
    block, _, mem = model
    assert block.get_mem_by_name("MemA") is mem


def test_add_memory_to_locked_block_fails(model):
    block, _, _ = model

    class MemB(uvm_mem):
        def __init__(self, name="MemB"):
            super().__init__(name, size=16, n_bits=8)

    mem_b = MemB()
    # The block is already locked; configure() should not raise, but the
    # memory must not be registered with the (locked) block.
    mem_b.configure(block, "")
    assert block.get_mem_by_name("MemB") is None
