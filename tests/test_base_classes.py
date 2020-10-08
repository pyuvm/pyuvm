import pyuvm_unittest
from base_classes import *
from uvm_pkg import *

class my_object ( uvm_object ): ...


class base_classes_TestCase ( pyuvm_unittest.pyuvm_TestCase ):
    """Basic test cases."""


    class other_object(uvm_object):...

    def test_base_factory(self):
        mo = self.my_object.create('object_name')
        self.assertEqual(type(mo), self.my_object)

    def test_override(self):
        self.my_object.override(self.other_object)
        mo = self.my_object.create('overridden')
        self.assertEqual(type(mo), self.other_object)


    def test_create_by_name(self):
        mo = uvm_object.create_by_name(globals()['my_object'], 'myname')
        self.assertEqual(type(mo), my_object)

