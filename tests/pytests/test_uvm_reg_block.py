# Main Packages for the entire RAL model
import itertools
import pytest
from pyuvm.s27_uvm_reg_pkg import uvm_reg_block, uvm_reg, uvm_reg_map
from pyuvm.s27_uvm_reg_pkg import uvm_reg_field
from pyuvm.s24_uvm_reg_includes import access_e, predict_t
from pyuvm.s17_uvm_reg_enumerations import uvm_hier_e
from pyuvm.s17_uvm_reg_enumerations import uvm_predict_e

##############################################################################
# TIPS
##############################################################################
"""
Use this to execute the test which will not be counted into the entire number
 of FAILING tests
@pytest.mark.xfail

Use this to just skip the execution of a specific test
@pytest.mark.skip

Use this to give a specific test method a name ID the
exeucte it by using py.test -m ID_NAME
@pytest.mark.ID_NAME

Use this to give a specific test parameters to be used
@pytest.mark.parametrize("name1, name2",value_type_1, value_type_2)

If pip install pytest-sugar is ran then pytest is gonna likly execute a
bar progression while
running tests (expecially if in Parallel)
"""

##############################################################################
# TESTS
##############################################################################


@pytest.mark.reg_block_get_name
def test_reg_block_get_name():
    block = uvm_reg_block('some_block')
    assert block.get_name() == 'some_block'


@pytest.mark.reg_block_with_single_reg
def test_reg_block_with_single_reg():
    class temp_reg(uvm_reg):
        def __init__(self, name="temp_reg", reg_width=32):
            super().__init__(name, reg_width)

        def build(self):
            self._set_lock()
    # START
    block = uvm_reg_block()
    reg = temp_reg()
    reg.configure(block, "0x4", "")
    block.set_lock()
    assert block.get_registers() == [reg]


@pytest.mark.reg_block_with_multiple_regs
def test_reg_block_with_multiple_regs():
    class temp_reg(uvm_reg):
        def __init__(self, name="temp_reg", reg_width=32):
            super().__init__(name, reg_width)

        def build(self):
            self._set_lock()
    # START
    block = uvm_reg_block()
    reg0 = temp_reg()
    reg0.configure(block, "0x4", "")
    reg1 = temp_reg()
    reg1.configure(block, "0x8", "")
    block.set_lock()
    assert block.get_registers() == [reg0, reg1]


@pytest.mark.reg_block_with_sub_blocks
def test_reg_block_with_sub_blocks():
    # FIRST REGISTER
    class temp_reg_1(uvm_reg):
        def __init__(self, name="temp_reg_1", reg_width=32):
            super().__init__(name, reg_width)

        def build(self):
            self._set_lock()
    # SECOND REGISTER
    class temp_reg_2(uvm_reg):
        def __init__(self, name="temp_reg_2", reg_width=32):
            super().__init__(name, reg_width)

        def build(self):
            self._set_lock()
    # THIRD REGISTER
    class temp_reg_3(uvm_reg):
        def __init__(self, name="temp_reg_3", reg_width=32):
            super().__init__(name, reg_width)

        def build(self):
            self._set_lock()
    # SUB REG BLOCK
    class temp_blk_1(uvm_reg_block):
        def __init__(self, name="temp_blk_1"):
            super().__init__(name)
            self.def_map = uvm_reg_map("blk_1_map")
            self.def_map.configure(self, 0)

            self.reg0 = temp_reg_3("test_reg_3")
            self.reg0.configure(self, "0xC", "")
            self.def_map.add_reg(self.reg0, "0x0", 'RW')
    # START
    block = uvm_reg_block()
    reg0 = temp_reg_1()
    reg0.configure(block, "0x4", "")
    reg1 = temp_reg_2()
    reg1.configure(block, "0x8", "")
    blk0 = temp_blk_1()
    blk0.set_lock()
    block.add_block(blk0)
    block.set_lock()
    assert block.get_registers() == [reg0, reg1, blk0.reg0]
    assert block.get_registers(hier=uvm_hier_e.UVM_NO_HIER) == [reg0, reg1]


@pytest.mark.reg_block_get_field_empty_reg
def test_reg_block_get_field_empty_reg():
    class temp_reg(uvm_reg):
        def __init__(self, name="temp_reg", reg_width=32):
            super().__init__(name, reg_width)

        def build(self):
            self._set_lock()
    # START
    block = uvm_reg_block()
    reg0 = temp_reg()
    reg0.configure(block, "0x4", "")
    block.set_lock()
    assert block.get_fields() == []


