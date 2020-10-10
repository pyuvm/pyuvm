import pyuvm_unittest
from base_classes import *
from uvm_pkg import *
factory_classes

class my_object(uvm_object): ...

class base_classes_TestCase ( pyuvm_unittest.pyuvm_TestCase ):
    """Basic test cases."""

    def test_basic_creation(self):
        uvf = factory_classes.uvm_factory()
        mof= uvf.fd.classes["my_object"]("factory")
        moi=my_object("myinst")
        self.assertEqual(type(mof), type(moi))

    def test_create(self):
        mo = my_object("first")
        mo2 = mo.create("second")
        self.assertEqual(type(mo), type(mo2))


    # def test_override(self):
    #     self.my_object.override(self.other_object)
    #     mo = self.my_object.create('overridden')
    #     self.assertEqual(type(mo), self.other_object)
    #
    #
    # def test_create_by_name(self):
    #     mo = uvm_object.create_by_name(globals()['my_object'], 'myname')
    #     self.assertEqual(type(mo), my_object)
    #
