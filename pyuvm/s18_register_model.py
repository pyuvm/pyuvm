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
    def __init__(self, name='uvm_reg_field'):
        super().__init__(name)
        self._parent = None
        self._size = None
        self._lsb_pos = None
        self._access = None
        self._is_volatile = None
        self._reset = None

    # 18.5.3.2
    # TODO Fix signature
    def configure(self, parent, size, lsb_pos, access, is_volatile, reset):
        # TODO Add validation of arguments
        # TODO Support binary and hex values for 'reset'
        self._parent = parent
        self._size = size
        self._lsb_pos = lsb_pos
        self._access = access
        self._is_volatile = is_volatile
        self._reset = reset

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

    # 18.5.4.5
    def get_access(self):
        # TODO Check that 'configure' was called
        return self._access

    # 18.5.4.10
    def is_volatile(self):
        # TODO Check that 'configure' was called
        return self._is_volatile

    # 18.5.5.6
    def get_reset(self):
        # TODO Check that 'configure' was called
        return self._reset
