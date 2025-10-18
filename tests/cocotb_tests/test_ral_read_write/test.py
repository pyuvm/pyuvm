# Main Packages for the entire RAL model
from random import choice, randint

import cocotb
from cocotb.types import LogicArray

from pyuvm import (
    logging,
    uvm_analysis_port,
    uvm_driver,
    uvm_env,
    uvm_root,
    uvm_sequence,
    uvm_sequence_item,
    uvm_sequencer,
    uvm_test,
)
from pyuvm.reg.uvm_reg import uvm_reg
from pyuvm.reg.uvm_reg_adapter import uvm_reg_adapter, uvm_reg_bus_op
from pyuvm.reg.uvm_reg_block import uvm_reg_block
from pyuvm.reg.uvm_reg_field import uvm_reg_field
from pyuvm.reg.uvm_reg_model import (
    uvm_access_e,
    uvm_door_e,
    uvm_endianness_e,
    uvm_status_e,
)

logger = logging.getLogger("RAL")
logger.setLevel(logging.INFO)
##############################################################################
# TESTS ENTIRE RAL READ operation
##############################################################################


# Single REG
class command_reg(uvm_reg):
    def __init__(self, name="command_reg", reg_width=32):
        super().__init__(name, reg_width)
        self.WLS = uvm_reg_field("WLS")
        self.STB = uvm_reg_field("STB")
        self.PEN = uvm_reg_field("PEN")
        self.EPS = uvm_reg_field("EPS")
        self.WLS.configure(self, 2, 0, "RW", False, (2**2) - 1, True, False, False)
        self.STB.configure(self, 1, 2, "RW", False, (2**1) - 1, True, False, False)
        self.PEN.configure(self, 1, 3, "RW", False, (2**1) - 1, True, False, False)
        self.EPS.configure(self, 4, 4, "RW", False, (2**4) - 1, True, False, False)


# Single REG
class status_reg(uvm_reg):
    def __init__(self, name="status_reg", reg_width=32):
        super().__init__(name, reg_width)
        self.DR = uvm_reg_field("DR")
        self.OE = uvm_reg_field("OE")
        self.PE = uvm_reg_field("PE")
        self.FE = uvm_reg_field("FE")
        self.DR.configure(self, 1, 0, "RO", True, 1, True, False, False)
        self.OE.configure(self, 1, 1, "RO", True, 1, True, False, False)
        self.PE.configure(self, 1, 2, "RO", True, 1, True, False, False)
        self.FE.configure(self, 1, 3, "RO", True, 1, True, False, False)


# Register model with 2 Regs and 1 Map
class cmd_ral(uvm_reg_block):
    def __init__(self, name):
        super().__init__(name)
        # do not use create map if only the default one
        # is intended to be used
        self.CMD = command_reg("CMD")
        self.ST = status_reg("ST")
        self.CMD.configure(self)
        self.ST.configure(self)
        self.def_map = self.create_map("map", 0x0, 4, uvm_endianness_e.UVM_LITTLE_ENDIAN, True)
        self.def_map.add_reg(self.CMD, 0x100c, "RW")
        self.def_map.add_reg(self.ST, 0x1014, "RO")
        self.lock_model()

