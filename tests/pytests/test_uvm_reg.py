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