@pytest.mark.reg_block_get_field_single_reg
def test_reg_block_get_field_single_reg():
    class temp_reg(uvm_reg):
        def __init__(self, name="temp_reg", reg_width=32):
            super().__init__(name, reg_width)
            self.test_field_1 = uvm_reg_field("test_field_1")

        def build(self):
            self.test_field_1.configure(self, 8, 0, 'RW', 0, 0)
            self._set_lock()
    # START
    block = uvm_reg_block()
    reg0 = temp_reg()
    reg0.configure(block, "0x4", "")
    block.set_lock()
    assert block.get_fields() == [reg0.test_field_1]


@pytest.mark.reg_block_get_field_multiple_regs
def test_reg_block_get_field_multiple_regs():
    # FIRST REGISTER
    class temp_reg_1(uvm_reg):
        def __init__(self, name="temp_reg_1", reg_width=32):
            super().__init__(name, reg_width)
            self.test_field_1 = uvm_reg_field("test_field_1")
            self.test_field_2 = uvm_reg_field("test_field_2")

        def build(self):
            self.test_field_1.configure(self, 8, 0, 'RW', 0, 0)
            self.test_field_2.configure(self, 16, 8, 'RW', 0, 0)
            self._set_lock()
    # SECOND REGISTER
    class temp_reg_2(uvm_reg):
        def __init__(self, name="temp_reg_2", reg_width=32):
            super().__init__(name, reg_width)
            self.test_field_3 = uvm_reg_field("test_field_3")
            self.test_field_4 = uvm_reg_field("test_field_4")
            self.test_field_5 = uvm_reg_field("test_field_5")

        def build(self):
            self.test_field_3.configure(self, 8, 0, 'RW', 0, 0)
            self.test_field_4.configure(self, 8, 8, 'RW', 0, 0)
            self.test_field_5.configure(self, 8, 16, 'RW', 0, 0)
            self._set_lock()
    # START
    block = uvm_reg_block()
    reg0 = temp_reg_1()
    reg0.configure(block, "0x4", "")
    reg1 = temp_reg_2()
    reg1.configure(block, "0x8", "")
    block.set_lock()
    assert block.get_fields() == [reg0.test_field_1, reg0.test_field_2, reg1.test_field_3, reg1.test_field_4, reg1.test_field_5]


@pytest.mark.reg_block_get_field_sub_reg_block
def test_reg_block_get_field_sub_reg_block():
    # FIRST REGISTER
    class temp_reg_1(uvm_reg):
        def __init__(self, name="temp_reg_1", reg_width=32):
            super().__init__(name, reg_width)
            self.test_field_1 = uvm_reg_field("test_field_1")
            self.test_field_2 = uvm_reg_field("test_field_2")

        def build(self):
            self.test_field_1.configure(self, 8, 0, 'RW', 0, 0)
            self.test_field_2.configure(self, 16, 8, 'RW', 0, 0)
            self._set_lock()
    # SECOND REGISTER
    class temp_reg_2(uvm_reg):
        def __init__(self, name="temp_reg_2", reg_width=32):
            super().__init__(name, reg_width)
            self.test_field_3 = uvm_reg_field("test_field_3")
            self.test_field_4 = uvm_reg_field("test_field_4")
            self.test_field_5 = uvm_reg_field("test_field_5")

        def build(self):
            self.test_field_3.configure(self, 8, 0, 'RW', 0, 0)
            self.test_field_4.configure(self, 8, 8, 'RW', 0, 0)
            self.test_field_5.configure(self, 8, 16, 'RW', 0, 0)
            self._set_lock()
    # THIRD REGISTER
    class temp_reg_3(uvm_reg):
        def __init__(self, name="temp_reg_3", reg_width=32):
            super().__init__(name, reg_width)
            self.test_field_6 = uvm_reg_field("test_field_6")
            self.test_field_7 = uvm_reg_field("test_field_7")

        def build(self):
            self.test_field_6.configure(self, 8, 0, 'RW', 0, 0)
            self.test_field_7.configure(self, 8, 8, 'RW', 0, 0)
            self._set_lock()
    # SUB REG BLOCK
    class temp_blk_1(uvm_reg_block):
        def __init__(self, name="temp_blk_1"):
            super().__init__(name)
            self.def_map = uvm_reg_map("blk_1_map")
            self.def_map.configure(self, 0)

            self.test_reg_1 = temp_reg_3("test_reg_3")
            self.test_reg_1.configure(self, "0xC", "")
            self.def_map.add_reg(self.test_reg_1, "0x0", 'RW')
    # START
    block = uvm_reg_block()
    reg0 = temp_reg_1()
    reg0.configure(block, "0x4", "")
    reg1 = temp_reg_2()
    reg1.configure(block, "0x8", "")
    blk0 = temp_blk_1()
    blk0.set_lock()
    block.add_block(blk0)
    block.set_lock()
    assert block.get_fields() == [reg0.test_field_1, reg0.test_field_2, reg1.test_field_3, reg1.test_field_4, reg1.test_field_5, blk0.test_reg_1.test_field_6, blk0.test_reg_1.test_field_7]
    assert block.get_fields(hier=uvm_hier_e.UVM_NO_HIER) == [reg0.test_field_1, reg0.test_field_2, reg1.test_field_3, reg1.test_field_4, reg1.test_field_5]


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
    assert reg_map.get_offset() == 1024


