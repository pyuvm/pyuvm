import unittest

import uvm_unittest

from pyuvm.s13_predefined_component_classes import *
from pyuvm.utility_classes import Singleton


class my_test(uvm_test): ...


class s13_predefined_component_TestCase(uvm_unittest.uvm_TestCase):
    """Basic test cases."""

    def setUp(self):
        super().setUp()
        ConfigDB().clear()
        uvm_root().clear_children()

    def test_uvm_component_no_parent(self):
        """
        13.1.2.2 Basic component creation.
        13.1.2.1 Constructor
        13.1 class defined
        """
        comp = uvm_component("test", None)
        self.assertTrue("test" in uvm_component.component_dict)
        self.assertTrue(comp.parent == uvm_root())
        self.assertTrue(comp.print_enabled)  # 13.1.2.2

    def test_do_execute_op_13_1_2_3(self):
        """
        13.1.2.3
        We have not implemented policies.
        """
        comp = uvm_component("test", None)
        with self.assertRaises(error_classes.UVMNotImplemented):
            comp.do_execute_op("op")

    def test_component_with_parent(self):
        parent = uvm_component("parent", None)
        child = uvm_component("child", parent)
        self.assertTrue("parent" in uvm_component.component_dict)
        self.assertTrue("parent.child" in uvm_component.component_dict)
        self.assertTrue(parent.parent == uvm_root())
        self.assertTrue(child.parent == parent)
        self.assertEqual(list(parent.hierarchy), [parent, child])

    def test_hierarchy(self):
        parent = uvm_component("parent", None)
        child1 = uvm_component("child1", parent)
        child2 = uvm_component("child2", parent)
        child3 = uvm_component("child3", child1)
        golden_list = [parent, child1, child3, child2]
        self.assertEqual(list(parent.hierarchy), golden_list)
        hier = list(parent.hierarchy)
        hier.reverse()
        golden_list.reverse()
        self.assertEqual(hier, golden_list)

    def test_get_parent_13_1_3_1(self):
        """
        13.1.3.1 get_parent test
        :return:
        """
        parent = uvm_component("parent", None)
        child = uvm_component("child", parent)
        grandchild = uvm_component("grandchild", child)
        par = grandchild.get_parent()
        self.assertEqual(child, par)
        par = child.get_parent()
        self.assertEqual(par, parent)
        par = grandchild.get_parent().get_parent()
        self.assertEqual(parent, par)

    def test_get_full_name_13_1_3_2(self):
        """
        13.1.3.1 get_parent test
        :return:
        """
        parent = uvm_component("parent", None)
        child1 = uvm_component("child1", parent)
        child2 = uvm_component("child2", parent)
        child21 = uvm_component("child21", child2)
        parent_name = parent.get_full_name()
        self.assertEqual("parent", parent_name)
        self.assertEqual("parent.child1", child1.get_full_name())
        self.assertEqual("parent.child2", child2.get_full_name())
        self.assertEqual("parent.child2.child21", child21.get_full_name())

    def test_get_children_13_1_3_3(self):
        """
        13.1.3.3

        """
        parent = uvm_component("parent", None)
        child1 = uvm_component("child1", parent)
        child2 = uvm_component("child2", parent)
        _ = uvm_component("child3", parent)
        child11 = uvm_component("child11", child1)
        _ = uvm_component("child111", child11)
        children = parent.get_children()
        self.assertTrue(len(children) == 3)
        children = child1.get_children()
        self.assertTrue(len(children) == 1)
        children = child2.get_children()
        self.assertTrue(len(children) == 0)
        children = list(parent.children)
        self.assertEqual(children, parent.get_children())

    def test_child_iterator_13_1_3_4(self):
        """
        13.1.3.4
        children is an iterator that we get from a
        UVM component. We can loop over it without getting a new
        copy of the children list.
        """

        parent = uvm_component("parent", None)
        _ = uvm_component("child1", parent)
        _ = uvm_component("child2", parent)
        _ = uvm_component("child3", parent)
        cl = parent.get_children()
        for cc in parent.children:
            _ = cc
            self.assertIn(cc, cl)

    def test_get_child_13_1_3_4(self):
        """
        oddly 13.1.3.4 defines several functions. We shall eschew
        get_next_child() and get_first_child().  But get_child(str name)
        is a righteous idea and so we'll implement that.

        As per the spec we return None if there is no child of that name rather
        than throwing a Lookup exception.
        :return:
        """
        parent = uvm_component("parent", None)
        child1 = uvm_component("child1", parent)
        _ = uvm_component("child2", parent)
        _ = uvm_component("child3", parent)
        self.assertEqual(parent.get_child("child1"), child1)
        self.assertIsNone(parent.get_child("orphan"))

    def test_get_num_children_13_1_3_5(self):
        """
        13.1.3.5
        get_num_children() returns the number of children.
        """
        parent = uvm_component("parent", None)
        child1 = uvm_component("child1", parent)
        _ = uvm_component("child2", parent)
        _ = uvm_component("child3", parent)
        cl = parent.get_children()
        self.assertEqual(parent.get_num_children(), len(cl))
        self.assertEqual(child1.get_num_children(), len(child1.get_children()))

    def test_has_child_13_1_3_6(self):
        """
        13.1.3.6
        Returns the child of the name
        :return:
        """
        parent = uvm_component("parent", None)
        child1 = uvm_component("child1", parent)
        _ = uvm_component("child2", parent)
        _ = uvm_component("child3", child1)
        self.assertTrue(child1.has_child("child3"))
        self.assertEqual(len(parent.get_children()), 2)
        self.assertEqual(parent.get_child("child1").get_name(), "child1")
        self.assertEqual(2, parent.get_num_children())
        self.assertFalse(parent.has_child("orphan"))

    def test_lookup_13_1_3_7(self):
        """
        13.1.3.7
        lookup finds components based on their full names.
        a.b.c is relative to the parent of a
        .a.b.c means a is the top level and we find our way down.
        :return:
        """
        parent = uvm_component("parent", None)
        child1 = uvm_component("child1", parent)
        _ = uvm_component("child2", parent)
        child3 = uvm_component("child3", child1)
        child4 = uvm_component("child4", child3)
        self.assertEqual(child1, parent.lookup("child1"))
        self.assertEqual(child3, parent.lookup("child1.child3"))
        self.assertNotEqual(child1, parent.lookup("child2"))
        self.assertEqual(child3, parent.lookup(".parent.child1.child3"))
        self.assertEqual(child3, child1.lookup("child3"))
        self.assertEqual(child4, child1.lookup("child3.child4"))

    def test_get_depth_13_1_3_8(self):
        """
        13.1.3.8
        get_depth measures dept from uvm_root where uvm_root is 0
        :return:
        """
        parent = uvm_component("parent", None)
        child1 = uvm_component("child1", parent)
        _ = uvm_component("child2", parent)
        child3 = uvm_component("child3", child1)
        _ = uvm_component("child4", child3)
        self.assertEqual(0, uvm_root().get_depth())
        self.assertEqual(1, parent.get_depth())
        self.assertEqual(2, child1.get_depth())
        self.assertEqual(3, child3.get_depth())

    class my_component(uvm_component):
        async def run_phase(self): ...

    def test_component_factory(self):
        mc = self.my_component("mc", None)
        mc2 = self.my_component.create("my_component", None)
        self.assertEqual(type(mc), type(mc2))

    def test_config_db(self):
        aa = uvm_component("aa", None)
        bb = uvm_component("bb", aa)
        cc = uvm_component("cc", aa)
        _ = uvm_component("D", cc)
        ee = uvm_component("ee", bb)

        aa.cdb_set("FIVE", 5, "")
        datum = aa.cdb_get("FIVE", "")
        self.assertEqual(5, datum)

        with self.assertRaises(error_classes.UVMConfigItemNotFound):
            bb.cdb_get("FIVE", "")

        cc.cdb_set("TT", 33, "aa.bb.cc.*")
        with self.assertRaises(error_classes.UVMConfigItemNotFound):
            cc.cdb_get("TT", "")

        ConfigDB().set(None, "aa.*", "TEN", 10)
        datum = ee.cdb_get("TEN", "")
        self.assertEqual(10, datum)

        ConfigDB().set(None, "aa.cc", "FF", 44)
        datum = cc.cdb_get("FF", "")
        self.assertEqual(44, datum)

    def test_wildcard_precedence(self):
        aa = uvm_component("aa", None)
        bb = uvm_component("bb", aa)
        cc = uvm_component("cc", aa)
        aa.cdb_set("TEST", 11, "*")
        aa.cdb_set("TEST", 22, "bb")
        ConfigDB().set(aa, "aa", "OTHER", 55)
        _ = aa.cdb_get("TEST", "X")
        bb_int = bb.cdb_get("TEST", "")
        self.assertEqual(22, bb_int)
        cc_int = cc.cdb_get("TEST", "")
        self.assertEqual(11, cc_int)
        aao = aa.cdb_get("OTHER", "aa")
        self.assertEqual(55, aao)

    def test_contextless_behavior_in_hierarchy(self):
        aa = uvm_component("aa", None)
        _ = uvm_component("B", aa)
        _ = uvm_component("C", aa)
        ConfigDB().set(aa, "*", "OTHER", 55)
        aa = ConfigDB().get(aa, "B", "OTHER")
        self.assertEqual(55, aa)

    async def test_agent_config(self):
        class bottom(uvm_agent):
            def build_phase(self):
                super().build_phase()

        class comp(uvm_agent):
            def build_phase(self):
                super().build_phase()
                ConfigDB().set(self, "bot", "is_active", 0)
                self.bot = bottom("bot", self)

        class test(uvm_test):
            def build_phase(self):
                self.cdb_set("is_active", uvm_active_passive_enum.UVM_ACTIVE)
                self.agent = comp("agent", self)

            async def run_phase(self):
                self.raise_objection()
                self.drop_objection()

        await uvm_root().run_test("test", keep_singletons=True)
        utt = uvm_root().get_child("uvm_test_top")
        self.assertEqual(uvm_active_passive_enum.UVM_ACTIVE, utt.agent.get_is_active())
        self.assertEqual(
            uvm_active_passive_enum.UVM_PASSIVE, utt.agent.bot.get_is_active()
        )
        self.assertTrue(utt.agent.active())
        self.assertFalse(utt.agent.bot.active())

    async def test_class_as_run_test_argument(self):
        class DataHolder(metaclass=Singleton):
            def __init__(self):
                self.call_count = 0

            def __str__(self):
                return f"DataHolder.call_count: {self.call_count}"

        class MyTest(uvm_test):
            async def run_phase(self):
                self.raise_objection()
                DataHolder().call_count += 1
                self.drop_objection()

        await uvm_root().run_test("MyTest", keep_set={DataHolder})
        await uvm_root().run_test(MyTest, keep_set={DataHolder})
        self.assertTrue(DataHolder().call_count == 2)

    async def test_default_agent_config(self):
        class bottom(uvm_agent):
            def build_phase(self):
                super().build_phase()

        class comp(uvm_agent):
            def build_phase(self):
                super().build_phase()
                self.bot = bottom("bot", self)

        class test(uvm_test):
            def build_phase(self):
                self.agent = comp("agent", self)

            async def run_phase(self):
                self.raise_objection()
                self.drop_objection()

        await uvm_root().run_test("test", keep_singletons=True)
        utt = uvm_root().get_child("uvm_test_top")
        self.assertEqual(uvm_active_passive_enum.UVM_ACTIVE, utt.agent.get_is_active())
        self.assertEqual(
            uvm_active_passive_enum.UVM_ACTIVE, utt.agent.bot.get_is_active()
        )
        self.assertTrue(utt.agent.active())
        self.assertTrue(utt.agent.bot.active())


if __name__ == "__main__":
    unittest.main()
