import itertools
from pyuvm import *


def test_reg_block_get_name():
    block = uvm_reg_block('some_block')
    assert block.get_name() == 'some_block'


def test_reg_block_with_single_reg():
    block = uvm_reg_block()
    reg = uvm_reg()
    reg.configure(block)
    assert block.get_registers() == [reg]


def test_reg_block_with_multiple_regs():
    block = uvm_reg_block()
    reg0 = uvm_reg()
    reg0.configure(block)
    reg1 = uvm_reg()
    reg1.configure(block)
    assert block.get_registers() == [reg0, reg1]


def test_reg_map_get_name():
    map_with_explicit_name = uvm_reg_map('some_map')
    assert map_with_explicit_name.get_name() == 'some_map'
    map_with_implicit_name = uvm_reg_map()
    assert map_with_implicit_name.get_name() == 'uvm_reg_map'


def test_reg_map_configure():
    reg_map = uvm_reg_map()
    parent = uvm_reg_block()
    reg_map.configure(parent, 1024)
    assert reg_map.get_parent() == parent
    assert reg_map.get_base_addr() == 1024


def test_reg_map_with_single_reg():
    reg_map = uvm_reg_map()
    reg = uvm_reg()
    reg_map.add_reg(reg, 0)
    assert reg_map.get_registers() == [reg]


def test_reg_map_with_multiple_regs():
    reg_map = uvm_reg_map()
    reg0 = uvm_reg()
    reg_map.add_reg(reg0, 128)
    reg1 = uvm_reg()
    reg_map.add_reg(reg1, 256)
    assert reg_map.get_registers() == [reg0, reg1]
    assert reg_map.get_reg_by_offset(128) == reg0
    assert reg_map.get_reg_by_offset(256) == reg1


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


def test_simple_reg_model():
    """
    A more realistic register model based on the venerable UART 16550 design
    """
    class LineControlRegister(uvm_reg):
        def __init__(self, name):
            super().__init__(name)
            self.WLS = uvm_reg_field('WLS')
            self.WLS.configure(self, 2, 0, 'RW', 0, 0)
            self.STB = uvm_reg_field('STB')
            self.STB.configure(self, 1, 2, 'RW', 0, 0)
            self.PEN = uvm_reg_field('PEN')
            self.PEN.configure(self, 1, 3, 'RW', 0, 0)
            self.EPS = uvm_reg_field('EPS')
            self.EPS.configure(self, 1, 4, 'RW', 0, 0)

    class LineStatusRegister(uvm_reg):
        def __init__(self, name):
            super().__init__(name)
            self.DR = uvm_reg_field('DR')
            self.DR.configure(self, 1, 0, 'RW', 1, 0)
            self.OE = uvm_reg_field('OE')
            self.OE.configure(self, 1, 1, 'RW', 1, 0)
            self.PE = uvm_reg_field('PE')
            self.PE.configure(self, 1, 2, 'RW', 1, 0)
            self.FE = uvm_reg_field('FE')
            self.FE.configure(self, 1, 3, 'RW', 1, 0)

    class Regs(uvm_reg_block):
        def __init__(self, name):
            super().__init__(name)
            self.map = uvm_reg_map('map')
            self.map.configure(self, 0)
            self.LCR = LineControlRegister('LCR')
            self.LCR.configure(self)
            self.map.add_reg(self.LCR, int('0x100c', 0))
            self.LSR = LineStatusRegister('LSR')
            self.LSR.configure(self)
            self.map.add_reg(self.LSR, int('0x1014', 0))

    regs = Regs('regs')
    assert regs.get_name() == 'regs'
    assert regs.map.get_reg_by_offset(int('0x100c', 0)) == regs.LCR
    assert regs.map.get_reg_by_offset(int('0x1014', 0)) == regs.LSR

    LCR = regs.LCR
    assert LCR.get_name() == 'LCR'
    assert LCR.WLS.get_name() == 'WLS'
    assert LCR.STB.get_name() == 'STB'
    assert LCR.PEN.get_name() == 'PEN'
    assert LCR.EPS.get_name() == 'EPS'

    assert LCR.WLS.get_n_bits() == 2
    for field in LCR.get_fields():
        if field == LCR.WLS:
            continue
        assert field.get_n_bits() == 1

    def pairwise(iterable):
        "s -> (s0,s1), (s1,s2), (s2, s3), ..."
        a, b = itertools.tee(iterable)
        next(b, None)
        return zip(a, b)

    assert LCR.get_fields()[0].get_lsb_pos() == 0
    for prev_field, field in pairwise(LCR.get_fields()):
        assert field.get_lsb_pos() == prev_field.get_lsb_pos() + prev_field.get_n_bits()

    for field in LCR.get_fields():
        assert field.get_access() == 'RW'
        assert not field.is_volatile()
        assert field.get_reset() == 0

    LSR = regs.LSR
    assert LSR.DR.get_name() == 'DR'
    assert LSR.OE.get_name() == 'OE'
    assert LSR.PE.get_name() == 'PE'
    assert LSR.FE.get_name() == 'FE'

    for field in LSR.get_fields():
        assert field.get_n_bits() == 1
        assert field.get_access() == 'RW'
        assert field.is_volatile()
        assert field.get_reset() == 0

    assert LSR.get_fields()[0].get_lsb_pos() == 0
    for prev_field, field in pairwise(LSR.get_fields()):
        assert field.get_lsb_pos() == prev_field.get_lsb_pos() + prev_field.get_n_bits()