def test_reg_map_with_single_reg():
    reg_map = uvm_reg_map()
    reg = uvm_reg()
    reg_map.add_reg(reg, "0x0")
    assert reg_map.get_registers() == [reg]


def test_reg_map_with_multiple_regs():
    reg_map = uvm_reg_map()
    reg0 = uvm_reg()
    reg_map.add_reg(reg0, "0xf")
    reg1 = uvm_reg()
    reg_map.add_reg(reg1, "0xff")
    assert reg_map.get_registers() == [reg0, reg1]
    assert reg_map.get_reg_by_offset("0xf") == reg0
    assert reg_map.get_reg_by_offset("0xff") == reg1

@pytest.mark.reg_block_get_reg_by_name
def test_reg_block_get_reg_by_name():
    # FIRST REGISTER
    class temp_reg_1(uvm_reg):
        def __init__(self, name="temp_reg_1", reg_width=32):
            super().__init__(name, reg_width)

        def build(self):
            self._set_lock()
    # SECOND REGISTER
    class temp_reg_2(uvm_reg):
        def __init__(self, name="temp_reg_2", reg_width=32):
            super().__init__(name, reg_width)

        def build(self):
            self._set_lock()
    # THIRD REGISTER
    class temp_reg_3(uvm_reg):
        def __init__(self, name="temp_reg_3", reg_width=32):
            super().__init__(name, reg_width)

        def build(self):
            self._set_lock()
    # FOUTH REGISTER
    class temp_reg_4(uvm_reg):
        def __init__(self, name="temp_reg_4", reg_width=32):
            super().__init__(name, reg_width)

        def build(self):
            self._set_lock()
    # FIRST SUB REG BLOCK
    class temp_blk_1(uvm_reg_block):
        def __init__(self, name="temp_blk_1"):
            super().__init__(name)
            self.def_map = uvm_reg_map("blk_1_map")
            self.def_map.configure(self, 0)

            self.reg0 = temp_reg_2()
            self.reg0.configure(self, "0x8", "")
            self.reg1 = temp_reg_3()
            self.reg1.configure(self, "0xC", "")
            self.def_map.add_reg(self.reg0, "0x0", 'RW')
            self.def_map.add_reg(self.reg1, "0x0", 'RW')
    # SECOND SUB REG BLOCK
    class temp_blk_2(uvm_reg_block):
        def __init__(self, name="temp_blk_2"):
            super().__init__(name)
            self.def_map = uvm_reg_map("blk_2_map")
            self.def_map.configure(self, 0)

            self.reg0 = temp_reg_4()
            self.reg0.configure(self, "0x10", "")
            self.def_map.add_reg(self.reg0, "0x0", 'RW')

            self.blk1 = temp_blk_1()
            self.blk1.set_lock()
            self.add_block(self.blk1)
    block = uvm_reg_block()
    reg0 = temp_reg_1()
    reg0.configure(block, "0x4", "")
    blk0 = temp_blk_2()
    blk0.set_lock()
    block.add_block(blk0)
    block.set_lock()

    print(type(block.get_reg_by_name("temp_reg_1")))
    assert block.get_reg_by_name("temp_reg_1") == reg0
    assert block.get_reg_by_name("temp_reg_2") == blk0.blk1.reg0
    assert block.get_reg_by_name("temp_reg_3") == blk0.blk1.reg1
    assert block.get_reg_by_name("temp_reg_4") == blk0.reg0
    assert block.get_reg_by_name("temp_reg_X") == None

