import pyuvm_unittest
import unittest
from predefined_component_classes import *
import uvm_pkg

class predefined_component_TestCase(pyuvm_unittest.pyuvm_TestCase):
    """Basic test cases."""

    def test_uvm_component_noparent(self):
        comp=uvm_component('test')
        print(uvm_component.component_dict)
        self.assertTrue('.test' in uvm_component.component_dict)
        self.assertTrue(comp.parent == uvm_component.uvm_root)

    def test_component_with_parent(self):
        parent = uvm_component('parent')
        child  = uvm_component('child',parent)
        print(uvm_component.component_dict)
        self.assertTrue('.parent' in uvm_component.component_dict)
        self.assertTrue(f'.parent.child' in uvm_component.component_dict)
        self.assertTrue(parent.parent == uvm_component.uvm_root)
        self.assertTrue(child.parent == parent)
        self.assertEqual(list(parent.hierarchy), [parent, child])

    def test_hierarchy(self):
        parent=uvm_component('parent')
        child1=uvm_component('child1', parent)
        child2=uvm_component('child2', parent)
        child3=uvm_component('child3', child1)
        child4=uvm_component('child4', child3)
        self.assertEqual(list(parent.hierarchy), [parent, child1, child3, child2])
        hier = list(parent.hierarchy)
        hier.reverse()

    def test_children(self):
        parent=uvm_component('parent')
        child1=uvm_component('child1', parent)
        child2=uvm_component('child2', parent)
        child3=uvm_component('child3', child1)
        child4=uvm_component('child4', child3)
        self.assertTrue(child1.has_child('child3'))
        self.assertEqual(len(parent.children),2)
        self.assertEqual(parent.get_child('child1').name,'child1')
        self.assertEqual(2,parent.get_num_children())

    def test_lookup(self):
        parent=uvm_component('parent')
        child1=uvm_component('child1', parent)
        child2=uvm_component('child2', parent)
        child3=uvm_component('child3', child1)
        child4=uvm_component('child4', child3)
        self.assertEqual(parent.lookup('child1'),child1)
        self.assertEqual(parent.lookup('child1.child3'),child3)
        self.assertNotEqual(parent.lookup('child2'), child1)
        self.assertEqual(parent.lookup('.parent.child1.child3'),child3)
        self.assertEqual(child1.lookup('child3'),child3)
        self.assertEqual(child1.lookup('child3.child4'),child4)

    def test_depth(self):
        parent=uvm_component('parent')
        child1=uvm_component('child1', parent)
        child2=uvm_component('child2', parent)
        child3=uvm_component('child3', child1)
        child4=uvm_component('child4', child3)
        self.assertEqual(child3.get_depth(), 3)

if __name__ == '__main__':
    unittest.main()
