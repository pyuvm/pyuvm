import pyuvm_unittest
import unittest
from pyuvm.s13_predefined_component_classes import *

class my_test(uvm_test):...


class s13_predefined_component_TestCase ( pyuvm_unittest.pyuvm_TestCase ):
    """Basic test cases."""
    def setUp(self):
        super().setUp()
        ConfigDB().clear()

    def test_uvm_component_noparent(self):
        """
        13.1.2.2 Basic component creation.
        13.1.2.1 Constructor
        13.1 class defined
        """
        comp = uvm_component ( 'test' )
        self.assertTrue ( 'test' in uvm_component.component_dict )
        self.assertTrue ( comp.parent == uvm_root() )
        self.assertTrue(comp.print_enabled) #13.1.2.2

    def test_do_execute_op_13_1_2_3(self):
        """
        13.1.2.3
        We have not implemented policies.
        """
        comp = uvm_component('test')
        with self.assertRaises(error_classes.UVMNotImplemented):
            comp.do_execute_op("op")

    def test_component_with_parent(self):
        parent = uvm_component ( 'parent' )
        child = uvm_component ( 'child', parent )
        self.assertTrue ( 'parent' in uvm_component.component_dict )
        self.assertTrue ( f'parent.child' in uvm_component.component_dict )
        self.assertTrue ( parent.parent == uvm_root() )
        self.assertTrue ( child.parent == parent )
        self.assertEqual ( list ( parent.hierarchy ), [parent, child] )

    def test_hierarchy(self):
        parent = uvm_component ( 'parent' )
        child1 = uvm_component ( 'child1', parent )
        child2 = uvm_component ( 'child2', parent )
        child3 = uvm_component ( 'child3', child1 )
        child4 = uvm_component ( 'child4', child3 )
        golden_list = [parent, child1, child3, child2]
        self.assertEqual ( list ( parent.hierarchy ), golden_list )
        hier = list ( parent.hierarchy )
        hier.reverse ()
        golden_list.reverse ()
        self.assertEqual ( hier, golden_list )

    def test_get_parent_13_1_3_1(self):
        """
        13.1.3.1 get_parent test
        :return:
        """
        parent = uvm_component('parent')
        child = uvm_component('child', parent)
        grandchild = uvm_component('grandchild',child)
        par = grandchild.get_parent()
        self.assertEqual(child, par)
        gpar = child.get_parent()
        self.assertEqual(gpar, parent)
        gpar = grandchild.get_parent().get_parent()
        self.assertEqual(parent,gpar)

    def test_get_full_name_13_1_3_2(self):
        """
        13.1.3.1 get_parent test
        :return:
        """
        parent = uvm_component('parent')
        child1 = uvm_component('child1', parent)
        child2 = uvm_component('child2', parent)
        child21 = uvm_component('child21',child2)
        parent_name = parent.get_full_name()
        self.assertEqual("parent", parent_name)
        self.assertEqual("parent.child1", child1.get_full_name())
        self.assertEqual("parent.child2", child2.get_full_name())
        self.assertEqual("parent.child2.child21", child21.get_full_name())




    def test_get_children_13_1_3_3(self):
        """
        13.1.3.3

        """
        parent = uvm_component ( 'parent' )
        child1 = uvm_component ( 'child1', parent )
        child2 = uvm_component ( 'child2', parent )
        child3 = uvm_component ( 'child3', parent )
        child11 = uvm_component ( 'child11', child1 )
        child111 = uvm_component ( 'child111', child11 )
        children = parent.get_children()
        print(children)
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

        parent = uvm_component('parent')
        child1 = uvm_component('child1', parent)
        child2 = uvm_component('child2', parent)
        child3 = uvm_component('child3', parent)
        cl = parent.get_children()
        for cc in parent.children:
            cc_name = cc
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
        parent = uvm_component('parent')
        child1 = uvm_component('child1', parent)
        child2 = uvm_component('child2', parent)
        child3 = uvm_component('child3', parent)
        self.assertEqual(parent.get_child("child1"),child1)
        self.assertIsNone(parent.get_child("orphan"))

    def test_get_num_children_13_1_3_5(self):
        """
        13.1.3.5
        get_num_children() returns the number of children.
        """
        parent = uvm_component('parent')
        child1 = uvm_component('child1', parent)
        child2 = uvm_component('child2', parent)
        child3 = uvm_component('child3', parent)
        cl = parent.get_children()
        self.assertEqual(parent.get_num_children(), len(cl))
        self.assertEqual(child1.get_num_children(), len(child1.get_children()))

    def test_has_child_13_1_3_6(self):
        """
        13.1.3.6
        Returns the child of the name
        :return:
        """
        parent = uvm_component('parent')
        child1 = uvm_component('child1', parent)
        child2 = uvm_component('child2', parent)
        child3 = uvm_component('child3', child1)
        self.assertTrue ( child1.has_child ( 'child3' ) )
        self.assertEqual ( len ( parent.get_children() ), 2 )
        self.assertEqual ( parent.get_child ( 'child1' ).get_name(), 'child1' )
        self.assertEqual ( 2, parent.get_num_children () )
        self.assertFalse(parent.has_child("orphan"))


    def test_lookup_13_1_3_7(self):
        """
        13.1.3.7
        lookup finds components based on their full names.
        a.b.c is relative to the parent of a
        .a.b.c means a is the top level and we find our way down.
        :return:
        """
        parent = uvm_component ( 'parent' )
        child1 = uvm_component ( 'child1', parent )
        child2 = uvm_component ( 'child2', parent )
        child3 = uvm_component ( 'child3', child1 )
        child4 = uvm_component ( 'child4', child3 )
        self.assertEqual (child1, parent.lookup ( 'child1' ))
        self.assertEqual (child3, parent.lookup ( 'child1.child3' ))
        self.assertNotEqual (child1, parent.lookup ( 'child2' ))
        self.assertEqual (child3, parent.lookup ( '.parent.child1.child3' ))
        self.assertEqual (child3, child1.lookup ( 'child3' ))
        self.assertEqual (child4, child1.lookup ( 'child3.child4' ))

    def test_get_depth_13_1_3_8(self):
        """
        13.1.3.8
        get_depth measures dept from uvm_root where uvm_root is 0
        :return:
        """
        parent = uvm_component ( 'parent' )
        child1 = uvm_component ( 'child1', parent )
        child2 = uvm_component ( 'child2', parent )
        child3 = uvm_component ( 'child3', child1 )
        child4 = uvm_component ( 'child4', child3 )
        self.assertEqual( 0, uvm_root().get_depth())
        self.assertEqual(1, parent.get_depth())
        self.assertEqual(2, child1.get_depth())
        self.assertEqual (3, child3.get_depth ())

    class my_component ( uvm_component ):
        def run_phase(self): ...




    def test_component_factory(self):
        mc = self.my_component('mc', None)
        mc2 = self.my_component.create('my_component' , None)
        self.assertEqual(type(mc), type(mc2))


    def test_config_db(self):
        A = uvm_component('A')
        B = uvm_component('B', A)
        C = uvm_component('C', A)
        D = uvm_component('D', C)
        E = uvm_component('E', B)

        A.cdb_set("FIVE", 5, "")
        datum = A.cdb_get("FIVE", "")
        self.assertEqual(5, datum)

        with self.assertRaises(error_classes.UVMConfigItemNotFound):
            B.cdb_get("FIVE", "")

        C.cdb_set("TT", 33, "A.B.C.*")
        with self.assertRaises(error_classes.UVMConfigItemNotFound):
            C.cdb_get("TT", "")

        ConfigDB().set(None, "A.*", "TEN",  10)
        datum = E.cdb_get("TEN", "")
        self.assertEqual(10, datum)

        ConfigDB().set(None, "A.C","FF", 44)
        datum = C.cdb_get("FF", "")
        self.assertEqual(44, datum)


    def test_wildcard_precedence(self):
        A = uvm_component('A')
        B = uvm_component('B', A)
        C = uvm_component('C', A)
        A.cdb_set("TEST", 11, "*")
        A.cdb_set("TEST", 22, "B")
        ConfigDB().set(A, "A", "OTHER", 55)
        aa = A.cdb_get("TEST", "X")
        bb = B.cdb_get("TEST", "")
        self.assertEqual(22,bb)
        cc = C.cdb_get("TEST", "")
        self.assertEqual(11, cc)
        aao = A.cdb_get("OTHER", "A")
        self.assertEqual(55, aao)

    def test_contextless_behavior_in_heirarchy(self):
        A = uvm_component('A')
        B = uvm_component('B', A)
        C = uvm_component('C', A)
        ConfigDB().set(A, "*", "OTHER", 55)
        aa = ConfigDB().get(A, "B", "OTHER")
        self.assertEqual(55, aa)

    def test_agent_config(self):
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

            def run_phase(self):
                self.raise_objection()
                time.sleep(0.1)
                self.drop_objection()
        uvm_root().run_test("test")
        utt = uvm_root().get_child("uvm_test_top")
        self.assertEqual(uvm_active_passive_enum.UVM_ACTIVE, utt.agent.get_is_active())
        self.assertEqual(uvm_active_passive_enum.UVM_PASSIVE, utt.agent.bot.get_is_active())
        self.assertTrue(utt.agent.active())
        self.assertFalse(utt.agent.bot.active())

    def test_default_agent_config(self):
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

            def run_phase(self):
                self.raise_objection()
                time.sleep(0.1)
                self.drop_objection()
        uvm_root().run_test("test")
        utt = uvm_root().get_child("uvm_test_top")
        self.assertEqual(uvm_active_passive_enum.UVM_ACTIVE, utt.agent.get_is_active())
        self.assertEqual(uvm_active_passive_enum.UVM_ACTIVE, utt.agent.bot.get_is_active())
        self.assertTrue(utt.agent.active())
        self.assertTrue(utt.agent.bot.active())

if __name__ == '__main__':
    unittest.main ()