@pytest.mark.reg_block_get_field_by_name
def test_reg_block_get_field_by_name():
    # FIRST REGISTER
    class temp_reg_1(uvm_reg):
        def __init__(self, name="temp_reg_1", reg_width=32):
            super().__init__(name, reg_width)
            self.fieldA = uvm_reg_field("fieldA")
            self.fieldB = uvm_reg_field("fieldB")

        def build(self):
            self.fieldA.configure(self, 8, 0, 'RW', 0, 0)
            self.fieldB.configure(self, 16, 8, 'RW', 0, 0)
            self._set_lock()
    # SECOND REGISTER
    class temp_reg_2(uvm_reg):
        def __init__(self, name="temp_reg_2", reg_width=32):
            super().__init__(name, reg_width)
            self.fieldC = uvm_reg_field("fieldC")
            self.fieldD = uvm_reg_field("fieldD")
            self.fieldE = uvm_reg_field("fieldE")

        def build(self):
            self.fieldC.configure(self, 8, 0, 'RW', 0, 0)
            self.fieldD.configure(self, 8, 8, 'RW', 0, 0)
            self.fieldE.configure(self, 8, 16, 'RW', 0, 0)
            self._set_lock()
    # THIRD REGISTER
    class temp_reg_3(uvm_reg):
        def __init__(self, name="temp_reg_3", reg_width=32):
            super().__init__(name, reg_width)
            self.fieldF = uvm_reg_field("fieldF")
            self.fieldG = uvm_reg_field("fieldG")

        def build(self):
            self.fieldF.configure(self, 8, 0, 'RW', 0, 0)
            self.fieldG.configure(self, 8, 8, 'RW', 0, 0)
            self._set_lock()
    # FOUTH REGISTER
    class temp_reg_4(uvm_reg):
        def __init__(self, name="temp_reg_4", reg_width=32):
            super().__init__(name, reg_width)
            self.fieldH = uvm_reg_field("fieldH")
            self.fieldI = uvm_reg_field("fieldI")

        def build(self):
            self.fieldH.configure(self, 8, 0, 'RW', 0, 0)
            self.fieldI.configure(self, 8, 8, 'RW', 0, 0)
            self._set_lock()
    # FIRST SUB REG BLOCK
    class temp_blk_1(uvm_reg_block):
        def __init__(self, name="temp_blk_1"):
            super().__init__(name)
            self.def_map = uvm_reg_map("blk_1_map")
            self.def_map.configure(self, 0)

            self.reg0 = temp_reg_2("reg2")
            self.reg0.configure(self, "0x8", "")
            self.reg1 = temp_reg_3("reg3")
            self.reg1.configure(self, "0xC", "")
            self.def_map.add_reg(self.reg0, "0x0", 'RW')
            self.def_map.add_reg(self.reg1, "0x0", 'RW')
    # SECOND SUB REG BLOCK
    class temp_blk_2(uvm_reg_block):
        def __init__(self, name="temp_blk_2"):
            super().__init__(name)
            self.def_map = uvm_reg_map("blk_2_map")
            self.def_map.configure(self, 0)

            self.reg0 = temp_reg_4("reg4")
            self.reg0.configure(self, "0x10", "")
            self.def_map.add_reg(self.reg0, "0x0", 'RW')

            self.blk1 = temp_blk_1()
            self.blk1.set_lock()
            self.add_block(self.blk1)
    # START
    block = uvm_reg_block()
    reg0 = temp_reg_1()
    reg0.configure(block, "0x4", "")
    blk0 = temp_blk_2()
    blk0.set_lock()
    block.add_block(blk0)
    block.set_lock()
    assert block.get_field_by_name("fieldB") == reg0.fieldB
    assert block.get_field_by_name("fieldC") == blk0.blk1.reg0.fieldC
    assert block.get_field_by_name("fieldF") == blk0.blk1.reg1.fieldF
    assert block.get_field_by_name("fieldH") == blk0.reg0.fieldH
    assert block.get_field_by_name("fieldX") == None

##############################################################################
# TESTS UVM_REG
##############################################################################


def test_reg_get_name():
    reg = uvm_reg('some_reg')
    assert reg.get_name() == 'some_reg'


def test_reg_configure():
    class temp_reg(uvm_reg):
        def __init__(self, name="temp_reg", reg_width=32):
            super().__init__(name, reg_width)

        def build(self):
            self._set_lock()
    # START
    reg = temp_reg()
    parent = uvm_reg_block()
    reg.configure(parent, "0x4", "")
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
    field1.configure(reg, 8, 8, 'RW', 0, 0)
    assert reg.get_fields() == [field0, field1]


def test_reg_field_get_name():
    field_with_explicit_name = uvm_reg_field("some_field")
    print(field_with_explicit_name.get_name())
    assert field_with_explicit_name.get_name() == "some_field"
    field_with_implicit_name = uvm_reg_field()
    assert field_with_implicit_name.get_name() == 'uvm_reg_field'


