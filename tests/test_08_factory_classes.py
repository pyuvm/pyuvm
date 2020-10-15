import pyuvm_unittest
from pyuvm import *

class s08_factory_classes_TestCase (pyuvm_unittest.pyuvm_TestCase):
    """
    8.0 Factory Class Testing
    """

    class original(uvm_component):...
    class override_1(uvm_component):...
    class override_2(uvm_component):...
    class override_3(uvm_component):...

    def setUp(self):
        self.fd = utility_classes.FactoryData()
        self.top = uvm_component("top")
        self.mid = uvm_component("mid", self.top)
        self.sib = uvm_component("sib", self.top)
        self.orig = self.original("orig", self.mid)
        self.orig = self.original("orig", self.sib)
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
        self.factory.set_inst_override_by_type(self.original, self.override_1, "top.mid.orig")
        override = self.fd.overrides[self.original]
        self.assertEqual("top.mid.orig", override.inst_pattern)
        self.assertEqual(self.override_1, override.override)


    def test_set_inst_override_by_name_8_3_1_4_1(self):
        """
        8.3.1.4.1
        :return:
        check that we put the right data into fd for this override.
        """
        self.factory.set_inst_override_by_name("original", "override_1", "top.sib.orig")
        override = self.fd.overrides[self.original]
        self.assertEqual("top.sib.orig", override.inst_pattern)
        self.assertEqual(self.override_1, override.override)

    def test_set_type_override_by_type_8_3_1_4_2(self):
        """
        8.3.1.4.2
        Check that class override is set properly
        """
        self.factory.set_type_override_by_type(self.original, self.override_1)
        ovr = self.fd.overrides[self.original]
        self.assertEqual(self.override_1, ovr.override)
        self.factory.set_type_override_by_type(self.original, self.override_2, False)
        ovr = self.fd.overrides[self.original]
        self.assertEqual(self.override_1, ovr.override)
        self.factory.set_type_override_by_type(self.original, self.override_2, True)
        ovr = self.fd.overrides[self.original]
        self.assertEqual(self.override_2, ovr.override)

    def test_set_type_override_by_name_8_3_1_4_2(self):
        """
        8.3.1.4.2
        Check that name override is setting correct informmation.
        """
        self.factory.set_type_override_by_name("original", "override_1")
        self.assertEqual(self.override_1, self.fd.overrides[self.original].override)
        self.factory.set_type_override_by_name("original", "override_2", False)
        self.assertEqual(self.override_1, self.fd.overrides[self.original].override)
        self.factory.set_type_override_by_name("original", "override_2", True)
        self.assertEqual(self.override_2, self.fd.overrides[self.original].override)


    def test_find_inst_override_8_3_1_5(self):
        self.factory.set_inst_override_by_type(self.original, self.override_1, "top.sib.orig")
        overridden = self.fd.find_inst_override(self.original, "top.sib.orig")
        self.assertEqual(overridden, self.override_1 )

    def test_find_inst_override_wildcard_8_3_1_5(self):
        self.factory.set_inst_override_by_type(self.original, self.override_2, "*")
        overridden = self.fd.find_inst_override(self.original, "top.mid.orig")
        self.assertEqual(self.override_2, overridden )
        overridden = self.fd.find_inst_override(self.original, "top.sib.orig")
        self.assertEqual(self.override_2, overridden )

    def test_find_inst_override_wildcard_in_path_8_3_1_5(self):
        self.factory.set_inst_override_by_type(self.original, self.override_2, "top.mid*")
        overridden = self.fd.find_inst_override(self.original, "top.mid.orig")
        self.assertEqual(self.override_2, overridden )
        overridden = self.fd.find_inst_override(self.original, "top.sib.orig")
        self.assertEqual(self.original, overridden )

    def test_find_inst_recursive_override_in_path_8_3_1_5(self):
        self.factory.set_inst_override_by_type(self.original, self.override_1, "*")
        self.factory.set_inst_override_by_type(self.override_1, self.override_2, "*")
        self.factory.set_inst_override_by_type(self.override_2, self.override_3, "*")
        overridden = self.fd.find_inst_override(self.original, "top.mid.orig")
        self.assertEqual(self.override_3, overridden)





