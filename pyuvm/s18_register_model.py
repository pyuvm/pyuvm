from pyuvm import uvm_object


# 18.1.1 Class declaration
class uvm_reg_block(uvm_object):
    pass


# 18.2.1 Class declaration
class uvm_reg_map(uvm_object):
    pass


# 18.4.1 Class declaration
class uvm_reg(uvm_object):
    pass


# 18.5.1 Class declaration
class uvm_reg_field(uvm_object):

    # 18.5.3.1
    # TODO Fix signature
    def __init__(self):
        self._parent = None
        self._size = None

    # 18.5.3.2
    # TODO Fix signature
    def configure(self, parent, size):
        self._parent = parent
        self._size = size

    # 18.5.4.1
    def get_parent(self):
        return self._parent

    # 18.5.4.3
    def get_n_bits(self):
        return self._size
