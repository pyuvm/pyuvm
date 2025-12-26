"""
Main Packages for the entire RAL model
"""

import pytest

from pyuvm._reg.uvm_reg import uvm_reg
from pyuvm._reg.uvm_reg_block import uvm_reg_block
from pyuvm._reg.uvm_reg_file import uvm_reg_file
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
# TESTS UVM_REG
##############################################################################


@pytest.fixture
def model():
    class RegA(uvm_reg):
        def __init__(self, name="RegA"):
            super().__init__(name, 32)

    block = uvm_reg_block()
    map = block.create_map("map", 0x0, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, False)
    regfile = None
    reg = RegA()
    reg.configure(block, regfile, "")
    map.add_reg(reg, 0x8, "RW", False, None)
    block.lock_model()
    return block, map, regfile, reg


def test_get_name(model):
    _, _, _, reg = model
    assert reg.get_name() == "RegA"


def test_get_address(model):
    _, _, _, reg = model
    assert reg.get_address() == 0x8


def test_get_parent(model):
    block, _, _, reg = model
    assert reg.get_parent() is block
    assert reg.get_block() is not uvm_reg_block()


def test_get_block(model):
    block, _, _, reg = model
    assert reg.get_block() is block
    assert reg.get_block() is not uvm_reg_block()


@pytest.mark.xfail(reason="Not implemented", raises=NotImplementedError)
def test_get_regfile(model):
    _, _, regfile, reg = model
    assert reg.get_regfile() is regfile
    assert reg.get_regfile() is not uvm_reg_file()


def test_set_offset(model):
    _, map, _, reg = model
    reg.set_offset(map, 0xC, unmapped=False)
    assert reg.get_address() == 0xC
    info = map.get_reg_map_info(reg)
    assert not info.unmapped


def test_get_n_maps(model):
    _, _, _, reg = model
    assert reg.get_n_maps() == 1


def test_is_in_map(model):
    _, map, _, reg = model
    assert reg.is_in_map(map)
    assert not reg.is_in_map(uvm_reg_map("map"))
