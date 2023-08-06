## Import Main Packages
from pyuvm import uvm_object, uvm_sequencer
from pyuvm.s24_pyuvm_reg_includes import *
from pyuvm.s25_pyuvm_adapter import *
from pyuvm.s26_pyuvm_predictor import *
from pyuvm.s18_pyuvm_reg_block import *

# Class declaration: uvm_reg_map
class pyuvm_reg_map(uvm_object):
    # Constructor
    def __init__(self, name="pyuvm_reg_map"):
        super().__init__(name)
        self._parent        = None
        self._base_addr     = None
        self._regs          = {}
        self.name           = name
        self.header         = name + " -- "

    # Function called by the REG_BLOCK create_map funcction
    # the parent value here should be a pyuvm_reg_block instance type
    def configure(self, parent, base_addr):
        if(isinstance(parent, pyuvm_reg_block)):
            self._parent    = parent
        else:
            UVMFatalError("pyuvm_reg_map -- configure -- parent should be pyuvm_reg_block type")
        self._base_addr = base_addr
        ## No support for Byte_Addressing nor for Byte_en TODO: add

    # get_parent
    def get_parent(self):
        return self._parent

    # get_base_addr
    def get_base_addr(self):
        return self._base_addr

    # add_reg
    def add_reg(self, reg, offset):
        self._regs[offset] = reg

    # get_registers
    def get_registers(self):
        return list(self._regs.values())

    # get_reg_by_offset
    def get_reg_by_offset(self, offset):
        return self._regs[offset]

    ## set_predictor
    def set_predictor(self, predictor):
        if isinstance(predictor, pyuvm_reg_predictor):
            self.predictor = predictor
        else:
            error_out(self.header,"predictor should be type of uvm_reg_predictor")

    ## get_predictor
    def get_predictor(self):
        if self.predictor == None:
            error_out(self.header,"predictor Not set")
        else:
            return self.predictor

    ## set_adapter
    def set_adapter(self, adapter):
        if isinstance(adapter, pyuvm_reg_adapter):
            self.adapter = adapter
        else:
            error_out(self.header,"adapter should be type of uvm_reg_adapter")

    ## get_adapter
    def get_adapter(self):
        if self.adapter == None:
            error_out(self.header,"Adapter Not set")
        else:
            return self.adapter

    ## set_sequencer
    def set_sequencer(self, sequencer):
        if isinstance(sequencer, uvm_sequencer):
            self.sequencer = sequencer
        else:
            error_out(self.header,"setting a wrong sequencer type")

    ## get_sequencer
    def get_sequencer(self):
        if(self.sequencer == None):
            error_out(self.header,"uvm_reg_map sequencer is not set")
        else:
            return self.sequencer

    ## process_write_operation
    async def process_write_operation(self, reg_address, data_to_be_written, path, check):
        ## Get the sequencer and the adapter
        local_adapter           = self.get_adapter()
        local_sequencer         = self.get_sequencer()
        ## check if the Path is set to BACKDOOR, FRONTDOOR or USER_FRONTDOOR
        if path == path_t.BACKDOOR:
            error_out(self.header,"BACKDOOR not implemented")
        elif path == path_t.USER_FRONTDOOR:
            error_out(self.header,"USER_FRONTDOOR not implemented")
        elif path == path_t.FRONTDOOR:
            ## Populate internal Item
            local_bus_op            = uvm_reg_bus_op()
            local_bus_op.kind       = access_e.PYUVM_WRITE
            local_bus_op.addr       = reg_address 
            local_bus_op.n_bits     = self._regs[reg_address].get_n_bits()
            local_bus_op.byte_en    = local_adapter.get_byte_en()
            local_bus_op.data       = data_to_be_written
            ## Parse the local bus operation with the adapter
            local_adapter.reg2bus(local_bus_op)
            ## Get the sequence and start
            local_sequence          = local_adapter.get_parent_sequence()
            ## Start the sequence on local sequencer
            await local_sequence.start(local_sequencer)
            ## Get the sequence item from the local sequence
            local_item              = uvm_sequence_item
            local_sequence.copy(local_item)
            ## Assign the response and read data back
            local_adapter.bus2reg(local_item, local_bus_op)
            ## Invoke the prediction
            if enable_auto_predict == True:
                local_predictor     = self.get_predictor() 
                local_predictor.predict(local_bus_op, check)
            else:
                error_out(self.header,"EXPLICIT_PREDICTION not implemented")

    ## process_read_operation
    async def process_read_operation(self, reg_address, path, check):
        ## Get the sequencer and the adapter
        local_adapter           = self.get_adapter()
        local_sequencer         = self.get_sequencer()
        ## check if the Path is set to BACKDOOR, FRONTDOOR or USER_FRONTDOOR
        if path == path_t.BACKDOOR:
            error_out(self.header,"BACKDOOR not implemented")
        elif path == path_t.USER_FRONTDOOR:
            error_out(self.header,"USER_FRONTDOOR not implemented")
        elif path == path_t.FRONTDOOR:
            ## Populate internal Item
            local_bus_op            = uvm_reg_bus_op()
            local_bus_op.kind       = access_e.PYUVM_READ
            local_bus_op.addr       = reg_address 
            local_bus_op.n_bits     = self._regs[reg_address].get_n_bits()
            local_bus_op.byte_en    = local_adapter.get_byte_en()
            ## Parse the local bus operation with the adapter
            local_adapter.reg2bus(local_bus_op)
            ## The get parent sequence is still not implemented hence we should be using the base sequence type for the time being 
            local_sequence          = local_adapter.get_parent_sequence()
            ## Start the sequence on local sequencer
            await local_sequence.start(local_sequencer)
            ## Get the sequence item from the local sequence
            local_item              = uvm_sequence_item
            local_sequence.copy(local_item)
            ## Assign the response and read data back
            local_adapter.bus2reg(local_item, local_bus_op)
            ## Invoke the prediction
            if enable_auto_predict == True:
                local_predictor     = self.get_predictor() 
                local_predictor.predict(local_bus_op, check)
            else:
                error_out(self.header,"EXPLICIT_PREDICTION not implemented")


