import pyuvm_unittest
from pyuvm import *

class s14_sequence_TestCase (pyuvm_unittest.pyuvm_TestCase):

    def test_sequence_item_creation(self):
        """
        14.1.2.1
        Testing that initial values are set properly
        :return:
        """
        si = uvm_sequence_item("si")
        self.assertEqual("si", si.get_name())
        self.assertFalse(si.get_use_sequence_info())

    def test_set_context(self):
        """
        14.1.2.2
        :return:
        """
        # Not sure how to test this without an associated get_context method
        pass

    def test_set_get_use_sequence_info(self):
        """
        14.1.2.3
        :return:
        """
        si = uvm_sequence_item("test")
        self.assertFalse(si.get_use_sequence_info())
        si.set_use_sequence_info(True)
        self.assertTrue(si.get_use_sequence_info())
        si.set_use_sequence_info(False)
        self.assertFalse(si.get_use_sequence_info())
        with self.assertRaises(AssertionError):
            si.set_use_sequence_info(1)



    
