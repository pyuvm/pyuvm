'''
Main Packages for the entire RAL model
'''
import pytest
from pyuvm.s17_uvm_reg_enumerations import uvm_predict_e
from pyuvm.s27_uvm_reg_pkg import uvm_reg_field, uvm_reg, uvm_reg_block
from pyuvm.s24_uvm_reg_includes import access_e, predict_t
from typing import List

##############################################################################
# TIPS
##############################################################################
"""
Use this to execute the test which will not be counted into the entire
number of FAILING tests
@pytest.mark.xfail

Use this to just skip the execution of a specific test
@pytest.mark.skip

Use this to give a specific test method a name ID the exeucte it by
using py.test -m ID_NAME
@pytest.mark.ID_NAME

Use this to give a specific test parameters to be used
@pytest.mark.parametrize("name1, name2",value_type_1, value_type_2)

If pip install pytest-sugar is ran then pytest is gonna likly execute a bar
progression while
running tests (expecially if in Parallel)
"""

##############################################################################
# TESTS UVM_REG
##############################################################################


@pytest.mark.test_reg_get_name
def test_reg_get_name():
    for elem in range(1,32):
        reg = uvm_reg(('some_reg_'+str(elem)), elem)
        assert reg.get_name() == ('some_reg_'+str(elem)), "Name mismatch: expected {} got: {}".format(('some_reg_'+str(elem)), reg.get_name())
        assert reg.get_reg_size() == elem, "Register size mismatch: expected {} got: {}".format(elem, reg.get_reg_size())
        reg.check_err_list()


@pytest.mark.test_reg_configure
def test_reg_configure():
    class temp_reg(uvm_reg):
        def __init__(self, name="temp_reg", reg_width=32):
            super().__init__(name, reg_width)

        def build(self):
            self._set_lock()
    # START
    reg = temp_reg()
    parent = uvm_reg_block()
    parent.set_lock()
    reg.configure(parent, "0x4", "", False, False)
    print(f"reg: {reg}")
    print(f"parent: {parent}")
    assert reg.get_parent() == parent, f"Mismatch on get parent: expected {type(parent)} got: {type(reg.get_parent)}"
    assert reg.get_address() == "0x4", f"Mismacth on get address: expected 0x4 got {reg.get_address()}"


@pytest.mark.test_reg_with_single_field
def test_reg_with_single_field():
    class my_reg(uvm_reg):
        def __init__(self, name="uvm_reg", reg_width=32):
            super().__init__(name, reg_width)
            self.myfield_1 = uvm_reg_field("myfield_1")

        def build(self):
            self.myfield_1.configure(myreg, 16, 0, "RW", False, 10)
            self._set_lock()

    myreg = my_reg("myreg", 32)
    myreg.build()
    myreg.reset()
    assert myreg.get_fields() == [myreg.myfield_1]
    myreg.check_err_list()


@pytest.mark.test_reg_with_multiple_fields
def test_reg_with_multiple_fields():
    class my_reg(uvm_reg):
        def __init__(self, name="uvm_reg", reg_width=32):
            super().__init__(name, reg_width)
            self.myfield_1 = uvm_reg_field("myfield_1")
            self.myfield_2 = uvm_reg_field("myfield_2")

        def build(self):
            self.myfield_1.configure(myreg, 16, 0, "RW", False, 10)
            self.myfield_2.configure(myreg, 16, 16, "RW", False, 20)
            self._set_lock()

    myreg = my_reg("myreg", 32)
    myreg.build()
    assert myreg.get_fields() == [myreg.myfield_1, myreg.myfield_2]
    myreg.check_err_list()


@pytest.mark.test_reg_with_multiple_felds_reset
def test_reg_with_multiple_felds_reset():
    class my_reg(uvm_reg):
        def __init__(self, name="uvm_reg", reg_width=32):
            super().__init__(name, reg_width)
            self.myfield_1 = uvm_reg_field("myfield_1")
            self.myfield_2 = uvm_reg_field("myfield_2")

        def build(self):
            # int('0x0f',16)
            self.myfield_1.configure(self, 16, 0, "RW", False, int('0x0f', 16))
            self.myfield_2.configure(self, 16, 16, "RW", False, int('0x0f', 16))
            self._set_lock()
            print("calling build")

    myreg = my_reg("myreg",32)
    myreg.build()
    for f in myreg.get_fields():
        print(f"{f}")
    myreg.reset()
    assert myreg.get_mirrored_value() == int('0xf000f', 16)
    myreg.check_err_list()


