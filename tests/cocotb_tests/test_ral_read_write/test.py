# Main Packages for the entire RAL model
from pyuvm import *
from cocotb.binary import BinaryValue
from cocotb import test
from random import randint
from random import choice

##############################################################################
# TESTS ENTIRE RAL READ operation
##############################################################################


# Single REG
class command_reg(uvm_reg):
    def __init__(self, name="command_reg", reg_width=32):
        super().__init__(name, reg_width)
        self.WLS = uvm_reg_field('WLS')
        self.STB = uvm_reg_field('STB')
        self.PEN = uvm_reg_field('PEN')
        self.EPS = uvm_reg_field('EPS')

    def build(self):
        self.WLS.configure(self, 2, 0, 'RW', 0, (2**2) - 1)
        self.STB.configure(self, 1, 2, 'RW', 0, (2**1) - 1)
        self.PEN.configure(self, 1, 3, 'RW', 0, (2**1) - 1)
        self.EPS.configure(self, 4, 4, 'RW', 0, (2**4) - 1)
        self._set_lock()

# Single REG
class status_reg(uvm_reg):
    def __init__(self, name="status_reg", reg_width=32):
        super().__init__(name, reg_width)
        self.DR = uvm_reg_field('DR')
        self.OE = uvm_reg_field('OE')
        self.PE = uvm_reg_field('PE')
        self.FE = uvm_reg_field('FE')

    def build(self):
        self.DR.configure(self, 1, 0, 'RO', 1, 1)
        self.OE.configure(self, 1, 1, 'RO', 1, 1)
        self.PE.configure(self, 1, 2, 'RO', 1, 1)
        self.FE.configure(self, 1, 3, 'RO', 1, 1)
        self._set_lock()

# Register model with 2 Regs and 1 Map
class cmd_ral(uvm_reg_block):
    def __init__(self, name):
        super().__init__(name)
        # do not use create map if only the default one
        # is intended to be used
        self.def_map = uvm_reg_map('map')
        self.def_map.configure(self, 0)
        self.CMD = command_reg('CMD')
        self.CMD.configure(self, "0x100c", "", False, False)
        self.def_map.add_reg(self.CMD, "0x0", "RW")
        self.ST = status_reg('ST')
        self.ST.configure(self, "0x1014", "", False, False)
        self.def_map.add_reg(self.ST, "0x0", "RO")


# UVM Sequence item class
class cmd_item(uvm_sequence_item):
    def __init__(self, name):
        super().__init__(name)
        self.Endian = False
        self.CMD_data = BinaryValue(0, 32, self.Endian)
        self.WR_RD = BinaryValue(0, 1, self.Endian)
        self.write_data: int = 0
        self.read_data: int = 0
        self.addr: str = ""
        self.status: bool = True

    def randomize(self):
        self.CMD_data.integer = randint(0, (2**self.CMD_data.n_bits) - 1)
        self.WR_RD.integer = randint(0, (2**self.WR_RD.n_bits) - 1)
        self.addr = choice(["0x1014", "0x100c"])

    def print_cmd(self):
        print(f"Received CMD_data   is {self.CMD_data.get_value()}")
        print(f"Received WR_RD      is {self.WR_RD.get_value()}")
        print(f"Received write_data is {self.write_data}")
        print(f"Received addr       is {self.addr}")

    def set_write_data(self, value: int):
        self.write_data = value

    def set_read_data(self, value: int):
        self.read_data = value

    def set_addr(self, value: int):
        self.addr = value

    def set_status(self, st):
        self.status = st

    def get_status(self):
        return self.status


# UVM Sequence
class random_cmd_seq(uvm_sequence):
    def __init__(self, name="random_cmd_seq"):
        super().__init__(name)
        self.iteranctions = 0

    async def body(self):
        for i in range(self.iteranctions):
            cmd = cmd_item(f"cmd{self.iteranctions}")
            await self.start_item(cmd)
            cmd.randomize()
            await self.finish_item(cmd)


