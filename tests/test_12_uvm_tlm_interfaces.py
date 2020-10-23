import pyuvm_unittest
from pyuvm import *


class s12_uvm_tlm_interfaces_TestCase (pyuvm_unittest.pyuvm_TestCase):
    class my_comp(uvm_component):...
    def test_uvm_put_port(self):
        mc = self.my_comp("mc")
        pp = uvm_put_port("pp", mc)
        pp.put('5')
        pass
    
