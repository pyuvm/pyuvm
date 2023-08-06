## Import Main Package
from pyuvm import uvm_object
from pyuvm import uvm_sequence_item
from pyuvm import uvm_sequence
from s24_pyuvm_reg_includes import *
from s23_pyuvm_reg_item import *

## Main Class
class pyuvm_reg_predictor(uvm_object):
    ## Constructor
    def __init__(self, name="pyuvm_reg_predictor"):
        super().__init__(name)
