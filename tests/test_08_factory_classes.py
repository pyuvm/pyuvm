import pyuvm_unittest
from pyuvm import *

class s08_factory_classes_TestCase (pyuvm_unittest.pyuvm_TestCase):
    """
    8.0 Factory Class Testing
    """

    class original_comp(uvm_component):...
    class override_1(uvm_component):...
    class override_2(uvm_component):...
    class override_3(uvm_component):...
    class original_object(uvm_object):...
    class object_1(uvm_object):...
    class object_2(uvm_object):...
    class object_3(uvm_object):...


    def setUp(self):
        self.fd = utility_classes.FactoryData()
        self.top = uvm_component("top")
        self.mid = uvm_component("mid", self.top)
        self.sib = uvm_component("sib", self.top)
        self.orig = self.original_comp("orig", self.mid)
        self.orig = self.original_comp("orig", self.sib)
        self.factory = uvm_factory()

    def tearDown(self):
        self.fd.clear_overrides()
        uvm_root.clear_singletons()
        self.top.clear_hierarchy()
        uvm_component.clear_components()

    def test_set_inst_override_by_type_8_3_1_4_1(self):
        """
        8.3.1.4.1 set_inst_override_by_type
        Basic test to make sure that the factory data is set properly
        """
        self.factory.set_inst_override_by_type(self.original_comp, self.override_1, "top.mid.orig")
        override = self.fd.overrides[self.original_comp]
        self.assertTrue("top.mid.orig" in override.inst_overrides)
        self.assertEqual(self.override_1, override.inst_overrides["top.mid.orig"])
        self.assertEqual(self.override_1, override.find_inst_override("top.mid.orig"))

    def test_set_inst_override_by_name_8_3_1_4_1(self):
        """
        8.3.1.4.1
        :return:
        check that we put the right data into fd for this override.
        """
        self.factory.set_inst_override_by_name("original", "override_1", "top.sib.orig")
        override = self.fd.overrides[self.original_comp]
        self.assertTrue("top.sib.orig" in override.inst_overrides)
        self.assertEqual(self.override_1, override.inst_overrides["top.sib.orig"])
        self.assertEqual(self.override_1, override.find_inst_override("top.sib.orig"))


    def test_set_type_override_by_type_8_3_1_4_2(self):
        """
        8.3.1.4.2
        Check that class override is set properly
        """
        self.factory.set_type_override_by_type(self.original_comp, self.override_1)
        ovr = self.fd.overrides[self.original_comp]
        self.assertEqual(self.override_1, ovr.type_override)
        self.factory.set_type_override_by_type(self.original_comp, self.override_2, False)
        ovr = self.fd.overrides[self.original_comp]
        self.assertEqual(self.override_1, ovr.type_override)
        self.factory.set_type_override_by_type(self.original_comp, self.override_2, True)
        ovr = self.fd.overrides[self.original_comp]
        self.assertEqual(self.override_2, ovr.type_override)

    def test_set_type_override_by_name_8_3_1_4_2(self):
        """
        8.3.1.4.2
        Check that name override is setting correct informmation.
        """
        self.factory.set_type_override_by_name("original", "override_1")
        self.assertEqual(self.override_1, self.fd.overrides[self.original_comp].type_override)
        self.factory.set_type_override_by_name("original", "override_2", False)
        self.assertEqual(self.override_1, self.fd.overrides[self.original_comp].type_override)
        self.factory.set_type_override_by_name("original", "override_2", True)
        self.assertEqual(self.override_2, self.fd.overrides[self.original_comp].type_override)

    def test_find_type_override(self):
        """
        Test simple retrieval of type override
        :return:
        """
        self.factory.set_type_override_by_type(self.original_comp, self.override_1)
        self.assertEqual(self.override_1, self.fd.find_override(self.original_comp))

    def test_find_recursive_override_8_3_1_5(self):
        """
        8.3.1.5
        Test recursive overrides
        :return:
        """
        self.factory.set_type_override_by_type(self.original_comp, self.override_1)
        self.factory.set_type_override_by_type(self.override_1, self.override_2)
        self.factory.set_type_override_by_type(self.override_2, self.override_3)
        self.assertEqual(self.override_3, self.fd.find_override(self.original_comp))

    def test_find_recursion_loop_8_3_1_5(self):
        """
        8.3.1.5
        Test recursive overrides with a loop
        :return:
        """
        self.factory.set_type_override_by_type(self.original_comp, self.override_1)
        self.factory.set_type_override_by_type(self.override_1, self.override_2)
        self.factory.set_type_override_by_type(self.override_2, self.override_3)
        self.factory.set_type_override_by_type(self.override_3, self.original_comp)
        overridden_orig = self.fd.find_override(self.original_comp)
        self.assertEqual(self.override_3, overridden_orig)

    def test_no_type_override(self):
        """
        8.3.1.5
        Test looking for an override and not finding one
        :return:
        """
        no_over = self.fd.find_override(self.original_comp)
        self.assertEqual(self.original_comp, no_over)

    def test_find_inst_override_8_3_1_5(self):
        """
        8.3.1.5
        Test for an override with an inst path
        """
        self.factory.set_inst_override_by_type(self.original_comp, self.override_1, "top.sib.orig")
        self.factory.set_inst_override_by_type(self.original_comp, self.override_2, "top.mid.orig")
        overridden = self.fd.find_override(self.original_comp, "top.sib.orig")
        self.assertEqual(self.override_1, overridden )

    def test_find_inst_override_wildcard_8_3_1_5(self):
        """
        8.3.1.5
        Test for an override with a wildcard
        :return:
        """
        self.factory.set_inst_override_by_type(self.original_comp, self.override_2, "*")
        overridden = self.fd.find_override(self.original_comp, "top.mid.orig")
        self.assertEqual(self.override_2, overridden )
        overridden = self.fd.find_override(self.original_comp, "top.sib.orig")
        self.assertEqual(self.override_2, overridden )

    def test_find_inst_override_wildcard_in_path_8_3_1_5(self):
        """
        8.3.1.5
        Test for an inst_path wildcard in part of a path
        :return:
        """
        self.factory.set_inst_override_by_type(self.original_comp, self.override_2, "top.mid*")
        overridden = self.fd.find_override(self.original_comp, "top.mid.orig")
        self.assertEqual(self.override_2, overridden )
        overridden = self.fd.find_override(self.original_comp, "top.sib.orig")
        self.assertEqual(self.original_comp, overridden)

    def test_find_inst_recursive_override_in_path_8_3_1_5(self):
        """
        8.3.1.5
        Test for recursive override with inst path.
        :return:
        """
        self.factory.set_inst_override_by_type(self.original_comp, self.override_1, "*")
        self.factory.set_inst_override_by_type(self.override_1, self.override_2, "*")
        self.factory.set_inst_override_by_type(self.override_2, self.override_3, "*")
        overridden = self.fd.find_override(self.original_comp, "top.mid.orig")
        self.assertEqual(self.override_3, overridden)

    def test_not_finding_inst_override_8_3_1_5(self):
        """
        8.3.1.5
        Test for looking for an inst override and not finding one with a type override
        :return:
        """
        self.factory.set_type_override_by_type(self.original_comp, self.override_3)
        self.factory.set_inst_override_by_type(self.original_comp, self.override_1, "top.sib.orig")
        self.factory.set_inst_override_by_type(self.original_comp, self.override_2, "top.mid.orig")
        overridden = self.fd.find_override(self.original_comp, "top.notthere.orig")
        self.assertEqual(self.override_3, overridden )

    def test_not_finding_inst_override_at_all_8_3_1_5(self):
        """
        8.3.1.5
        Test for looking for an inst override and not finding one and with no type_override
        :return:
        """
        self.factory.set_inst_override_by_type(self.original_comp, self.override_1, "top.sib.orig")
        self.factory.set_inst_override_by_type(self.original_comp, self.override_2, "top.mid.orig")
        overridden = self.fd.find_override(self.original_comp, "top.notthere.orig")
        self.assertEqual(self.original_comp, overridden )

    def test_create_object_by_type_8_3_1_5(self):
        new_obj = self.factory.create_object_by_type(self.original_object, name="foo")
        self.assertTrue(isinstance(new_obj, self.original_object))

    def test_create_object_by_type_with_type_override(self):
        self.factory.set_type_override_by_type(self.original_object, self.object_2)
        self.factory.set_inst_override_by_type(self.original_object, self.object_1, "top.sib.orig")
        new_obj = self.factory.create_object_by_type(self.original_object, parent_inst_path="top.sib",name="orig")
        self.assertTrue(isinstance(new_obj, self.object_1))
        self.assertEqual("orig", new_obj.get_name())
        new_obj = self.factory.create_object_by_type(self.original_object, parent_inst_path="top.noway",name="orig2")
        self.assertTrue(isinstance(new_obj, self.object_2))
        self.assertEqual("orig2", new_obj.get_name() )








