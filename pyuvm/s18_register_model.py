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
        self._lsb_pos = None

    # 18.5.3.2
    # TODO Fix signature
    def configure(self, parent, size, lsb_pos):
        # TODO Add validation of arguments
        self._parent = parent
        self._size = size
        self._lsb_pos = lsb_pos

    # 18.5.4.1
    def get_parent(self):
        # TODO Check that 'configure' was called
        return self._parent

    # 18.5.4.2
    def get_lsb_pos(self):
        # TODO Check that 'configure' was called
        return self._lsb_pos

    # 18.5.4.3
    def get_n_bits(self):
        # TODO Check that 'configure' was called
        return self._size
