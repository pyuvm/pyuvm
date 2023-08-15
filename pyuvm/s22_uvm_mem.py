# Main Packages same as import uvm_pkg or uvm_defines.svh
from pyuvm import uvm_object
from pyuvm.s24_uvm_reg_includes import uvm_not_implemeneted


# Pyuvm Mem Class declaration abstraction
class uvm_mem(uvm_object):
    def __init__(self, name="uvm_mem"):
        super().__init__(name)
        uvm_not_implemeneted(f"{name} uvm_mem not implemented")
