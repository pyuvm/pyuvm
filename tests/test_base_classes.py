import pyuvm_unittest
from uvm_pkg import *


class my_object(uvm_object): ...

class base_classes_TestCase ( pyuvm_unittest.pyuvm_TestCase ):
    """Basic test cases."""

    def test_basic_creation(self):
        """
        Tests whether the factory gets populated and whether it can be used.
        """
        uvf = uvm_factory()
        mof= uvf.fd.classes["my_object"]("factory")
        moi=my_object("myinst")
        self.assertEqual(type(mof), type(moi))

    # Testing specification

    def test_seeding_5_3_3(self):
        """
        5.3.3.1 get_uvm_seeding
        5.3.3.2 set_uvm_seeding
        5.3.3.3 reseed
        """
        mo = my_object("mo")
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.get_uvm_seeding()
        with self.assertRaises(error_classes.UVMNotImplemented):
            seeding = mo.set_uvm_seeding(1)
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.reseed()

    def test_identification_5_3_4(self):
        nameless = my_object()
        self.assertTrue(len(nameless.get_name()) == 0)
        moe = my_object("moe")
        name = moe.get_name()
        self.assertEqual("moe",name)
        moe.set_name("curly")
        name = moe.get_name()
        self.assertEqual("curly", name)





    def test_create(self):
        """
        Tests the create method.
        """
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