@pytest.mark.test_reg_with_multiple_fields_get_mirrored_value
def test_reg_with_multiple_fields_get_mirrored_value():
    class my_reg(uvm_reg):
        def __init__(self, name="uvm_reg", reg_width=32):
            super().__init__(name, reg_width)
            self.myfield_1 = uvm_reg_field("myfield_1")
            self.myfield_2 = uvm_reg_field("myfield_2")

        def build(self):
            self.myfield_1.configure(self, 16, 0, "RW", False, int('0xf', 16))
            self.myfield_2.configure(self, 16, 16, "RW", False, int('0xf', 16))
            self._set_lock()

    myreg = my_reg("myreg", 32)
    myreg.build()
    myreg.reset()
    myreg.predict(value=int('0x0f00f0', 16), kind=uvm_predict_e.UVM_PREDICT_WRITE)
    assert myreg.get_mirrored_value() == int('0x0f00f0', 16)
    myreg.reset()
    assert myreg.get_mirrored_value() == int('0xf000f', 16)
    myreg.check_err_list()


@pytest.mark.test_reg_with_multiple_fields_get_desired_value
def test_reg_with_multiple_fields_get_desired_value():
    class my_reg(uvm_reg):
        def __init__(self, name="uvm_reg", reg_width=32):
            super().__init__(name, reg_width)
            self.myfield_1 = uvm_reg_field("myfield_1")
            self.myfield_2 = uvm_reg_field("myfield_2")

        def build(self):
            self.myfield_1.configure(self, 16, 0, "RW", False, int('0xf', 16))
            self.myfield_2.configure(self, 16, 16, "RW", False, int('0xf', 16))
            self._set_lock()

    myreg = my_reg("myreg", 32)
    myreg.build()
    myreg.reset()
    myreg.set_desired(int('0xf0f0f0f0', 16))
    assert myreg.get_desired() == int('0xf0f0f0f0', 16)


def make_expected_value(reg: uvm_reg, policy_list: List[str]) -> int:
        field_list: List[uvm_reg_field] = reg.get_fields()
        pos = 0
        exp_val = 0
        for field in field_list:
            field_lsb_pos = field.get_lsb_pos()
            while pos != field_lsb_pos:
                pos += 1
            field_policy = field.get_access()
            field_size   = field.get_n_bits()
            if field_policy in policy_list:
                exp_val |= ((1 << field_size) - 1) << pos
                pos += field_size
        return exp_val


def predict_reg(reg: uvm_reg, predict_val: int = 0xFFFF_FFFF):
        reg.reset()
        assert reg.get_mirrored_value() == 0
        reg.predict(predict_val, kind=uvm_predict_e.UVM_PREDICT_WRITE)
        assert reg.get_mirrored_value() == make_expected_value(reg, ["RW", "WO"])
        reg.predict(predict_val, kind=uvm_predict_e.UVM_PREDICT_READ)
        assert reg.get_mirrored_value() == make_expected_value(reg, ["RW", "RO"])
        reg.predict(predict_val, kind=uvm_predict_e.UVM_PREDICT_DIRECT)
        assert reg.get_mirrored_value() == make_expected_value(reg, ["RW", "WO", "RO"])


