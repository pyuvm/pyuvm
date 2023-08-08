# Import Main Package
from pyuvm import uvm_object


# Main Class
class uvm_reg_predictor(uvm_object):
    # Constructor
    def __init__(self, name="uvm_reg_predictor"):
        super().__init__(name)
