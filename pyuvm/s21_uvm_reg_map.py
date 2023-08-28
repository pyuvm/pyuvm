# Import Main Packages
from pyuvm import uvm_object, uvm_sequencer, uvm_sequence
from pyuvm.s24_uvm_reg_includes import uvm_error
from pyuvm.s24_uvm_reg_includes import access_e, path_t, check_t
from pyuvm.s24_uvm_reg_includes import uvm_not_implemeneted, uvm_fatal
from pyuvm.s24_uvm_reg_includes import enable_auto_predict
from pyuvm.s24_uvm_reg_includes import uvm_reg_bus_op
from pyuvm.s25_uvm_adapter import uvm_reg_adapter
from pyuvm.s26_uvm_predictor import uvm_reg_predictor
from pyuvm.s23_uvm_reg_item import uvm_reg_item

'''
    TODO: the following must be completed
    1.  implement add_mem
    2.  implement m_set_mem_offset
    3.  implement get_fields
    4.  implement get_memories
    5.  implement get_virtual_registers
    6.  implement get_virtual_fields
    7.  implement get_full_name
    8.  implement get_mem_map_info
    9.  implement get_reg_map_info
    10. implement set_base_addr
    11. implement get_size
'''


# Class declaration: uvm_reg_map
class uvm_reg_map(uvm_object):
    # Constructor
    def __init__(self, name="uvm_reg_map"):
        super().__init__(name)
        # this must be uvm_reg_block
        self._parent = None
        # this is equivalent to offset in uvm map refernce
        self._offset = 0
        self._regs = {}
        self.name = name
        self.header = name + " -- "
        self._submaps = {}
        # this is set in case of this map is a submap of another map
        self._parent_map = None
        self._is_a_submap = False
        self._reset_kind = ["SOFT", "HARD"]
        self.predictor = None

    # Function called by the REG_BLOCK create_map funcction
    # the parent value here should be a uvm_reg_block instance type
    def configure(self, parent, base_addr):
        # TODO: check if the parent is a uvm_reg_block type
        self._parent = parent
        self._offset = base_addr
        # No support for Byte_Addressing nor for Byte_en TODO: add

    # add_parent_map
    def add_parent_map(self, parent_map):
        if self._parent_map is None:
            self._parent_map = parent_map
            # if there is a parent map then this map is automatically a submap
            self._parent_map.add_submap(self)
        else:
            uvm_error(self.header, "add_parent_map -- cannot add parent map \
                if the parentmap is already set")

    # str2int
    def _str2int(self, istr: str = "") -> int:
        return int(istr, 16)

    # int2hex
    def _int2hex(self, ival: int = 0) -> str:
        return hex(ival)

    # gen_message
    def gen_message(self, txt="") -> str:
        return f"{self.header} {txt}"

    # get_parent
    def get_parent(self):
        return self._parent

    # get_offset
    def get_offset(self):
        if self._is_a_submap is True:
            return self.get_parent_map().get_offset()
        else:
            return self._offset

    # add_reg
    def add_reg(self, reg, offset: str = "0x0", rigths: str = "RW"):
        reg.add_map(self)
        sum_offset = self._str2int(offset) + self._str2int(reg.get_address())
        reg.set_access_policy(rigths)
        self._regs[self._int2hex(sum_offset)] = reg

    # get_registers
    def get_registers(self, as_dict=False):
        reg_dict = self._regs
        for m in self._submaps:
            reg_dict = {**reg_dict, **m._regs}
        if as_dict is False:
            return list(reg_dict.values())
        else:
            return reg_dict

    # get_reg_by_offset
    def get_reg_by_offset(self, offset):
        local_dict = self.get_registers(as_dict=True)
        return local_dict[offset]

    # set_predictor
    def set_predictor(self, predictor):
        if isinstance(predictor, uvm_reg_predictor):
            self.predictor = predictor
        else:
            uvm_error(self.header, "predictor should be \
                      type of uvm_reg_predictor")

    # get_predictor
    def get_predictor(self):
        if (self.predictor is None):
            # TODO: this should be only a warning since depends
            # on the prediction type
            if enable_auto_predict is True:
                uvm_error(self.header, "predictor Not set")
        else:
            return self.predictor

    # set_adapter
    def set_adapter(self, adapter):
        if isinstance(adapter, uvm_reg_adapter):
            self.adapter = adapter
        else:
            uvm_error(self.header, "adapter should be type of uvm_reg_adapter")

    # get_adapter
    def get_adapter(self):
        if (self.adapter is None):
            uvm_error(self.header, "Adapter Not set")
        else:
            return self.adapter

    # set_sequencer
    def set_sequencer(self, sequencer):
        if isinstance(sequencer, uvm_sequencer):
            self.sequencer = sequencer
        else:
            uvm_error(self.header, "setting a wrong sequencer type")

    # get_sequencer
    def get_sequencer(self):
        if (self.sequencer is None):
            uvm_error(self.header, "uvm_reg_map sequencer is not set")
        else:
            return self.sequencer

    # add_submap
    def add_submap(self, submap):
        # we cannot add a submap to a MAP that belongs to another BLK
        # maps or submaps should belong to the same BLK parent
        if (self.get_parent() != submap.get_parent()):
            uvm_error(self.header, f"add_submap -- cannot add submap \
                      {submap.get_parent()} to map {self.get_parent()} \
                      if the parent BLK is different")
        # cannot add a submap that has been already added as SUBMAP
        # of another map
        if submap._is_a_submap is True:
            uvm_error(self.header, f"add_submap -- cannot add submap \
                      {submap.get_name()} to map {self.get_name()} \
                      because the submap is already a submap of another map")
        else:
            submap._is_a_submap = True
            self._submaps[submap.get_name()] = submap
            self._submaps[submap.get_name() + "_mapping_flag"] = True
            submap.add_parent_map(self)
        # TODO: add a check for n_bytes
        # submaps should never differ in the n-bytes transfered (bus interface
        # is shared per submaps) hence there should be only 1 n-bytes supported

    # reset
    def reset(self, reset_type: str):
        if reset_type in self._reset_kind:
            for rg in self.get_registers():
                rg.reset()
        else:
            uvm_not_implemeneted(self.header, f"reset -- {reset_type} is not \
                                 mapped as type of reset \
                                 available values are {self._reset_kind}")

    # verify_map_config
    def verify_map_config(self):
        # Make sure there is a generic payload sequence for each map
        # in the model and vice-versa if this is a root sequencer
        rmap = self.get_root_map()

        if rmap.get_adapter() is None:
            uvm_fatal(self.header, f"Map {rmap.get_name()} doesn't have \
                      adapter set")

        if rmap.get_sequencer() is None:
            uvm_fatal(self.header, f"Map {rmap.get_name()} doesn't have \
                      sequencer set")

    # ------------
    # get methods
    # ------------

    # get_parent_map
    def get_parent_map(self):
        return self._parent_map

    # get_root_map
    def get_root_map(self):
        if self.get_parent_map() is None:
            return self
        else:
            return self.get_parent_map().get_root_map()

    # get_n_bytes
    def get_n_bytes(self):
        uvm_not_implemeneted(self.header, "get_n_bytes -- not implemented")

    # get_endian
    def get_endian(self):
        uvm_not_implemeneted(self.header, "get_endian -- not implemented")

    # get_submaps
    def get_submaps(self, as_dict=False):
        if as_dict is True:
            return self._submaps
        else:
            return list(self._submaps.values)

    # check integrity of process
    def check_process_integrity(self, adapter=None, reg_item=None):
        # check if the input adapter is none
        if (adapter is None):
            # TODO: here basically we should be creating a local base sequence
            #       we should be getting the sequencers from the adapter
            #       error pout if NONE and call the start ITEM using the
            #       reg_item as sequence_item is then up to the Driver to
            #       figure out how to proceed
            uvm_fatal(self.gen_message("adapter is not assigned to MAP"))
        elif isinstance(adapter, uvm_reg_adapter) is False:
            uvm_fatal(self.gen_message("adapter is not correct type"))

        # check if the reg item is set
        if (reg_item is None):
            uvm_fatal(self.gen_message("reg_item is not assigned to MAP"))
        elif isinstance(reg_item, uvm_reg_item) is False:
            uvm_fatal(self.gen_message("reg_item is not correct type"))

        # check in case the Adapter is set
        # if the parent sequence is set by User
        if adapter.get_parent_sequence() is not None:
            reg_item.set_parent_sequence(adapter.get_parent_sequence())
        else:
            # if the parent sequence is not set in teh adapter we need to
            # create a base sequence and assign it internally
            # to the reg_item there is no need to use the factory
            # we aare not gonna use the factory constructor
            base_seq = uvm_sequence("base_seq")
            reg_item.set_parent_sequence(base_seq)
            adapter.set_parent_sequence(base_seq)

    #
    # OPERATION PROCESS
    #

    # process_write_operation
    async def process_write_operation(self, reg_address, data_to_be_written,
                                      path: path_t, check: check_t):
        # Get the sequencer and the adapter
        local_adapter = self.get_adapter()
        # Build a local reg_item
        # TODO: this should come as input of the main process operation
        item = uvm_reg_item()
        item.set_kind(access_e.UVM_WRITE)
        item.set_value(data_to_be_written)
        item.set_door(path)
        item.set_map(self)
        item.set_parent_sequence(None)
        # check if we pass this point we are ready to go
        self.check_process_integrity(local_adapter, item)
        local_sequencer = self.get_sequencer()
        # check if the Path is set to BACKDOOR, FRONTDOOR or USER_FRONTDOOR
        if (path is path_t.BACKDOOR):
            uvm_not_implemeneted(self.header, "BACKDOOR not implemented")
        elif (path is path_t.USER_FRONTDOOR):
            uvm_not_implemeneted(self.header, "USER_FRONTDOOR not implemented")
        elif (path is path_t.FRONTDOOR):
            # Populate internal Item
            local_bus_op = uvm_reg_bus_op()
            local_bus_op.kind = access_e.UVM_WRITE
            local_bus_op.addr = reg_address
            local_bus_op.n_bits = self._regs[reg_address].get_reg_size()
            local_bus_op.byte_en = local_adapter.get_byte_en()
            local_bus_op.data = data_to_be_written
            # Parse the local bus operation with the adapter
            # give the ITEM once to the adpater so it can
            # eventually fecth the extension element
            local_adapter.set_item(item)
            bus_req = local_adapter.reg2bus(local_bus_op)
            local_adapter.set_item(None)
            # Get the sequence and start
            local_sequence = local_adapter.get_parent_sequence()
            # set the sequencer to the local sequence
            local_sequence.sequencer = local_sequencer
            # Start the sequence on local sequencer
            await local_sequence.start_item(bus_req)
            await local_sequence.finish_item(bus_req)
            # Get the sequence item from the local sequence
            # Assign the response and read data back
            local_adapter.bus2reg(bus_req, local_bus_op)
            # Invoke the prediction
            if (enable_auto_predict is True):
                local_predictor = self.get_predictor()
                local_predictor.predict(local_bus_op, check)
            else:
                pass
                # uvm_not_implemeneted(self.header,
                #                      "EXPLICIT_PREDICTION not implemented")
            # assign status
            return local_bus_op.status

    # process_read_operation
    async def process_read_operation(self, reg_address, path: path_t,
                                     check: check_t):
        # Get the sequencer and the adapter
        local_adapter = self.get_adapter()
        # Build a local reg_item
        # TODO: this should come as input of the main process operation
        item = uvm_reg_item()
        item.set_kind(access_e.UVM_WRITE)
        item.set_door(path)
        item.set_map(self)
        item.set_parent_sequence(None)
        # check if we pass this point we are ready to go
        self.check_process_integrity(local_adapter, item)
        local_sequencer = self.get_sequencer()
        # check if the Path is set to BACKDOOR, FRONTDOOR or USER_FRONTDOOR
        if (path is path_t.BACKDOOR):
            uvm_not_implemeneted(self.header, "BACKDOOR not implemented")
        elif (path is path_t.USER_FRONTDOOR):
            uvm_not_implemeneted(self.header, "USER_FRONTDOOR not implemented")
        elif (path is path_t.FRONTDOOR):
            # Populate internal Item
            local_bus_op = uvm_reg_bus_op()
            local_bus_op.kind = access_e.UVM_READ
            local_bus_op.addr = reg_address
            local_bus_op.n_bits = self._regs[reg_address].get_reg_size()
            local_bus_op.byte_en = local_adapter.get_byte_en()
            # Parse the local bus operation with the adapter
            # give the ITEM once to the adpater so it can
            # eventually fecth the extension element
            local_adapter.set_item(item)
            bus_req = local_adapter.reg2bus(local_bus_op)
            local_adapter.set_item(None)
            # Get the sequence and start
            local_sequence = local_adapter.get_parent_sequence()
            # set the sequencer to the local sequence
            local_sequence.sequencer = local_sequencer
            # Start the sequence on local sequencer
            await local_sequence.start_item(bus_req)
            await local_sequence.finish_item(bus_req)
            # Get the sequence item from the local sequence
            # Assign the response and read data back
            local_adapter.bus2reg(bus_req, local_bus_op)
            # Invoke the prediction
            if (enable_auto_predict is True):
                local_predictor = self.get_predictor()
                local_predictor.predict(local_bus_op, check)
            else:
                pass
                # uvm_not_implemeneted(self.header,
                #                      "EXPLICIT_PREDICTION not implemented")
            # assign status
            return local_bus_op.status, local_bus_op.data

    # print of uvm_reg_map similar to convert2string
    def __str__(self) -> str:
        return f"   {self.header} \
                    self._parent    : {self._parent} \
                    self._offset    : {self._offset} \
                    self._regs      : {self._regs} \
                    self.name       : {self.name }"
