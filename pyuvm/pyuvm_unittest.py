import unittest
import logging
import uvm_pkg
from predefined_component_classes import uvm_component, uvm_root
class pyuvm_TestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('pyuvm_TestCase')

    def setUp(self):
        uvm_component.uvm_root=None
        uvm_pkg.uvm_root=None
        uvm_component.component_dict.clear()
        uvm_root.component_dict.clear()
        uvm_root.clear_singletons()
        uvm_component.uvm_root=uvm_root('uvm_root')
        pass