# UVM Sequence item class
class cmd_item(uvm_sequence_item):
    def __init__(self, name):
        super().__init__(name)
        self.Endian = False
        self.CMD_data = LogicArray(0, 32)
        self.WR_RD = LogicArray(0, 1)
        self.write_data: int = 0
        self.read_data: int = 0
        self.addr: int = None
        self.status: bool = True

    def randomize(self):
        self.CMD_data[:] = randint(0, (2**self.CMD_data.n_bits) - 1)
        self.WR_RD[:] = randint(0, (2**self.WR_RD.n_bits) - 1)
        self.addr = choice([0x1014, 0x100c])

    def __str__(self):
        return textwrap.dedent(
            f"""
            Received CMD_data   is {self.CMD_data}
            Received WR_RD      is {self.WR_RD}
            Received write_data is {self.write_data}
            Received addr       is {self.addr}
            """
        )

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
            logger.debug(cmd)
            self.reg_target = self.driver_ral.def_map.get_reg_by_offset(cmd.addr)
            addr = self.reg_target.get_address()
            logger.debug(f"cmd_driver -- addr: {addr}")
            logger.debug(f"cmd_driver -- rights: {self.reg_target.get_rights()}")
            if cmd.WR_RD.to_unsigned() == 0:
                logger.debug("cmd_driver -- READ_CMD")
                cmd.set_read_data(5)
                self.RW = False
            else:
                logger.debug("cmd_driver -- WRITE_CMD")
                self.RW = True
            cmd_item.status = True
            if (self.RW is True) and (self.reg_target.get_rights() == "RO"):
                cmd_item.status = False
            self.seq_item_port.item_done()
            self.drop_objection()


# UVM Adaptor
class cmd_adapter(uvm_reg_adapter):
    def __init__(self, name="cmd_adapter"):
        super().__init__(name)

    def reg2bus(self, rw: uvm_reg_bus_op) -> uvm_sequence_item:
        cmdItem = cmd_item("cmdItem")
        if rw.kind == uvm_access_e.UVM_READ:
            cmdItem.WR_RD[:] = 0
            cmdItem.set_read_data(rw.data)
        else:
            cmdItem.WR_RD[:] = 1
            cmdItem.set_write_data(rw.data)
        cmdItem.addr = rw.addr
        return cmdItem

    def bus2reg(self, bus_item: uvm_sequence_item, rw: uvm_reg_bus_op):
        if bus_item.WR_RD == 0:
            rw.kind = uvm_access_e.UVM_READ
            rw.data = bus_item.read_data
        else:
            rw.kind = uvm_access_e.UVM_WRITE
            rw.data = bus_item.write_data
        rw.addr = bus_item.addr
        rw.status = uvm_status_e.UVM_IS_OK
        if cmd_item.status is False:
            rw.status = uvm_status_e.UVM_NOT_OK


# UVM Environment
class cmd_env(uvm_env):
    def build_phase(self):
        self.cmd_seqr = uvm_sequencer("cmd_seqr", self)
        self.ral = cmd_ral("ral")  # there is no need for the build
        # self.ral.lock_model()
        self.driver = cmd_driver.create("cmd_driver", self)
        self.ral_adapter = cmd_adapter("ral_adapter")

    def connect_phase(self):
        self.driver.seq_item_port.connect(self.cmd_seqr.seq_item_export)
        # assign the adapter and sequencer
        self.ral.def_map.set_sequencer(self.cmd_seqr, self.ral_adapter)
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
        for rg in registers:
            logger.debug(f"{rg.get_address()=}: {rg.get()=}")
            (status, data) = await rg.read(
                uvm_door_e.UVM_FRONTDOOR, self.ral_map
            )
            name = rg.get_name()
            addr = rg.get_address()
            logger.info(f"READ: name: {name}, addr: 0x{addr:X}, data: {data}, status: {status.name}")
            assert data == 5
            assert status == uvm_status_e.UVM_IS_OK
        for rg in registers:
            data = randint(0, 200)
            status = await rg.write(
                data, uvm_door_e.UVM_FRONTDOOR, self.ral_map
            )
            name = rg.get_name()
            addr = rg.get_address()
            rights = rg.get_rights()
            logger.info(f"WRITE: name: {name}, addr: 0x{addr:X}, data: {data}, status: {status.name}")
            if rights == "RO":
                assert status == uvm_status_e.UVM_NOT_OK
            else:
                assert status == uvm_status_e.UVM_IS_OK

        self.drop_objection()


@cocotb.test()
async def test_start(dut):
    await uvm_root().run_test("ral_test_rd")
