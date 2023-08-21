from cocotb.triggers import RisingEdge
from pyuvm import *
from pyuvm import uvm_sequence_item
from pyuvm.s24_uvm_reg_includes import uvm_reg_bus_op


class simple_bus_item(uvm_sequence_item):
    def __init__(self, name):
        super().__init__(name)
        self.rdata = 0
        self.read = 0
        self.addr = 0
        self.wmask = 0
        self.wdata = 0


class simple_bus_driver(uvm_driver):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.item: simple_bus_item = None
        self.vif = None

    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)
        self.vif = self.cdb_get(self.get_full_name(), "vif")
        if self.vif is None:
            raise UVMError("dut handle not available in driver")

    async def drive(self, item: simple_bus_item):
        # Wait for one clock
        RisingEdge(self.vif.clk)
        # Drive valid
        self.vif.valid = 1
        # Drive addr
        self.vif.addr = item.addr
        # Drive read bit
        self.vif.read = item.read
        # Drive wmask
        self.vif.wmask = item.wmask
        self.vif.wdata = item.wdata

    async def run_phase(self):
        while True:
            item = await self.seq_item_port.get_next_item()
            await self.drive(item)
            self.ap.write(item)
            self.seq_item_port.item_done()


class simple_bus_monitor(uvm_monitor):
    def __init__(self, name, parent):
        super().__init__(name, parent)

    def build_phase(self):
        super().build_phase()
        self.ap = uvm_analysis_port("ap", self)
        self.vif = self.cdb_get(self.get_full_name(), "vif")
        if self.vif is None:
            raise UVMError("dut handle not available in driver")

    async def run_phase(self):
        while True:
            # Wait for one clock
            RisingEdge(self.vif.clk)
            if self.vif.resetn != 0:
                if self.vif.valid == 1:
                    item = simple_bus_item("item")
                    item.addr = self.vif.addr
                    item.read = self.read
                    item.wmask = self.wmask
                    item.wdata = self.wdata
                    item.rdata = self.vif.rdata
            self.logger.debug(f"MONITORED {item}")
            self.ap.write(item)


class simple_bus_agent(uvm_agent):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.seqr: uvm_sequencer = None
        self.monitor: uvm_monitor = None
        self.driver: uvm_driver = None

    def build_phase(self):
        super().build_phase()
        self.seqr = uvm_sequencer("simple_bus_seqr", self)
        self.driver = uvm_driver("simple_bus_driver", self)
        self.monitor = uvm_monitor("simple_bus_monitor", self)

    def connect_phase(self):
        super().connect_phase()
        self.driver.seq_item_port.connect(self.seqr.seq_item_export)


class simple_bus_adapter(uvm_reg_adapter):
    def __init__(self, name="uvm_reg_adapter"):
        super().__init__(name)

    # uvm_
    def reg2bus(rw: uvm_reg_bus_op) -> uvm_sequence_item:
        item = simple_bus_item("reg_seq_item")
        # Set read bit
        if rw == uvm_access_e.UVM_READ:
            item.read = 1
        else:
            item.read = 0
        # set addr
        item.addr = rw.addr
        # set write mask
        item.wmask = rw.byte_en
        # Set write data
        item.wdata = rw.data
        return item

    # uvm_reg_bus_op is not created but updated and returned
    def bus2reg(bus_item: uvm_sequence_item, rw: uvm_reg_bus_op):
        if bus_item.read == 1:
            rw.kind = uvm_access_e.UVM_READ
        else:
            rw.kind = uvm_access_e.UVM_WRITE
        # Set addr
        rw.addr = bus_item.addr
        # Set write data
        rw.data = bus_item.wdata
        # Set nbits
        rw.n_bits = bus_item.wmask.bit_count()
        # Set byte_en
        rw.byte_en = bus_item.wmask
        # Set status
        rw.status = uvm_status_e.UVM_IS_OK
        return rw
