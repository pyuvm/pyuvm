import pyuvm_unittest
from pyuvm import *
import logging


class s08_factory_classes_TestCase(pyuvm_unittest.pyuvm_TestCase):
    # class s08_factory_classes_TestCase (unittest.TestCase):
    """
    8.0 Factory Class Testing
    """

    class original_comp(uvm_component): ...

    class comp_1(uvm_component): ...

    class comp_2(uvm_component): ...

    class comp_3(uvm_component): ...

    class original_object(uvm_object): ...

    class object_1(uvm_object): ...

    class object_2(uvm_object): ...

    class object_3(uvm_object): ...

    def setUp(self):
        self.fd = utility_classes.FactoryData()
        self.top = uvm_component("top")
        self.mid = uvm_component("mid", self.top)
        self.sib = uvm_component("sib", self.top)
        self.mid_orig = self.original_comp("orig", self.mid)
        self.sib_orig = self.original_comp("orig", self.sib)
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
        self.factory.set_inst_override_by_type(self.original_comp, self.comp_1, "top.mid.orig")
        override = self.fd.overrides[self.original_comp]
        self.assertTrue("top.mid.orig" in override.inst_overrides)
        self.assertEqual(self.comp_1, override.inst_overrides["top.mid.orig"])
        self.assertEqual(self.comp_1, override.find_inst_override("top.mid.orig"))

    def test_set_inst_override_by_name_8_3_1_4_1(self):
        """
        8.3.1.4.1
        :return:
        check that we put the right data into fd for this override.
        """
        self.factory.set_inst_override_by_name("original_comp", "comp_1", "top.sib.orig")
        override = self.fd.overrides[self.original_comp]
        self.assertTrue("top.sib.orig" in override.inst_overrides)
        self.assertEqual(self.comp_1, override.inst_overrides["top.sib.orig"])
        self.assertEqual(self.comp_1, override.find_inst_override("top.sib.orig"))

        self.factory.set_inst_override_by_name("arb", "comp_2", "top.sib.orig2")
        override = self.fd.overrides["arb"]
        self.assertTrue("top.sib.orig2" in override.inst_overrides)
        self.assertEqual(self.comp_2, override.inst_overrides["top.sib.orig2"])
        self.assertEqual(self.comp_2, override.find_inst_override("top.sib.orig2"))

    def test_set_type_override_by_type_8_3_1_4_2(self):
        """
        8.3.1.4.2
        Check that class override is set properly
        """
        self.factory.set_type_override_by_type(self.original_comp, self.comp_1)
        ovr = self.fd.overrides[self.original_comp]
        self.assertEqual(self.comp_1, ovr.type_override)
        self.factory.set_type_override_by_type(self.original_comp, self.comp_2, False)
        ovr = self.fd.overrides[self.original_comp]
        self.assertEqual(self.comp_1, ovr.type_override)
        self.factory.set_type_override_by_type(self.original_comp, self.comp_2, True)
        ovr = self.fd.overrides[self.original_comp]
        self.assertEqual(self.comp_2, ovr.type_override)

    def test_set_type_override_by_name_8_3_1_4_2(self):
        """
        8.3.1.4.2
        Check that name override is setting correct informmation.
        """
        self.factory.set_type_override_by_name("original_comp", "comp_1")
        self.assertEqual(self.comp_1, self.fd.overrides[self.original_comp].type_override)
        self.factory.set_type_override_by_name("original_comp", "comp_2", False)
        self.assertEqual(self.comp_1, self.fd.overrides[self.original_comp].type_override)
        self.factory.set_type_override_by_name("original_comp", "comp_2", True)
        self.assertEqual(self.comp_2, self.fd.overrides[self.original_comp].type_override)
        # Test adding an override with an arbitrary string
        self.factory.set_type_override_by_name("xyzzy", "comp_2")
        self.assertEqual(self.comp_2, self.fd.overrides['xyzzy'].type_override)

    def test_override_str(self):
        self.factory.set_type_override_by_type(self.original_comp, self.comp_1)
        ovr = self.fd.overrides[self.original_comp]
        self.assertEqual(self.comp_1, ovr.type_override)
        # using name because less typing
        self.factory.set_inst_override_by_name("original_comp", "comp_2", "top.sib.orig")
        self.factory.set_inst_override_by_name("original_comp", "comp_3", "top.mid.orig")
        ovr = self.fd.overrides[self.original_comp]
        ss = str(self.fd.overrides[self.original_comp])
        self.assertEqual('Type Override: comp_1     || Instance Overrides: top.sib.orig => comp_2 | top.mid.orig => comp_3',
                         str(self.fd.overrides[self.original_comp]))

    def test_find_type_override(self):
        """
        Test simple retrieval of type override
        :return:
        """
        self.factory.set_type_override_by_type(self.original_comp, self.comp_1)
        self.assertEqual(self.comp_1, self.fd.find_override(self.original_comp))

    def test_find_override_by_name(self):
        self.factory.set_type_override_by_name("xyzzy", "comp_2")
        new_obj = self.fd.find_override("xyzzy")
        self.assertEqual(self.comp_2, new_obj)

    def test_find_recursive_override_8_3_1_5(self):
        """
        8.3.1.5
        Test recursive overrides
        :return:
        """
        self.factory.set_type_override_by_type(self.original_comp, self.comp_1)
        self.factory.set_type_override_by_type(self.comp_1, self.comp_2)
        self.factory.set_type_override_by_type(self.comp_2, self.comp_3)
        self.assertEqual(self.comp_3, self.fd.find_override(self.original_comp))

    def test_find_recursion_loop_8_3_1_5(self):
        """
        8.3.1.5
        Test recursive overrides with a
        :return:
        """
        self.factory.set_type_override_by_type(self.original_comp, self.comp_1)
        self.factory.set_type_override_by_type(self.comp_1, self.comp_2)
        self.factory.set_type_override_by_type(self.comp_2, self.comp_3)
        self.factory.set_type_override_by_type(self.comp_3, self.original_comp)
        with self.assertLogs(logging.getLogger('Factory')):
            overridden_orig = self.fd.find_override(self.original_comp)
        self.assertEqual(self.comp_3, overridden_orig)

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
        self.factory.set_inst_override_by_type(self.original_comp, self.comp_1, "top.sib.orig")
        self.factory.set_inst_override_by_type(self.original_comp, self.comp_2, "top.mid.orig")
        overridden = self.fd.find_override(self.original_comp, "top.sib.orig")
        self.assertEqual(self.comp_1, overridden)

    def test_find_inst_override_wildcard_8_3_1_5(self):
        """
        8.3.1.5
        Test for an override with a wildcard
        :return:
        """
        self.factory.set_inst_override_by_type(self.original_comp, self.comp_2, "*")
        overridden = self.fd.find_override(self.original_comp, "top.mid.orig")
        self.assertEqual(self.comp_2, overridden)
        overridden = self.fd.find_override(self.original_comp, "top.sib.orig")
        self.assertEqual(self.comp_2, overridden)

    def test_find_inst_override_wildcard_in_path_8_3_1_5(self):
        """
        8.3.1.5
        Test for an inst_path wildcard in part of a path
        :return:
        """
        self.factory.set_inst_override_by_type(self.original_comp, self.comp_2, "top.mid*")
        overridden = self.fd.find_override(self.original_comp, "top.mid.orig")
        self.assertEqual(self.comp_2, overridden)
        overridden = self.fd.find_override(self.original_comp, "top.sib.orig")
        self.assertEqual(self.original_comp, overridden)

    def test_find_inst_recursive_override_in_path_8_3_1_5(self):
        """
        8.3.1.5
        Test for recursive override with inst path.
        :return:
        """
        self.factory.set_inst_override_by_type(self.original_comp, self.comp_1, "*")
        self.factory.set_inst_override_by_type(self.comp_1, self.comp_2, "*")
        self.factory.set_inst_override_by_type(self.comp_2, self.comp_3, "*")
        overridden = self.fd.find_override(self.original_comp, "top.mid.orig")
        self.assertEqual(self.comp_3, overridden)

    def test_not_finding_inst_override_8_3_1_5(self):
        """
        8.3.1.5
        Test for looking for an inst override and not finding one with a type override
        :return:
        """
        self.factory.set_type_override_by_type(self.original_comp, self.comp_3)
        self.factory.set_inst_override_by_type(self.original_comp, self.comp_1, "top.sib.orig")
        self.factory.set_inst_override_by_type(self.original_comp, self.comp_2, "top.mid.orig")
        overridden = self.fd.find_override(self.original_comp, "top.notthere.orig")
        self.assertEqual(self.comp_3, overridden)

    def test_not_finding_inst_override_at_all_8_3_1_5(self):
        """
        8.3.1.5
        Test for looking for an inst override and not finding one and with no type_override
        :return: None
        """
        self.factory.set_inst_override_by_type(self.original_comp, self.comp_1, "top.sib.orig")
        self.factory.set_inst_override_by_type(self.original_comp, self.comp_2, "top.mid.orig")
        overridden = self.fd.find_override(self.original_comp, "top.notthere.orig")
        self.assertEqual(self.original_comp, overridden)

    def test_create_object_by_type_and_name_8_3_1_5(self):
        """
        8.3.1.5
        :return: None
        """
        new_obj = self.factory.create_object_by_type(self.original_object, name="foo")
        self.assertTrue(isinstance(new_obj, self.original_object))
        self.assertEqual("foo", new_obj.get_name())
        new_obj = self.factory.create_object_by_name("object_1", name="foo_1")
        self.assertTrue(isinstance(new_obj, self.object_1))
        self.assertEqual("foo_1", new_obj.get_name())

    def test_create_object_by_type_and_name_with_type_override_8_3_1_5(self):
        """
        8.3.1.5
        :return: None
        """
        self.factory.set_type_override_by_type(self.original_object, self.object_2)
        self.factory.set_inst_override_by_type(self.original_object, self.object_1, "top.sib.orig")
        self.factory.set_inst_override_by_name("original_object", "object_1", "top.sib.orig_1")
        new_obj = self.factory.create_object_by_type(self.original_object, parent_inst_path="top.sib", name="orig")
        self.assertTrue(isinstance(new_obj, self.object_1))
        self.assertEqual("orig", new_obj.get_name())
        new_obj = self.factory.create_object_by_type(self.original_object, parent_inst_path="top.noway", name="orig")
        self.assertTrue(isinstance(new_obj, self.object_2))
        self.assertEqual("orig", new_obj.get_name())
        new_obj = self.factory.create_object_by_name("original_object", parent_inst_path="top.sib", name="orig_1")
        self.assertTrue(isinstance(new_obj, self.object_1))
        self.assertEqual("orig_1", new_obj.get_name())
        new_obj = self.factory.create_object_by_name("original_object", parent_inst_path="top.noway", name="orig2b")
        self.assertTrue(isinstance(new_obj, self.object_2))
        self.assertEqual("orig2b", new_obj.get_name())
        with self.assertLogs(self.factory.logger):
            not_an_instance = self.factory.create_object_by_name("not_an_object", name="badname")
            self.assertIsNone(not_an_instance)

    def test_create_component_by_type_and_name_override_8_3_1_5(self):
        """
        8.3.1.5
        Create overridden object.
        :return:
        """
        test_top = self.factory.create_component_by_type(self.original_comp, name="test_top")
        self.factory.set_type_override_by_type(self.original_comp, self.comp_1)
        self.factory.set_inst_override_by_type(self.original_comp, self.comp_1, "test_top.sib1")
        self.factory.set_inst_override_by_name("original_comp", "comp_2", "test_top.sib2")
        new_obj = self.factory.create_component_by_type(self.original_comp,
                                                        parent_inst_path="test_top", name="sib1", parent=test_top)
        self.assertTrue(isinstance(new_obj, self.comp_1))
        self.assertEqual("sib1", new_obj.get_name())
        self.assertEqual("test_top.sib1", new_obj.get_full_name())
        new_obj = self.factory.create_component_by_name("original_comp",
                                                        parent_inst_path="test_top", name="sib2", parent=test_top)
        self.assertTrue(isinstance(new_obj, self.comp_2))
        self.assertEqual("sib2", new_obj.get_name())
        self.assertEqual("test_top.sib2", new_obj.get_full_name())

    def test_set_type_alias_8_3_1_6_1(self):
        """
        8.3.1.6.1
        This is not implemeneted in SystemVerilog or here
        :return: None
        """
        with self.assertRaises(error_classes.UVMNotImplemented):
            self.factory.set_type_alias("xyzzy", self.original_comp)

    def test_set_inst_alias_8_3_1_6_2(self):
        """
        8.3.1.6.2
        This is not implemeneted in SystemVerilog or here
        :return: None
        """
        with self.assertRaises(error_classes.UVMNotImplemented):
            self.factory.set_inst_alias("xyzzy", self.original_comp, "instpath")

    def test_find_override_by_type_and_name_8_3_1_7_1(self):
        """
        8.3.1.7.1
        Testing both the type and name variants
        :return: None
        """
        self.factory.set_inst_override_by_type(self.original_object, self.object_1, "top.sib.orig")
        self.factory.set_inst_override_by_name("original_object", "object_2", "top.sib.orig_2")
        override = self.factory.find_override_by_type(self.original_object, "top.sib.orig")
        self.assertEqual(self.object_1, override)
        override = self.factory.find_override_by_name("original_object", "top.sib.orig_2")
        self.assertEqual(self.object_2, override)
        with self.assertRaises(AssertionError):
            override = self.factory.find_override_by_name(self.original_object, "top.sib.orig_2")

    def test_find_wrapper_by_name_8_3_1_7_2(self):
        """
        8.3.1.7.2
        find_wrapper_by_name is not implemented
        :return: None
        """
        with self.assertRaises(error_classes.UVMNotImplemented):
            self.factory.find_wrapper_by_name()

    def test_is_type_name_registered_8_3_1_7_3(self):
        """
        8.3.1.7.3
        :return: None
        """
        self.assertTrue(self.factory.is_type_name_registered("original_object"))
        self.assertFalse(self.factory.is_type_name_registered("fake_object"))

    def test_is_type_registered_8_3_1_7_3(self):
        """
        8.3.1.7.3
        :return: None
        """
        self.assertTrue(self.factory.is_type_registered(self.original_comp))

        class uvm_fake(uvm_object):...
        del self.factory.fd.classes["uvm_fake"]

        self.assertFalse(self.factory.is_type_registered(uvm_fake))

    def test_factory_str(self):
        self.factory.set_type_override_by_type(self.original_comp, self.comp_1)
        ovr = self.fd.overrides[self.original_comp]
        self.assertEqual(self.comp_1, ovr.type_override)
        # using name because less typing
        self.factory.set_inst_override_by_name("original_comp", "comp_2", "top.sib.orig")
        self.factory.set_inst_override_by_name("original_comp", "comp_3", "top.mid.orig")
        self.factory.set_inst_override_by_type(self.original_object, self.object_1, "label")
        ss0 = self.factory.__str__(0)
        ss1 = self.factory.__str__(1)
        ss2 = self.factory.__str__(2)
        # Testing for the actual strings will cause errors as classes change due to
        # other tests being run. This catches the basic functionality.
        self.assertTrue(len(ss2) > len(ss1) > len(ss0))

    def test_object_creation(self):
        new_obj = uvm_object.create("claribel")
        self.assertTrue(isinstance(new_obj, uvm_object))
        self.assertEqual("claribel", new_obj.get_name())

    def test_class_creation(self):
        class Foo(uvm_object):
            ...
        new_obj = Foo.create("foobar")
        self.assertTrue(isinstance(new_obj, Foo))
        self.assertEqual("foobar", new_obj.get_name())

    def test_component_creation(self):
        new_comp = uvm_component.create("test", None)
        self.assertTrue(isinstance(new_comp, uvm_component))
        self.assertEqual("test", new_comp.get_name())

    def test_ext_comp_creation(self):
        class FooComp(uvm_component):
            ...
        new_comp = FooComp.create("Foo", None)
        self.assertEqual("Foo", new_comp.get_name())
        self.assertTrue(isinstance(new_comp, FooComp))

    def test_type_override_by_type(self):
        class Comp(uvm_component):
            ...
        class Other(Comp):
            ...
        class Test(uvm_test):
            def build_phase(self):
                uvm_factory().set_type_override_by_type(Comp, Other)
                self.cc = Comp.create("cc", self)
        uvm_root().run_test("Test")
        utt = uvm_root()._utt()
        self.assertTrue(isinstance(utt.cc, Other))

    def test_inst_override_by_type(self):
        class Comp(uvm_component):
            ...
        class Other(Comp):
            ...
        class Test(uvm_test):
            def build_phase(self):
                uvm_factory().set_inst_override_by_type(Comp, Other, self.get_full_name()+".cc2")
                self.cc1 = Comp.create("cc1", self)
                self.cc2 = Comp.create("cc2", self)
        uvm_root().run_test("Test")
        utt = uvm_root()._utt()
        self.assertTrue(isinstance(utt.cc1, Comp))
        self.assertTrue(isinstance(utt.cc2, Other))

    def test_inst_override_by_name(self):
        class Comp(uvm_component):
            ...
        class Other(Comp):
            ...
        class Test(uvm_test):
            def build_phase(self):
                uvm_factory().set_inst_override_by_name("Comp", "Other", self.get_full_name()+".cc2")
                self.cc1 = Comp.create("cc1", self)
                self.cc2 = Comp.create("cc2", self)
        uvm_root().run_test("Test")
        utt = uvm_root()._utt()
        self.assertTrue(isinstance(utt.cc1, Comp))
        self.assertTrue(isinstance(utt.cc2, Other))

    def test_type_override_by_name(self):
        class Comp(uvm_component):
            ...
        class Other(Comp):
            ...
        class Test(uvm_test):
            def build_phase(self):
                uvm_factory().set_type_override_by_name("Comp", "Other")
                self.cc1 = Comp.create("cc1", self)
                self.cc2 = Comp.create("cc2", self)
        uvm_root().run_test("Test")
        utt = uvm_root()._utt()
        self.assertTrue(isinstance(utt.cc1, Other))
        self.assertTrue(isinstance(utt.cc2, Other))

    def test_obj_type_override_by_type(self):
        class Obj(uvm_object):
            ...
        class OtherObj(Obj):
            ...
        class Test(uvm_test):
            def build_phase(self):
                uvm_factory().set_type_override_by_type(Obj, OtherObj)
                self.cc1 = Obj.create("cc1")
        uvm_root().run_test("Test")
        utt = uvm_root()._utt()
        self.assertTrue(isinstance(utt.cc1, OtherObj))

    def test_obj_type_override_by_name(self):
        class Obj(uvm_object):
            ...
        class OtherObj(Obj):
            ...
        class Test(uvm_test):
            def build_phase(self):
                uvm_factory().set_type_override_by_name("Obj", "OtherObj")
                self.cc1 = Obj.create("cc1")
        uvm_root().run_test("Test")
        utt = uvm_root()._utt()
        self.assertTrue(isinstance(utt.cc1, OtherObj))

    def test_obj_inst_override_by_type(self):
        class Obj(uvm_object):
            ...
        class OtherObj(Obj):
            ...
        class Test(uvm_test):
            def build_phase(self):
                uvm_factory().set_inst_override_by_type(Obj, OtherObj, self.get_full_name())
                self.cc1 = Obj.create("cc1")
        uvm_root().run_test("Test")
        utt = uvm_root()._utt()
        self.assertTrue(isinstance(utt.cc1, Obj)) #Cant inst override objects

