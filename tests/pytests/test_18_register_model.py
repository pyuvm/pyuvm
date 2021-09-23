from pyuvm import *


def test_reg_block():
    assert uvm_reg_block()


def test_reg_map():
    assert uvm_reg_map()


def test_reg():
    assert uvm_reg()


def test_reg_field_configure():
    field = uvm_reg_field()
    parent = uvm_reg()
    field.configure(parent, 8, 16, 'RW', True)
    assert field.get_parent() == parent
    assert field.get_n_bits() == 8
    assert field.get_lsb_pos() == 16
    assert field.get_access() == 'RW'
    assert field.is_volatile()


def test_reg_field_is_volatile():
    field = uvm_reg_field()
    field.configure(uvm_reg(), 8, 16, 'RW', True)
    assert field.is_volatile()
    field.configure(uvm_reg(), 8, 16, 'RW', False)
    assert not field.is_volatile()