@pytest.mark.test_reg_simple_predict
def test_reg_simple_predict():
    """
    Test registers with different simple access types like a RW/RO/WO
    """
    class reg0(uvm_reg):
        def __init__(self, name="reg0", reg_width=32):
            super().__init__(name, reg_width)
            self.field1 = uvm_reg_field('field1')
            self.field2 = uvm_reg_field('field2')
            self.field3 = uvm_reg_field('field3')
            self.field4 = uvm_reg_field('field4')

        def build(self):
            self.field1.configure(self, 8, 0,  'RW', 0, 0)
            self.field2.configure(self, 8, 8,  'RO', 0, 0)
            self.field3.configure(self, 8, 16, 'WO', 0, 0)
            self.field4.configure(self, 8, 24, 'RW', 0, 0)
            self._set_lock()

    class reg1(uvm_reg):
        def __init__(self, name="reg1", reg_width=32):
            super().__init__(name, reg_width)
            self.field1 = uvm_reg_field('field1')
            self.field2 = uvm_reg_field('field2')
            self.field3 = uvm_reg_field('field3')
            self.field4 = uvm_reg_field('field4')
            self.field5 = uvm_reg_field('field5')
            self.field6 = uvm_reg_field('field6')
            self.field7 = uvm_reg_field('field7')
            self.field8 = uvm_reg_field('field8')

        def build(self):
            self.field1.configure(self, 4, 0,  'RW', 0, 0)
            self.field2.configure(self, 4, 4,  'RW', 0, 0)
            self.field3.configure(self, 4, 8,  'RO', 0, 0)
            self.field4.configure(self, 4, 12, 'WO', 0, 0)
            self.field5.configure(self, 4, 16, 'RW', 0, 0)
            self.field6.configure(self, 4, 20, 'WO', 0, 0)
            self.field7.configure(self, 4, 24, 'RO', 0, 0)
            self.field8.configure(self, 4, 28, 'RW', 0, 0)
            self._set_lock()

    register_0 = reg0('reg0')
    assert register_0.get_name() == 'reg0'
    assert register_0.field1.get_name() == 'field1'
    assert register_0.field2.get_name() == 'field2'
    assert register_0.field3.get_name() == 'field3'
    assert register_0.field4.get_name() == 'field4'

    register_1 = reg1('reg1')
    assert register_1.get_name() == 'reg1'
    assert register_1.field1.get_name() == 'field1'
    assert register_1.field2.get_name() == 'field2'
    assert register_1.field3.get_name() == 'field3'
    assert register_1.field4.get_name() == 'field4'
    assert register_1.field5.get_name() == 'field5'
    assert register_1.field6.get_name() == 'field6'
    assert register_1.field7.get_name() == 'field7'
    assert register_1.field8.get_name() == 'field8'

    predict_reg(register_0)
    predict_reg(register_1)


@pytest.mark.test_reg_predict_edge_cases
def test_reg_predict_edge_cases():
    """
    Test register predict with edge cases
    """
    class Reg0(uvm_reg):
        def __init__(self, name="reg0", reg_width=32):
            super().__init__(name, reg_width)
            self.field = uvm_reg_field('field')

        def build(self):
            self.field.configure(self, 32, 0, 'RW', 0, 0)
            self._set_lock()

    class Reg1(uvm_reg):
        def __init__(self, name="reg0", reg_width=32):
            super().__init__(name, reg_width)
            self.field = uvm_reg_field('field')

        def build(self):
            self.field.configure(self, 32, 0, 'RO', 0, 0)
            self._set_lock()

    class Reg2(uvm_reg):
        def __init__(self, name="reg0", reg_width=32):
            super().__init__(name, reg_width)
            self.field = uvm_reg_field('field')

        def build(self):
            self.field.configure(self, 32, 0, 'WO', 0, 0)
            self._set_lock()

    class Reg3(uvm_reg):
        def __init__(self, name="reg0", reg_width=32):
            super().__init__(name, reg_width)

        def build(self):
            self._set_lock()

    register_0 = Reg0('reg0')
    assert register_0.get_name() == 'reg0'
    assert register_0.field.get_name() == 'field'

    register_1 = Reg1('reg1')
    assert register_1.get_name() == 'reg1'
    assert register_1.field.get_name() == 'field'

    register_2 = Reg2('reg2')
    assert register_2.get_name() == 'reg2'
    assert register_2.field.get_name() == 'field'

    register_3 = Reg3('reg3')
    assert register_3.get_name() == 'reg3'

    predict_reg(register_0)
    predict_reg(register_1)
    predict_reg(register_2)
    predict_reg(register_3)


@pytest.mark.test_reg_predict_with_spaces
def test_reg_predict_with_spaces():
    """
    Test register predict with spaces
    """
    class Reg0(uvm_reg):
        def __init__(self, name="reg0", reg_width=32):
            super().__init__(name, reg_width)
            self.field1 = uvm_reg_field('field1')
            self.field2 = uvm_reg_field('field2')
            self.field3 = uvm_reg_field('field3')
            self.field4 = uvm_reg_field('field4')

        def build(self):
            self.field1.configure(self, 7, 1,   'RW', 0, 0)
            self.field2.configure(self, 8, 11,  'RW', 0, 0)
            self.field3.configure(self, 3, 19,  'RW', 0, 0)
            self.field4.configure(self, 7, 24,  'RW', 0, 0)
            self._set_lock()

    reg0 = Reg0('reg0')
    assert reg0.get_name() == 'reg0'
    assert reg0.field1.get_name() == 'field1'
    assert reg0.field2.get_name() == 'field2'
    assert reg0.field3.get_name() == 'field3'
    assert reg0.field4.get_name() == 'field4'

    predict_reg(reg0)