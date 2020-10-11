import unittest
import logging
import pyuvm
from s13_predefined_component_classes import uvm_component, uvm_root
class pyuvm_TestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('pyuvm_TestCase')

    def setUp(self):
        uvm_component.component_dict.clear()
        uvm_root.component_dict.clear()
        uvm_root.clear_singletons()
        pass
