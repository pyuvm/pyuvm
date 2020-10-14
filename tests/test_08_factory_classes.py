import pyuvm_unittest
from pyuvm import *

class s08_factory_classes_TestCase (pyuvm_unittest.pyuvm_TestCase):
    """
    8.0 Factory Class Testing
    """

    class original(uvm_component):...
    class override_1(uvm_component):...
    class override_2(uvm_component):...

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
        self.assertEqual(self.fd.type_instance_overrides["top.mid.orig"], (self.original,self.override_1))

    def test_set_inst_override_by_name_8_3_1_4_1(self):
        """
        8.3.1.4.1
        :return:
        check that we put the right data into fd for this override.
        """
        self.factory.set_inst_override_by_name("original", "override_1", "top.sib.orig")
        self.assertEqual(self.fd.name_instance_overrides["top.sib.orig"], ("original", self.override_1))

    def test_set_type_override_by_type_8_3_1_4_2(self):
        """
        8.3.1.4.2
        Check that class override is set properly
        """
        self.factory.set_type_override_by_type(self.original, self.override_1)
        self.assertEqual(self.fd.class_overrides[self.original], self.override_1)
        self.factory.set_type_override_by_type(self.original, self.override_2, False)
        self.assertEqual(self.fd.class_overrides[self.original], self.override_1)
        self.factory.set_type_override_by_type(self.original, self.override_2, True)
        self.assertEqual(self.fd.class_overrides[self.original], self.override_2)

    def test_set_type_override_by_name_8_3_1_4_2(self):
        """
        8.3.1.4.2
        Check that name override is setting correct informmation.
        """
        self.factory.set_type_override_by_name("original", "override_1")
        self.assertEqual(self.fd.name_overrides["original"], self.override_1)
        self.factory.set_type_override_by_name("original", "override_2", False)
        self.assertEqual(self.fd.name_overrides["original"], self.override_1)
        self.factory.set_type_override_by_name("original", "override_2", True)
        self.assertEqual(self.fd.name_overrides["original"], self.override_2)

