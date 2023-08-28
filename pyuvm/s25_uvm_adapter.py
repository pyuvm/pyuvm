# Import Main Package
from pyuvm import uvm_object
from pyuvm import uvm_sequence_item
from pyuvm import uvm_sequence
from pyuvm.s24_uvm_reg_includes import uvm_reg_bus_op
from pyuvm.s24_uvm_reg_includes import uvm_not_implemeneted
from pyuvm.s23_uvm_reg_item import uvm_reg_item


# Main Class
class uvm_reg_adapter(uvm_object):
    # Constructor
    def __init__(self, name="uvm_reg_adapter"):
        super().__init__(name)
        #  Set this bit in extensions of this class if the bus protocol
        #  supports byte enables.
        self.byte_enable = True
        self.parent_sequence = None
        self.reg_item = uvm_sequence_item
        self.header = name + "-- "
        self.provide_response = False

    # Function -- reg2bus
    # Extensions of this class must
    # implement this method to convert the specified
    # <uvm_reg_bus_op> to a corresponding <uvm_sequence_item>
    # subtype that defines the bus
    # transaction.
    # The method must allocate a new bus-specific <uvm_sequence_item>,
    # assign its members from
    # the corresponding members from the given
    # generic ~rw~ bus operation, then
    # return it.
    def reg2bus(self, rw: uvm_reg_bus_op) -> uvm_sequence_item:
        uvm_not_implemeneted(self.header)

    #    Function -- bus2reg
    #    Extensions of this class ~must~ implement this method to copy members
    #    of the given bus-specific ~bus_item~
    #   to corresponding members of the provided
    #    ~bus_rw~ instance. Unlike <reg2bus>, the resulting transaction
    #    is not allocated from scratch. This is to accommodate applications
    #    where the bus response must be returned in the original request.
    def bus2reg(self, bus_item: uvm_sequence_item, rw: uvm_reg_bus_op):
        uvm_not_implemeneted(self.header)

    # Use this method to retrieve the item from the adapter
    def get_item(self):
        return self.reg_item

    # Use this method to set the item into the adapter class
    def set_item(self, item: uvm_reg_item):
        self.reg_item = item

    # Use this method to set the parent sequence into the adapter class
    # Generaly is a simple Write Sequence
    def set_parent_sequence(self, sequence: uvm_sequence):
        self.parent_sequence = sequence

    # Use this method to set the parent sequence into the adapter class
    # Generaly is a simple Write Sequence
    def get_parent_sequence(self):
        return self.parent_sequence

    # get_provide_reponse
    def get_provide_reponse(self):
        return self.provide_response

    # get_byte_en
    def get_byte_en(self):
        return self.byte_enable

# ------------------------------------------------------------------------------
#  Example:
#  The following example illustrates how to implement a
#   RegModel-BUS adapter class
#  for the APB bus protocol.
#
# class rreg2apb_adapter(uvm_reg_adapter):
#  def __init__(self, name="uvm_reg_adapter"):
#      super().__init__(name)
#
#  def reg2bus(rw: uvm_reg_bus_op):
#    apb_item apb = apb_item.create("apb_item")
#    if(rw.kind == UVM_READ):
#        apb.op   = READ
#    elsif (rw.kind == UVM_WRITE):
#        apb.op   = WRITE;
#    else:
#        assert(0,"reg2bus -- Wrong operation type used for APB OP")
#    apb.addr = rw.addr;
#    apb.data = rw.data;
#    return apb;
#
#  def bus2reg(bus_item: uvm_sequencer_item, rw: uvm_reg_bus_op):
#    apb_item apb;
#    if (isinstance(apb,uvm_sequencer_item)):
#        assert(0,"Bus item is not of type apb_item")
#    else:
#        if(apb.op == READ):
#           rw.kind   = UVM_READ
#        elsif (apb.op == WRITE):
#           rw.kind   = UVM_WRITE;
#        else:
#           assert 0,"bus2reg -- Wrong operation \
#           type used for uvm_reg_bus_op"
#        rw.addr      = apb.addr;
#        rw.data      = apb.data;
#        rw.status    = UVM_IS_OK;
#
# ------------------------------------------------------------------------------