# UVM Driver
class cmd_driver(uvm_driver):
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)
        self.driver_ral = None
        self.reg_target = None

    async def run_phase(self):
        while True:
            cmd = await self.seq_item_port.get_next_item()
            self.raise_objection()
            cmd.print_cmd()
            self.reg_target = self.driver_ral.def_map.get_reg_by_offset(cmd.addr)
            if self.reg_target.get_address() == "0x1014":
                print("cmd_driver -- addr: 0x1014")
            else:
                print("cmd_driver -- addr: 0x100c")
            print(f"cmd_driver -- policy: {self.reg_target.get_access_policy()}")
            if (cmd.WR_RD.integer == 0):
                print("cmd_driver -- READ_CMD")
                cmd.set_read_data(5)
                self.RW = False
            else:
                print("cmd_driver -- WRITE_CMD")
                self.RW = True
            cmd_item.status=True
            if ((self.RW is True) and (self.reg_target.get_access_policy() == "RO")):
                cmd_item.status=False
            self.seq_item_port.item_done()
            self.drop_objection()


# UVM Adaptor
class cmd_adapter(uvm_reg_adapter):
    def __init__(self, name="cmd_adapter"):
        super().__init__(name)

    def reg2bus(self, rw: uvm_reg_bus_op) -> uvm_sequence_item:
        cmdItem = cmd_item("cmdItem")
        if rw.kind == access_e.UVM_READ:
            cmdItem.WR_RD.integer = 0
            cmdItem.set_read_data(rw.data)
        else:
            cmdItem.WR_RD.integer = 1
            cmdItem.set_write_data(rw.data)
        cmdItem.addr = rw.addr
        return cmdItem

    def bus2reg(self, bus_item: uvm_sequence_item, rw: uvm_reg_bus_op):
        if (bus_item.WR_RD == 0):
            rw.kind = access_e.UVM_READ
            rw.data = bus_item.read_data
        else:
            rw.kind = access_e.UVM_WRITE
            rw.data = bus_item.write_data
        rw.addr = bus_item.addr
        rw.status = status_t.IS_OK
        if (cmd_item.status is False):
            rw.status = status_t.IS_NOT_OK

# UVM Environment
class cmd_env(uvm_env):
    def build_phase(self):
        self.cmd_seqr = uvm_sequencer("cmd_seqr", self)
        self.ral = cmd_ral("ral")  # there is no need for the build
        self.driver = cmd_driver.create("cmd_driver", self)
        self.ral_adapter = cmd_adapter("ral_adapter")

    def connect_phase(self):
        self.driver.seq_item_port.connect(self.cmd_seqr.seq_item_export)
        # assign the adapter and sequencer
        self.ral.def_map.set_adapter(self.ral_adapter)
        self.ral.def_map.set_sequencer(self.cmd_seqr)
        # connect the Driver RAL to the ENV ral
        self.driver.driver_ral = self.ral


# UVM Test
class ral_test_rd(uvm_test):
    def build_phase(self):
        self.environment = cmd_env.create("environment", self)

    async def run_phase(self):
        self.raise_objection()
        self.ral_map = self.environment.ral.def_map
        self.ral_map.reset("HARD")
        registers = self.environment.ral.def_map.get_registers()
        print(registers)
        for rg in registers:
            print(rg.get_address())
            if (isinstance(rg, uvm_reg)):
                (status, data) = await rg.read(self.ral_map,
                                               path_t.FRONTDOOR,
                                               check_t.NO_CHECK)
                print(f"Status: {status.name} -- Data: {data}")
        for rg in registers:
            if (isinstance(rg, uvm_reg)):
                wdata = randint(0 ,200)
                status = await rg.write(wdata,
                                        self.ral_map,
                                        path_t.FRONTDOOR,
                                        check_t.NO_CHECK)
                print(f"Status: {status.name} -- Data: {wdata}")
        self.drop_objection()

@test()
async def test_start(dut):
    await uvm_root().run_test("ral_test_rd")
