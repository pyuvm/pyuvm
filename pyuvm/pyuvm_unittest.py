import unittest
import logging
from predefined_component_classes import uvm_component, uvm_root
class pyuvm_TestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('pyuvm_TestCase')

    def setUp(self):
        uvm_component.uvm_root=None
        uvm_component.component_dict={}
        uvm_component.uvm_root=uvm_root()
