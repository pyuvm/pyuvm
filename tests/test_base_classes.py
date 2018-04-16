import pyuvm_unittest
import unittest
from predefined_component_classes import *
import uvm_pkg
from base_classes import *

class base_classes_TestCase ( pyuvm_unittest.pyuvm_TestCase ):
    """Basic test cases."""

    class my_object(uvm_object):...

    class other_object(uvm_object):...
    def test_base_factory(self):
        mo = self.my_object.create('object_name')
        self.assertEqual(type(mo), self.my_object)

    def test_override(self):
        self.my_object.override=self.other_object
        mo = self.my_object.create('overridden')
        self.assertEqual(type(mo), self.other_object)

