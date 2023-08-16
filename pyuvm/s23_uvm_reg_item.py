# Import Main Package
from pyuvm import uvm_sequence_item
from copy import deepcopy
from pyuvm import uvm_object
from pyuvm.s24_uvm_reg_includes import elem_kind_e, access_e
from pyuvm.s24_uvm_reg_includes import status_t, path_t
from pyuvm.s24_uvm_reg_includes import error_out


# Main Class
class uvm_reg_item(uvm_sequence_item):
    # constructor
    def __init__(self, name='item'):
        # Kind of element being accessed: REG, MEM, or FIELD.
        self.element_kind = elem_kind_e()
        # A handle to the RegModel model element
        # associated with this transaction.
        # Use <element_kind> to determine the type to cast  to: <uvm_reg>,
        # <uvm_mem>, or <uvm_reg_field>.
        self.element_object = None
        # Kind of access: READ or WRITE.
        # with it shall be via the set_kind() and get_kind() accessor methods
        self.kind = access_e()
        # The value to write to, or after completion,
        # the value read from the DUT.
        self.value = []
        # For memory accesses, the offset address. For bursts,
        # the ~starting~ offset address.
        # Access to this variable is provided
        # for randomization, otherwise interactions
        # with it shall be via the set_offset()
        # and get_offset() accessor methods
        self.offset = 0
        # The result of the transaction: IS_OK, HAS_X, or ERROR.
        self.status = status_t()
        # The local map used to obtain addresses. Users may customize
        # address-translation using this map. Access to the sequencer
        # and bus adapter can be obtained by getting this map's root map,
        # then calling <uvm_reg_map::get_sequencer> and
        # self.local_map = uvm_reg_map() TODO:
        # The original map specified for the operation. The actual <map>
        # used may differ when a test or sequence written at the block
        # level is reused at the system level.
        # self.map = uvm_reg_map() TODO:
        # The path being used: <UVM_FRONTDOOR> or <UVM_BACKDOOR>.
        self.path = path_t()
        # The sequence from which the operation originated.
        # with it shall be via the set_parent() and get_parent()
        # accessor methods
        self.parent_sequence = None  # TODO: i doubt is needed
        # TODO: not needed as rand since it will
        # be simple assigned to be carried
        self.extension_object = None
        # If path is UVM_BACKDOOR, this member specifies the abstraction
        # kind for the backdoor access, e.g. "RTL" or "GATES".
        self.bd_kind = "RTL"
        # Name storing
        self.name = name
        # Additional Fields
        self.addr = 0
        self.data = 0
        self.n_bits = 0
        self.header = "PYUVM_REG_ITEM -- "

    ########################################################
    # Internal Methods
    ########################################################

    # do_copy
    def do_copy(self, rhs):
        # Check
        if not isinstance(rhs, uvm_reg_item):
            error_out(self.header, "WRONG_TYPE Provided rhs \
                      is not of type uvm_reg_item")
        else:
            # Deep Copy
            copied = deepcopy(rhs)
        return copied

    # set_element_kind
    def set_element_kind(self, _kind):
        self.element_kind = _kind

    # get_element_kind
    def get_element_kind(self):
        return self.element_kind

    # set_element
    def set_element(self, el):
        self.element = el

    # get_element
    def get_element(self):
        return self.element

    # set_kind
    def set_kind(self, _kind):
        self.kind = _kind

    # get_kind
    def get_kind(self):
        return self.kind

    # set_value
    def set_value(self, value):
        self.value.append(value)

    # get_value
    def get_value(self, idx):
        if (idx < self.value.size()):
            return self.value[idx]
        else:
            error_out(self.header, "Index out of LIST")

    # set_value_size
    def set_value_size(self, sz):
        self.value = [0] * sz

    # get_value_size
    def get_value_size(self):
        return self.value.size()

    # set_value_array
    def set_value_array(self, v):
        self.value = v

    # get_value_array
    def get_value_array(self):
        return self.value

    # set_offset
    def set_offset(self, offset):
        self.offset = offset

    # get_offset
    def get_offset(self):
        return self.offset

    # set_status
    def set_status(self, status):
        if ~isinstance(status, status_t):
            error_out(self.header, "Wrong assignment to status Enum")
        else:
            self.status = status

    # get_status
    def get_status(self):
        return self.status

    # set_door
    def set_door(self, door):
        self.path = door

    # get_door
    def get_door(self):
        return self.path

    # set_extension
    def set_extension(self, ext):
        if not isinstance(ext, uvm_object):
            error_out(self.header, "bd kind is not string possible values \
                      RTL or GATE")
        else:
            self.extension = ext

    # get+extension
    def get_extension(self):
        return self.extension

    # set_bd_kind
    def set_bd_kind(self, val):
        if not isinstance(val, str):
            error_out(self.header, "bd kind is not string possible values \
                      RTL or GATE")
        else:
            self.bd_kind = val

    # get_bd_kind
    def get_bd_kind(self):
        return self.bd_kind
