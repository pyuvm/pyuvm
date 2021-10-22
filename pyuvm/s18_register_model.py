from pyuvm import uvm_object


# 18.1.1 Class declaration
class uvm_reg_block(uvm_object):

    # 18.1.2.1
    # TODO Fix signature
    def __init__(self, name=""):
        super().__init__(name)
        self._regs = []

    # 18.1.3.7
    # TODO Fix signature
    def get_registers(self):
        return self._regs

    def _add_register(self, reg):
        self._regs.append(reg)


# 18.2.1 Class declaration
class uvm_reg_map(uvm_object):

    # 18.2.3.1
    def __init__(self, name="uvm_reg_map"):
        super().__init__(name)
        self._parent = None
        self._base_addr = None
        self._regs = {}

    # 18.2.3.2
    # TODO Fix signature
    # TODO Support binary and hex values for 'base_addr'
    def configure(self, parent, base_addr):
        self._parent = parent
        self._base_addr = base_addr

    # 18.2.4.2
    def get_parent(self):
        return self._parent

    # 18.2.4.4
    # TODO Fix signature
    def get_base_addr(self):
        return self._base_addr

    # 18.2.3.3
    # TODO Fix signature
    # TODO Perform validation (e.g. reg not already added)
    def add_reg(self, reg, offset):
        self._regs[offset] = reg

    # 18.2.4.11
    def get_registers(self):
        return list(self._regs.values())

    # 18.2.4.17
    # TODO Fix signature
    # TODO Handle case where no register exists at offset
    def get_reg_by_offset(self, offset):
        return self._regs[offset]


# 18.4.1 Class declaration
class uvm_reg(uvm_object):

    # 18.3.2.1
    # TODO Fix signature
    def __init__(self, name=""):
        super().__init__(name)
        self._parent = None
        self._fields = []

    # 18.4.2.2
    def configure(self, parent):
        self._parent = parent
        parent._add_register(self)

    # 18.4.3.1
    def get_parent(self):
        return self._parent

    # 18.4.3.11
    # TODO Return fields in canonical order (LSB to MSB)
    def get_fields(self):
        return self._fields

    # TODO Add validation
    # - field not None
    # - field not already added
    # - field fits in reg
    # - field doesn't overlap with any other field
    # - etc.
    def _add_field(self, field):
        self._fields.append(field)


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
        parent._add_field(self)
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