def test_reg_field_configure():
    field = uvm_reg_field()
    parent = uvm_reg()
    field.configure(parent, 8, 16, 'RW', True, 15)
    field.field_lock()
    assert field.get_parent() == parent
    assert field.get_n_bits() == 8
    assert field.get_lsb_pos() == 16
    assert field.get_access() == 'RW'
    assert field.is_volatile()
    assert field.get_reset() == 15


def test_reg_field_is_volatile():
    field = uvm_reg_field()
    field.configure(uvm_reg(), 8, 16, 'RW', True, 15)
    field.field_lock()
    assert field.is_volatile()
    field.configure(uvm_reg(), 8, 16, 'RW', False, 15)
    assert not field.is_volatile()

##############################################################################
# TESTS ENTIRE RAL
##############################################################################


def test_simple_reg_model():
    """
    A more realistic register model based on the venerable UART 16550 design
    """
    class LineControlRegister(uvm_reg):
        def __init__(self, name="LineControlRegister", reg_width=32):
            super().__init__(name, reg_width)
            self.WLS = uvm_reg_field('WLS')
            self.STB = uvm_reg_field('STB')
            self.PEN = uvm_reg_field('PEN')
            self.EPS = uvm_reg_field('EPS')

        def build(self):
            self.WLS.configure(self, 2, 0, 'RW', 0, 0)
            self.STB.configure(self, 1, 2, 'RW', 0, 0)
            self.PEN.configure(self, 1, 3, 'RW', 0, 0)
            self.EPS.configure(self, 1, 4, 'RW', 0, 0)
            self._set_lock()

    class LineStatusRegister(uvm_reg):
        def __init__(self, name="LineStatusRegister", reg_width=32):
            super().__init__(name, reg_width)
            self.DR = uvm_reg_field('DR')
            self.OE = uvm_reg_field('OE')
            self.PE = uvm_reg_field('PE')
            self.FE = uvm_reg_field('FE')

        def build(self):
            self.DR.configure(self, 1, 0, 'RW', 1, 0)
            self.OE.configure(self, 1, 1, 'RW', 1, 0)
            self.PE.configure(self, 1, 2, 'RW', 1, 0)
            self.FE.configure(self, 1, 3, 'RW', 1, 0)
            self._set_lock()

    class Regs(uvm_reg_block):
        def __init__(self, name):
            super().__init__(name)
            self.map = uvm_reg_map('map')
            self.map.configure(self, 0)
            self.LCR = LineControlRegister('LCR')
            self.LCR.configure(self, "0x100c", "")
            self.map.add_reg(self.LCR, "0x0")
            self.LSR = LineStatusRegister('LSR')
            self.LSR.configure(self, "0x1014", "")
            self.map.add_reg(self.LSR, "0x0")

    regs = Regs('regs')
    assert regs.get_name() == 'regs'
    assert regs.map.get_reg_by_offset("0x100c") == regs.LCR
    assert regs.map.get_reg_by_offset("0x1014") == regs.LSR

    LCR = regs.LCR
    assert LCR.get_name() == 'LCR'
    assert LCR.WLS.get_name() == 'WLS'
    assert LCR.STB.get_name() == 'STB'
    assert LCR.PEN.get_name() == 'PEN'
    assert LCR.EPS.get_name() == 'EPS'

    assert LCR.WLS.get_n_bits() == 2
    for field in [field for field in LCR.get_fields() if field != LCR.WLS]:
        assert field.get_n_bits() == 1

    def pairwise(iterable):
        """s -> (s0,s1), (s1,s2), (s2, s3), ..."""
        a, b = itertools.tee(iterable)
        next(b, None)
        return zip(a, b)

    def get_msb_pos(field):
        return field.get_lsb_pos() + field.get_n_bits() - 1

    def are_adjacent(prev_field, field):
        return field.get_lsb_pos() == get_msb_pos(prev_field) + 1

    assert LCR.get_fields()[0].get_lsb_pos() == 0
    for prev_field, field in pairwise(LCR.get_fields()):
        assert are_adjacent(prev_field, field)

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
        assert are_adjacent(prev_field, field)

    LSR.reset()
    assert LSR.get_mirrored_value() == 0
    LSR.predict(12, kind=uvm_predict_e.UVM_PREDICT_WRITE)
    assert LSR.get_mirrored_value() == 12
    for field in LSR.get_fields():
        print(field.get_value())

    LSR.predict(12, kind=uvm_predict_e.UVM_PREDICT_READ)
    assert LSR.get_mirrored_value() == 12
