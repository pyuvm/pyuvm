from pyuvm import *


def test_reg_block():
    assert uvm_reg_block()


def test_reg_map():
    assert uvm_reg_map()


def test_reg_get_name():
    reg = uvm_reg('some_reg')
    assert reg.get_name() == 'some_reg'


def test_reg_configure():
    reg = uvm_reg()
    parent = uvm_reg_block()
    reg.configure(parent)
    assert reg.get_parent() == parent


def test_reg_with_single_field():
    reg = uvm_reg()
    field = uvm_reg_field()
    field.configure(reg, 8, 0, 'RW', 0, 0)
    assert reg.get_fields() == [field]


def test_reg_with_multiple_fields():
    reg = uvm_reg()
    field0 = uvm_reg_field()
    field0.configure(reg, 8, 0, 'RW', 0, 0)
    field1 = uvm_reg_field()
    field1.configure(reg, 8, 0, 'RW', 0, 0)
    assert reg.get_fields() == [field0, field1]


def test_reg_field_get_name():
    field_with_explicit_name = uvm_reg_field('some_field')
    assert field_with_explicit_name.get_name() == 'some_field'
    field_with_implicit_name = uvm_reg_field()
    assert field_with_implicit_name.get_name() == 'uvm_reg_field'


def test_reg_field_configure():
    field = uvm_reg_field()
    parent = uvm_reg()
    field.configure(parent, 8, 16, 'RW', True, 15)
    assert field.get_parent() == parent
    assert field.get_n_bits() == 8
    assert field.get_lsb_pos() == 16
    assert field.get_access() == 'RW'
    assert field.is_volatile()
    assert field.get_reset() == 15


def test_reg_field_is_volatile():
    field = uvm_reg_field()
    field.configure(uvm_reg(), 8, 16, 'RW', True, 15)
    assert field.is_volatile()
    field.configure(uvm_reg(), 8, 16, 'RW', False, 15)
    assert not field.is_volatile()
