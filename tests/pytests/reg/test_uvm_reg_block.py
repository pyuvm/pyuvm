# Main Packages for the entire RAL model
import itertools

import pytest

from pyuvm.reg.uvm_reg import uvm_reg
from pyuvm.reg.uvm_reg_block import uvm_reg_block
from pyuvm.reg.uvm_reg_field import uvm_reg_field
from pyuvm.reg.uvm_reg_map import uvm_reg_map
from pyuvm.reg.uvm_reg_model import uvm_endianness_e, uvm_hier_e, uvm_predict_e

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
execute it by using py.test -m ID_NAME
@pytest.mark.ID_NAME

Use this to give a specific test parameters to be used
@pytest.mark.parametrize("name1, name2",value_type_1, value_type_2)

If pip install pytest-sugar is ran then pytest is gonna likely execute a
bar progression while
running tests (especially if in Parallel)
"""

##############################################################################
# TESTS
##############################################################################


@pytest.fixture
def model():
    class ColorReg(uvm_reg):
        def __init__(self, name="color", reg_width=32):
            super().__init__(name, reg_width)
            self.blue = uvm_reg_field("blue")
            self.green = uvm_reg_field("green")
            self.red = uvm_reg_field("red")

            self.blue.configure(self, 8, 0, "RW", 0, 0, True, False, False)
            self.green.configure(self, 8, 8, "RW", 0, 0, True, False, False)
            self.red.configure(self, 8, 16, "RW", 0, 0, True, False, False)

    class ActionReg(uvm_reg):
        def __init__(self, name="action", reg_width=24):
            super().__init__(name, reg_width)
            self.start = uvm_reg_field("start")
            self.stop = uvm_reg_field("stop")
            self.wait = uvm_reg_field("wait")

            self.start.configure(self, 8, 0, "RO", False, 0, True, False, False)
            self.stop.configure(self, 8, 8, "RO", False, 0, True, False, False)
            self.wait.configure(self, 8, 16, "RO", False, 0, True, False, False)

    class Model(uvm_reg_block):
        def __init__(self, name="block"):
            super().__init__(name)

            color = ColorReg()
            color.configure(self)

            action = ActionReg()
            action.configure(self)

            map = self.create_map(
                "map", 0x0, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, False
            )
            map.add_reg(color, 0x0, "RW")
            map.add_reg(action, 0x4, "RO")

    model = Model()
    model.lock_model()
    return model


def test_get_name(model: uvm_reg_block):
    assert model.get_name() == "block"


def test_get_registers(model: uvm_reg_block):
    registers = model.get_registers()
    assert len(registers) == 2
    assert registers[0].get_name() == "color"
    assert registers[1].get_name() == "action"


def test_get_blocks(model):
    assert len(model.get_blocks()) == 0


def test_configure():
    block = uvm_reg_block("block")
    block.configure()
    assert block.get_name() == "block"
    assert block.get_parent() is None


def test_get_reg_by_name(model: uvm_reg_block):
    reg: uvm_reg = model.get_reg_by_name("color")
    assert reg.get_name() == "color"
    assert reg.get_address() == 0x0
    assert reg.get_rights() == "RW"
    assert reg.get_n_bits() == 32
    assert reg.get_n_bytes() == 4
    reg: uvm_reg = model.get_reg_by_name("action")
    assert reg.get_name() == "action"
    assert reg.get_address() == 0x4
    assert reg.get_rights() == "RO"
    assert reg.get_n_bits() == 24
    assert reg.get_n_bytes() == 3


def test_get_fields(model: uvm_reg_block):
    fields = model.get_fields()
    field_names = [field.get_name() for field in fields]
    assert "blue" in field_names
    assert "green" in field_names
    assert "red" in field_names
    assert "start" in field_names
    assert "stop" in field_names
    assert "wait" in field_names
    assert len(fields) == 6


def test_get_field_empty_reg():
    block = uvm_reg_block()
    reg = uvm_reg("reg", 32)
    reg.configure(block, None, "")
    assert block.get_fields() == list()
    assert block.get_registers() == [reg]


def test_reg_block_get_field_single_reg():
    class temp_reg(uvm_reg):
        def __init__(self, name="temp_reg", reg_width=32):
            super().__init__(name, reg_width)
            self.test_field_1 = uvm_reg_field("test_field_1")
            self.test_field_1.configure(self, 8, 0, "RW", 0, 0, True, False, False)

    block = uvm_reg_block()
    reg0 = temp_reg()
    reg0.configure(block)
    assert block.get_fields() == [reg0.test_field_1]


def test_reg_block_get_field_multiple_regs():
    # FIRST REGISTER
    class temp_reg_1(uvm_reg):
        def __init__(self, name="temp_reg_1", reg_width=32):
            super().__init__(name, reg_width)
            self.test_field_1 = uvm_reg_field("test_field_1")
            self.test_field_2 = uvm_reg_field("test_field_2")
            self.test_field_1.configure(self, 8, 0, "RW", 0, 0, True, False, False)
            self.test_field_2.configure(self, 16, 8, "RW", 0, 0, True, False, False)

    # SECOND REGISTER
    class temp_reg_2(uvm_reg):
        def __init__(self, name="temp_reg_2", reg_width=32):
            super().__init__(name, reg_width)
            self.test_field_3 = uvm_reg_field("test_field_3")
            self.test_field_4 = uvm_reg_field("test_field_4")
            self.test_field_5 = uvm_reg_field("test_field_5")
            self.test_field_3.configure(self, 8, 0, "RW", 0, 0, True, False, False)
            self.test_field_4.configure(self, 8, 8, "RW", 0, 0, True, False, False)
            self.test_field_5.configure(self, 8, 16, "RW", 0, 0, True, False, False)

    # START
    block = uvm_reg_block()
    reg0 = temp_reg_1()
    reg0.configure(block, None, "path")
    reg1 = temp_reg_2()
    reg1.configure(block, hdl_path="path")
    fields = block.get_fields()
    assert reg0.test_field_1 in fields
    assert reg0.test_field_2 in fields
    assert reg1.test_field_3 in fields
    assert reg1.test_field_4 in fields
    assert reg1.test_field_5 in fields
    assert len(fields) == 5


def test_reg_block_get_field_sub_reg_block():
    # FIRST REGISTER
    class temp_reg_1(uvm_reg):
        def __init__(self, name="temp_reg_1", reg_width=32):
            super().__init__(name, reg_width)
            self.test_field_1 = uvm_reg_field("test_field_1")
            self.test_field_2 = uvm_reg_field("test_field_2")
            self.test_field_1.configure(self, 8, 0, "RW", 0, 0, True, False, False)
            self.test_field_2.configure(self, 16, 8, "RW", 0, 0, True, False, False)

    # SECOND REGISTER
    class temp_reg_2(uvm_reg):
        def __init__(self, name="temp_reg_2", reg_width=32):
            super().__init__(name, reg_width)
            self.test_field_3 = uvm_reg_field("test_field_3")
            self.test_field_4 = uvm_reg_field("test_field_4")
            self.test_field_5 = uvm_reg_field("test_field_5")
            self.test_field_3.configure(self, 8, 0, "RW", 0, 0, True, False, False)
            self.test_field_4.configure(self, 8, 8, "RW", 0, 0, True, False, False)
            self.test_field_5.configure(self, 8, 16, "RW", 0, 0, True, False, False)

    # THIRD REGISTER
    class temp_reg_3(uvm_reg):
        def __init__(self, name="temp_reg_3", reg_width=32):
            super().__init__(name, reg_width)
            self.test_field_6 = uvm_reg_field("test_field_6")
            self.test_field_7 = uvm_reg_field("test_field_7")
            self.test_field_6.configure(self, 8, 0, "RW", 0, 0, True, False, False)
            self.test_field_7.configure(self, 8, 8, "RW", 0, 0, True, False, False)

    # SUB REG BLOCK
    class temp_blk_1(uvm_reg_block):
        def __init__(self, name="temp_blk_1"):
            super().__init__(name)
            self.def_map = self.create_map(
                "blk_1_map", 0x0, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN
            )
            self.test_reg_1 = temp_reg_3("test_reg_3")
            self.test_reg_1.configure(self)
            self.def_map.add_reg(self.test_reg_1, 0xC, "RW", False, None)

    # START
    block = uvm_reg_block()
    reg0 = temp_reg_1()
    reg0.configure(block)
    reg1 = temp_reg_2()
    reg1.configure(block)
    blk0 = temp_blk_1()
    blk0.configure(block, "path")

    assert block.get_fields() == [
        reg0.test_field_1,
        reg0.test_field_2,
        reg1.test_field_3,
        reg1.test_field_4,
        reg1.test_field_5,
        blk0.test_reg_1.test_field_6,
        blk0.test_reg_1.test_field_7,
    ]
    assert block.get_fields(hier=uvm_hier_e.UVM_NO_HIER) == [
        reg0.test_field_1,
        reg0.test_field_2,
        reg1.test_field_3,
        reg1.test_field_4,
        reg1.test_field_5,
    ]


def test_reg_map_get_name():
    map_with_explicit_name = uvm_reg_map("some_map")
    assert map_with_explicit_name.get_name() == "some_map"
    map_with_implicit_name = uvm_reg_map()
    assert map_with_implicit_name.get_name() == "uvm_reg_map"


def test_reg_map_configure():
    reg_map = uvm_reg_map()
    parent = uvm_reg_block()
    reg_map.configure(parent, 1024, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True)
    assert reg_map.get_parent() == parent
    assert reg_map.get_base_addr() == 1024


def test_reg_map_with_single_reg():
    reg_map = uvm_reg_map()
    reg = uvm_reg()
    reg_map.add_reg(reg, 0x0)
    assert reg_map.get_registers() == [reg]


def test_reg_map_with_multiple_regs():
    reg_block = uvm_reg_block("reg_block")
    reg_map = reg_block.create_map(
        "reg_map", 0x0, 1, uvm_endianness_e.UVM_LITTLE_ENDIAN, False
    )
    reg0 = uvm_reg("reg0", 8)
    reg1 = uvm_reg("reg1", 8)
    reg0.configure(reg_block)
    reg1.configure(reg_block)
    reg_map.add_reg(reg0, 0xF)
    reg_map.add_reg(reg1, 0xFF)
    reg_block.lock_model()

    assert reg_map.get_registers() == [reg0, reg1]
    assert reg0.get_address() == 0xF
    assert reg1.get_address() == 0xFF
    assert reg_map.get_reg_by_offset(0xF) == reg0
    assert reg_map.get_reg_by_offset(0xFF) == reg1


def test_reg_block_get_reg_by_name():
    # FIRST REGISTER
    class temp_reg_1(uvm_reg):
        def __init__(self, name="temp_reg_1", reg_width=32):
            super().__init__(name, reg_width)

    # SECOND REGISTER
    class temp_reg_2(uvm_reg):
        def __init__(self, name="temp_reg_2", reg_width=32):
            super().__init__(name, reg_width)

    # THIRD REGISTER
    class temp_reg_3(uvm_reg):
        def __init__(self, name="temp_reg_3", reg_width=32):
            super().__init__(name, reg_width)

    # FOURTH REGISTER
    class temp_reg_4(uvm_reg):
        def __init__(self, name="temp_reg_4", reg_width=32):
            super().__init__(name, reg_width)

    # FIRST SUB REG BLOCK
    class temp_blk_1(uvm_reg_block):
        def __init__(self, name="temp_blk_1"):
            super().__init__(name)
            self.def_map = uvm_reg_map("blk_1_map")
            self.def_map.configure(
                self, 0x0, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, False
            )
            self.reg0 = temp_reg_2()
            self.reg0.configure(self)
            self.reg1 = temp_reg_3()
            self.reg1.configure(self)
            self.def_map.add_reg(self.reg0, 0x8, "RW")
            self.def_map.add_reg(self.reg1, 0xC, "RW")

    # SECOND SUB REG BLOCK
    class temp_blk_2(uvm_reg_block):
        def __init__(self, name="temp_blk_2"):
            super().__init__(name)
            self.def_map = uvm_reg_map("blk_2_map")
            self.def_map.configure(
                self, 0x0, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, False
            )

            self.reg0 = temp_reg_4()
            self.reg0.configure(self)
            self.def_map.add_reg(self.reg0, 0x10, "RW")

            self.blk1 = temp_blk_1()
            self.blk1.configure(self)

    block = uvm_reg_block()
    reg0 = temp_reg_1()
    reg0.configure(block)  # 0x4
    blk0 = temp_blk_2()
    blk0.configure(block)

    print(type(block.get_reg_by_name("temp_reg_1")))
    assert block.get_reg_by_name("temp_reg_1") == reg0
    assert block.get_reg_by_name("temp_reg_2") == blk0.blk1.reg0
    assert block.get_reg_by_name("temp_reg_3") == blk0.blk1.reg1
    assert block.get_reg_by_name("temp_reg_4") == blk0.reg0
    assert block.get_reg_by_name("temp_reg_X") is None


def test_reg_block_get_field_by_name():
    # FIRST REGISTER
    class temp_reg_1(uvm_reg):
        def __init__(self, name="temp_reg_1", reg_width=32):
            super().__init__(name, reg_width)
            self.fieldA = uvm_reg_field("fieldA")
            self.fieldB = uvm_reg_field("fieldB")
            self.fieldA.configure(self, 8, 0, "RW", 0, 0, True, False, False)
            self.fieldB.configure(self, 16, 8, "RW", 0, 0, True, False, False)

    # SECOND REGISTER
    class temp_reg_2(uvm_reg):
        def __init__(self, name="temp_reg_2", reg_width=32):
            super().__init__(name, reg_width)
            self.fieldC = uvm_reg_field("fieldC")
            self.fieldD = uvm_reg_field("fieldD")
            self.fieldE = uvm_reg_field("fieldE")
            self.fieldC.configure(self, 8, 0, "RW", 0, 0, True, False, False)
            self.fieldD.configure(self, 8, 8, "RW", 0, 0, True, False, False)
            self.fieldE.configure(self, 8, 16, "RW", 0, 0, True, False, False)

    # THIRD REGISTER
    class temp_reg_3(uvm_reg):
        def __init__(self, name="temp_reg_3", reg_width=32):
            super().__init__(name, reg_width)
            self.fieldF = uvm_reg_field("fieldF")
            self.fieldG = uvm_reg_field("fieldG")
            self.fieldF.configure(self, 8, 0, "RW", 0, 0, True, False, False)
            self.fieldG.configure(self, 8, 8, "RW", 0, 0, True, False, False)

    # FOURTH REGISTER
    class temp_reg_4(uvm_reg):
        def __init__(self, name="temp_reg_4", reg_width=32):
            super().__init__(name, reg_width)
            self.fieldH = uvm_reg_field("fieldH")
            self.fieldI = uvm_reg_field("fieldI")
            self.fieldH.configure(self, 8, 0, "RW", 0, 0, True, False, False)
            self.fieldI.configure(self, 8, 8, "RW", 0, 0, True, False, False)

    # FIRST SUB REG BLOCK
    class temp_blk_1(uvm_reg_block):
        def __init__(self, name="temp_blk_1"):
            super().__init__(name)
            self.def_map = uvm_reg_map("blk_1_map")
            self.def_map.configure(
                self, 0x0, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True
            )
            self.reg0 = temp_reg_2("reg2")
            self.reg0.configure(self)
            self.reg1 = temp_reg_3("reg3")
            self.reg1.configure(self)
            self.def_map.add_reg(self.reg0, 0x8, "RW")
            self.def_map.add_reg(self.reg1, 0xC, "RW")

    # SECOND SUB REG BLOCK
    class temp_blk_2(uvm_reg_block):
        def __init__(self, name="temp_blk_2"):
            super().__init__(name)
            self.def_map = uvm_reg_map("blk_2_map")
            self.def_map.configure(
                self, 0x0, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, False
            )

            self.reg0 = temp_reg_4("reg4")
            self.reg0.configure(self)
            self.def_map.add_reg(self.reg0, 0x10, "RW")

            self.blk1 = temp_blk_1()
            self.blk1.configure(self)

    # START
    block = uvm_reg_block()
    reg0 = temp_reg_1()
    reg0.configure(block)
    blk0 = temp_blk_2()
    blk0.configure(block)
    assert block.get_field_by_name("fieldB") == reg0.fieldB
    assert block.get_field_by_name("fieldC") == blk0.blk1.reg0.fieldC
    assert block.get_field_by_name("fieldF") == blk0.blk1.reg1.fieldF
    assert block.get_field_by_name("fieldH") == blk0.reg0.fieldH
    assert block.get_field_by_name("fieldX") is None


##############################################################################
# TESTS UVM_REG
##############################################################################


def test_reg_get_name():
    reg = uvm_reg("some_reg")
    assert reg.get_name() == "some_reg"


def test_reg_configure():
    class temp_reg(uvm_reg):
        def __init__(self, name="temp_reg", reg_width=32):
            super().__init__(name, reg_width)

    # START
    reg = temp_reg()
    parent = uvm_reg_block()
    reg.configure(parent, None, "")
    assert reg.get_parent() == parent


def test_reg_with_single_field():
    reg = uvm_reg()
    field = uvm_reg_field()
    field.configure(reg, 8, 0, "RW", 0, 0, False, False, False)
    assert reg.get_fields() == [field]


def test_reg_with_multiple_fields():
    reg = uvm_reg()
    field0 = uvm_reg_field()
    field0.configure(reg, 8, 0, "RW", 0, 0, False, False, False)
    field1 = uvm_reg_field()
    field1.configure(reg, 8, 8, "RW", 0, 0, False, False, False)
    assert reg.get_fields() == [field0, field1]


def test_reg_field_get_name():
    field_with_explicit_name = uvm_reg_field("some_field")
    print(field_with_explicit_name.get_name())
    assert field_with_explicit_name.get_name() == "some_field"
    field_with_implicit_name = uvm_reg_field()
    assert field_with_implicit_name.get_name() == "uvm_reg_field"


def test_reg_field_configure():
    field = uvm_reg_field()
    parent = uvm_reg()
    field.configure(parent, 8, 16, "RW", True, 15, True, False, False)
    assert field.get_parent() == parent
    assert field.get_n_bits() == 8
    assert field.get_lsb_pos() == 16
    assert field.get_access() == "RW"
    assert field.is_volatile()
    assert field.get_reset() == 15


def test_reg_field_is_volatile():
    field = uvm_reg_field()
    field.configure(uvm_reg(), 8, 16, "RW", True, 15, False, False, False)
    assert field.is_volatile()
    field.configure(uvm_reg(), 8, 16, "RW", False, 15, False, False, False)
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
            self.WLS = uvm_reg_field("WLS")
            self.STB = uvm_reg_field("STB")
            self.PEN = uvm_reg_field("PEN")
            self.EPS = uvm_reg_field("EPS")
            self.WLS.configure(self, 2, 0, "RW", False, 0, False, False, False)
            self.STB.configure(self, 1, 2, "RW", False, 0, False, False, False)
            self.PEN.configure(self, 1, 3, "RW", False, 0, False, False, False)
            self.EPS.configure(self, 1, 4, "RW", False, 0, False, False, False)

    class LineStatusRegister(uvm_reg):
        def __init__(self, name="LineStatusRegister", reg_width=32):
            super().__init__(name, reg_width)
            self.DR = uvm_reg_field("DR")
            self.OE = uvm_reg_field("OE")
            self.PE = uvm_reg_field("PE")
            self.FE = uvm_reg_field("FE")
            self.DR.configure(self, 1, 0, "RW", True, 0, False, False, False)
            self.OE.configure(self, 1, 1, "RW", True, 0, False, False, False)
            self.PE.configure(self, 1, 2, "RW", True, 0, False, False, False)
            self.FE.configure(self, 1, 3, "RW", True, 0, False, False, False)

    class Regs(uvm_reg_block):
        def __init__(self, name):
            super().__init__(name)
            self.LCR = LineControlRegister("LCR")
            self.LSR = LineStatusRegister("LSR")
            self.LCR.configure(self, None, "")
            self.LSR.configure(self, None, "")
            self.map = uvm_reg_map("map")
            self.map.configure(self, 0, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, False)
            self.map.add_reg(self.LCR, 0x100C, "RW", False, None)
            self.map.add_reg(self.LSR, 0x1014, "RW", False, None)
            self._add_map(self.map)

    regs = Regs("regs")
    regs.lock_model()
    assert regs.get_name() == "regs"
    assert regs.map.get_reg_by_offset(0x100C) == regs.LCR
    assert regs.map.get_reg_by_offset(0x1014) == regs.LSR

    LCR = regs.LCR
    assert LCR.get_name() == "LCR"
    assert LCR.WLS.get_name() == "WLS"
    assert LCR.STB.get_name() == "STB"
    assert LCR.PEN.get_name() == "PEN"
    assert LCR.EPS.get_name() == "EPS"

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
        assert field.get_access() == "RW"
        assert not field.is_volatile()
        assert field.get_reset() == 0

    LSR = regs.LSR
    assert LSR.DR.get_name() == "DR"
    assert LSR.OE.get_name() == "OE"
    assert LSR.PE.get_name() == "PE"
    assert LSR.FE.get_name() == "FE"

    for field in LSR.get_fields():
        assert field.get_n_bits() == 1
        assert field.get_access() == "RW"
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
        print(field.get_mirrored_value())

    LSR.predict(12, kind=uvm_predict_e.UVM_PREDICT_READ)
    assert LSR.get_mirrored_value() == 12
