import pyuvm_unittest
from pyuvm import *


class my_object(uvm_object):
    def __init__(self, name = ""):
        super().__init__(name)
        self.val = 5
    def __eq__(self, other):
        if type(other) is type(self):
            return self.val == other.val



class s05_base_classes_TestCase (pyuvm_unittest.pyuvm_TestCase):
    """Basic test cases."""

    def test_basic_creation(self):
        """
        15.3
        Tests whether the factory gets populated and whether it can be used.
        """
        uvf = uvm_factory()
        mof= uvf.fd.classes["my_object"]("factory")
        moi=my_object("myinst")
        self.assertEqual(type(mof), type(moi))

    # Testing specification

    def test_seeding(self):
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

    def test_identification(self):
        """
        5.3.4
        :return:
        """
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

    def test_creation(self):
        """
        5.3.5
        :return:
        """
        mo = my_object('mo')
        # 5.3.5.1
        with self.assertRaises(UVMNotImplemented):
            new_mo = mo.create('new_mo')
            self.assertEqual('new_mo', new_mo.get_name())
            self.assertEqual(type(new_mo), type(mo))
        # 5.3.5.2
        mo.val = 5
        cln_mo = mo.clone()
        self.assertTrue(mo.__eq__(cln_mo))

    def test_printing(self):
        """
        5.3.6
        :return:
        """
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
    def test_recording(self):
        """
        5.3.7
        :return:
        """
        mo = my_object("mo")
        # 5.3.7.1
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.record()
        # 5.3.7.2
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo.do_record()

    def test_copying(self):
        """
        5.3.8
        :return:
        """
        mo = my_object("mo")
        # 5.3.8.1
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.copy()
        # 5.3.8.2
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.do_copy()

    def test_comparing(self):
        """
        5.3.9
        :return:
        """
        mo = my_object("mo")
        # 5.3.9.1
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.compare()
        # 5.3.9.2
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.do_compare()

    def test_packing(self):
        """
        5.3.10
        :return:
        """
        mo = my_object("mo")
        # 5.3.10.1
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.pack()
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.pack_bytes()
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.pack_ints()
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.pack_longints()
        # 5.3.10.2
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.do_pack()

    def test_unpacking(self):
        """
        5.3.11
        :return:
        """
        mo = my_object("mo")
        # 5.3.10.1
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.unpack()
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.unpack_bytes()
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.unpack_ints()
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.unpack_longints()
        # 5.3.11.2

        with self.assertRaises(error_classes.UsePythonMethod):
            mo.do_unpack()

    def test_configuration(self):
        """
        5.3.12
        :return:
        """
        mo = my_object("mo")
        # 5.3.12.1
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.set_local()

    def test_field_operations(self):
        """
        5.3.13
        :return:
        """
        mo = my_object("mo")
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.do_execute_op(None)

    def test_active_policy(self):
        """
        5.3.14
        :return:
        """
        mo = my_object("mo")
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.push_active_policy()
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.pop_active_policy()
        with self.assertRaises(error_classes.UsePythonMethod):
            mo.get_active_policy()

    def test_create(self):
        """
        5.3.5 This needs to be further implemented to include the factory
        """
        mo = my_object("first")
        with self.assertRaises(error_classes.UVMNotImplemented):
            mo2 = mo.create("second")

    def test_uvm_transaction_creation(self):
        """
        5.4.2.1
        5.4.2.14
        5.4.2.15
        :return:
        """
        tr = uvm_transaction()
        self.assertEqual(0, len(tr.get_name()))
        self.assertIsNone(tr.get_initiator())
        uc = uvm_component("uc")
        tr.set_initiator(uc)
        self.assertEqual(uc, tr.get_initiator())


    def test_transaction_recording(self):
        """
        5.4.2 all methods
        :return:
        """
        tr = uvm_transaction()
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.accept_tr(None)
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.do_accept_tr()
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.begin_tr(None, None)
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.do_begin_tr()
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.end_tr(None, None)
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.do_end_tr()
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.get_tr_handle()
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.enable_recording()
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.disable_recording()
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.is_recording_enabled()
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.is_active()
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.get_event_pool()
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.get_accept_time()
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.get_begin_time()
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.get_end_time()
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.set_transaction_id(-1)
        with self.assertRaises(error_classes.UVMNotImplemented):
            tr.get_transaction_id()
