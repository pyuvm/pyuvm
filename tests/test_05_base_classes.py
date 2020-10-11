import pyuvm_unittest
from pyuvm import *


class my_object(uvm_object):
    def __init__(self, name = ""):
        super().__init__(name)
        self.val = 5;
    def __eq__(self, other):
        if type(other) is type(self):
            return self.val == other.val



class s05_base_classes_TestCase (pyuvm_unittest.pyuvm_TestCase):
    """Basic test cases."""

    def test_basic_creation_15_3(self):
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
        # 5.3.4.2
        nameless = my_object()
        self.assertTrue(len(nameless.get_name()) == 0)
        moe = my_object("moe")
        # 5.3.4.2
        name = moe.get_name()
        self.assertEqual("moe",name)
        # 5.3.4.1
        moe.set_name("curly")
        name = moe.get_name()
        self.assertEqual("curly", name)
        moe.set_name("larry")
        # 5.3.4.3
        name = moe.get_full_name()
        self.assertEqual("larry", name)
        # 5.3.4.4
        moe_id = moe.get_inst_id()
        self.assertEqual(id(moe), moe_id)
        # 5.3.4.5 not implemented
        with self.assertRaises(error_classes.UVMNotImplemented):
            moe.get_type()
        # 5.3.4.6 not implemented
        with self.assertRaises(error_classes.UVMNotImplemented):
            moe.get_object_type()
        # 5.3.4.7
        self.assertEqual("my_object", moe.get_type_name())

    def test_creation_5_3_5(self):
        mo = my_object('mo')
        # 5.3.5.1
        new_mo = mo.create('new_mo')
        self.assertEqual('new_mo', new_mo.get_name())
        self.assertEqual(type(new_mo), type(mo))
        # 5.3.5.2
        mo.val = 5
        cln_mo = mo.clone()
        self.assertTrue(mo.__eq__(cln_mo))

    def test_printing_5_3_6(self):
        mo = my_object("mo")
        # 5.3.6.1
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.print()
        # 5.3.6.2
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.sprint()
        # 5.3.6.3 Use __str__(
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.convert2string()
    def test_recording_5_3_7(self):
        mo = my_object("mo")
        # 5.3.7.1
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.record()
        # 5.3.7.2
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.do_record()

    def test_copying_5_3_8(self):
        mo = my_object("mo")
        # 5.3.8.1
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.copy()
        # 5.3.8.2
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.do_copy()

    def test_comparing_5_3_9(self):
        mo = my_object("mo")
        # 5.3.9.1
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.compare()
        # 5.3.9.2
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.do_compare()

    def test_packing_5_3_10(self):
        mo = my_object("mo")
        # 5.3.10.1
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.pack()
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.pack_bytes()
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.pack_ints()
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.pack_longints()
        # 5.3.10.2
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.do_pack()

    def test_unpacking_5_3_11(self):
        mo = my_object("mo")
        # 5.3.10.1
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.unpack()
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.unpack_bytes()
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.unpack_ints()
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.unpack_longints()
        # 5.3.11.2

        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.do_unpack()

    def test_configuration_5_3_12(self):
        mo = my_object("mo")
        # 5.3.12.1
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.set_local()

    def test_field_operations_5_3_13(self):
        mo = my_object("mo")
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.do_execute_op()

    def test_active_policy_5_3_14(self):
        mo = my_object("mo")
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.push_active_policy()
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.pop_active_policy()
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.get_active_policy()









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