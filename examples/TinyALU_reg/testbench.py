from pyuvm import uvm_reg, uvm_reg_field, uvm_reg_map
from pyuvm import uvm_reg_block
from pyuvm import predict_t
from pyuvm import uvm_sequence_item
from pyuvm import uvm_sequence, uvm_report_object
from pyuvm import uvm_component, uvm_test
from pyuvm import uvm_reg_adapter
from pyuvm import uvm_reg_bus_op
from pyuvm.s24_uvm_reg_includes import access_e, status_t
from pyuvm.s24_uvm_reg_includes import path_t, check_t
from pyuvm import uvm_driver, uvm_subscriber
from pyuvm import uvm_env, uvm_sequencer, uvm_factory
from pyuvm import uvm_tlm_analysis_fifo
from pyuvm import uvm_analysis_port, UVMError
from pyuvm import UVMConfigItemNotFound
from pyuvm import UVMNotImplemented
from pyuvm import ConfigDB, uvm_root
from pyuvm import CRITICAL
from cocotb.clock import Clock
from cocotb.triggers import Join, Combine
import random
import cocotb
import pyuvm

# All testbenches use tinyalu_utils, so store it in a central
# place and add its path to the sys path so we can import it
import sys
from pathlib import Path
sys.path.append(str(Path("..").resolve()))
from tinyalu_utils import TinyAluBfm, Ops, alu_prediction  # noqa: E402

##############################################################################
# TESTS ENTIRE RAL of an ALU
# The ALU has 2 SRC input operands stored into 2 flops
# both fields are part of the SRC register (16bits) called DATA0 -DATA1
# the result of the operation is instead sent back into a 16bits register
# called RESULT
# the Operation is instead written into a regsiter called CMD:
# 1.    the first 5 (4:0) bits is the OP target
# 2.    the bit number 5 is the start if
#       not set the OPERATION is not kicked off
# 3.    the bit 6 is the DONE to be polled once the OP is accomplished
# 4.    the remaining bits are reserved and not used
##############################################################################
REG_WIDTH = 16
ALU_REG_SRC_ADDR = "0x0"
ALU_REG_SRC_ADDR_DATA0_S = 0
ALU_REG_SRC_ADDR_DATA1_S = 8
ALU_REG_SRC_ADDR_DATA0_M = 2 ** 8 - 1
ALU_REG_SRC_ADDR_DATA1_M = 2 ** 8 - 1
ALU_REG_RESULT_ADDR = "0x2"
ALU_REG_RESULT_DATA_S = 0
ALU_REG_RESULT_DATA_M = 2 ** 16 - 1
ALU_REG_CMD_ADDR = "0x4"
ALU_REG_CMD_OP_S = 0
ALU_REG_CMD_START_S = 5
ALU_REG_CMD_DONE_S = 6
ALU_REG_CMD_RESERVED_S = 7
ALU_REG_CMD_OP_M = 2 * 5 - 1
ALU_REG_CMD_START_M = 2 * 1 - 1
ALU_REG_CMD_DONE_M = 2 * 1 - 1
ALU_REG_CMD_RESERVED_M = 2 * 9 - 1


##############################################################################
# Register MOodel
##############################################################################


class ALU_REG_SRC(uvm_reg):
    def __init__(self, name="ALU_REG_SRC", reg_width=REG_WIDTH):
        super().__init__(name, reg_width)
        self.DATA0 = uvm_reg_field('DATA0')
        self.DATA1 = uvm_reg_field('DATA1')

    def build(self):
        self.DATA0.configure(self, 8, 0, 'RW', 0, 0)
        self.DATA1.configure(self, 8, 8, 'RW', 0, 0)
        self._set_lock()
        self.set_prediction(predict_t.PREDICT_DIRECT)


class ALU_REG_RESULT(uvm_reg):
    def __init__(self, name="ALU_REG_RESULT", reg_width=REG_WIDTH):
        super().__init__(name, reg_width)
        self.DATA = uvm_reg_field('DATA')

    def build(self):
        self.DATA.configure(self, 16, 0, 'RW', 0, 0)
        self._set_lock()
        self.set_prediction(predict_t.PREDICT_DIRECT)


class ALU_REG_CMD(uvm_reg):
    def __init__(self, name="ALU_REG_CMD", reg_width=REG_WIDTH):
        super().__init__(name, reg_width)
        self.OP = uvm_reg_field('OP')
        self.START = uvm_reg_field('START')
        self.DONE = uvm_reg_field('DONE')
        self.RESERVED = uvm_reg_field('RESERVED')

    def build(self):
        self.OP.configure(self, 5, 0, 'RW', 0, 1)
        self.START.configure(self, 1, 5, 'RW', 0, 1)
        self.DONE.configure(self, 1, 6, 'RO', 0, 1)
        self.RESERVED.configure(self, 8, 7, 'RW', 0, 1)
        self._set_lock()
        self.set_prediction(predict_t.PREDICT_DIRECT)


class ALU_REG_REG_BLOCK(uvm_reg_block):
    def __init__(self, name="ALU_REG_REG_BLOCK"):
        super().__init__(name)
        # do not use create map if only the default one
        # is intended to be used
        self.def_map = uvm_reg_map('map')
        self.def_map.configure(self, 0)

        #
        self.SRC = ALU_REG_SRC('SRC')
        self.SRC.configure(self, "0x0", "", False, False)
        self.def_map.add_reg(self.SRC, "0x0", "RW")

        #
        self.RESULT = ALU_REG_RESULT('RESULT')
        self.RESULT.configure(self, "0x2", "", False, False)
        self.def_map.add_reg(self.RESULT, "0x0", "RW")

        #
        self.CMD = ALU_REG_CMD('CMD')
        self.CMD.configure(self, "0x4", "", False, False)
        self.def_map.add_reg(self.CMD, "0x0", "RW")

##############################################################################
# ADAPATER
##############################################################################


class simple_bus_adapter(uvm_reg_adapter):
    def __init__(self, name="simple_bus_adapter"):
        super().__init__(name)

    # uvm_
    def reg2bus(self, rw: uvm_reg_bus_op) -> uvm_sequence_item:
        item = simple_bus_item("item")
        # Set read bit
        if (rw.kind == access_e.UVM_READ):
            item.read = 1
            item.rdata = rw.data
        else:
            item.read = 0
            item.wdata = rw.data
        item.addr = rw.addr
        return item

    # uvm_reg_bus_op is not created but updated and returned
    def bus2reg(self, bus_item: uvm_sequence_item, rw: uvm_reg_bus_op):
        if bus_item.read == 1:
            rw.kind = access_e.UVM_READ
            rw.data = bus_item.rdata
        else:
            rw.data = bus_item.wdata
            rw.kind = access_e.UVM_WRITE
        # Set addr
        rw.addr = bus_item.addr
        # Set nbits
        rw.n_bits = pyuvm.count_bits(bus_item.wmask)
        # Set byte_en
        rw.byte_en = bus_item.wmask
        # Set status
        rw.status = status_t.IS_OK
        if (bus_item.status is False):
            rw.status = status_t.IS_NOT_OK

##############################################################################
# Sequence Items
##############################################################################


class simple_bus_item(uvm_sequence_item):
    def __init__(self, name):
        super().__init__(name)
        self.rdata: int = 0
        self.read: int = 0
        self.addr: str = ""
        self.wmask: int = 0
        self.wdata: int = 0
        self.status = None

    def get_addr(self):
        return int(self.addr, 16)

    def print_item(self):
        cocotb.log.info(f"  simple_bus_item: \
                            rdata   {self.rdata} \
                            read    {self.read  } \
                            addr    {self.addr  } \
                            wmask   {self.wmask } \
                            wdata   {self.wdata } \
                            status  {self.status}")


class AluSeqItem(uvm_sequence_item):
    def __init__(self, name, aa, bb, op):
        super().__init__(name)
        self.A = aa
        self.B = bb
        self.op = Ops(op)
        self.result = 0

    def randomize_operands(self):
        self.A = random.randint(0, 255)
        self.B = random.randint(0, 255)

    def randomize(self):
        self.randomize_operands()
        self.op = random.choice(list(Ops))

    def __eq__(self, other):
        same = self.A == other.A and self.B == other.B and self.op == other.op
        return same

    def __str__(self):
        return f"{self.get_name()} : A: 0x{self.A:02x} OP: {self.op.name}"
        f" ({self.op.value}) B: 0x{self.B:02x}"


##############################################################################
# Sequence classes
##############################################################################
class AluReg_base_sequence(uvm_sequence, uvm_report_object):
    def __init__(self, name="AluReg_base_sequence"):
        super().__init__(name)
        self.ral = ConfigDB().get(None, "", "regsiter_model")
        self.map = self.ral.def_map

    async def body(self):
        raise UVMNotImplemented

    def compute_done(self, data: int):
        if ((data >> ALU_REG_CMD_DONE_S) & (ALU_REG_CMD_DONE_M) == 1):
            return True
        else:
            return False

    def seq_print(self, msg: str):
        # self.logger.info(msg)
        uvm_root().logger.info(msg)

    def print_w_access(self, reg_addr: int, wdata: int):
        reg = self.map.get_reg_by_offset(reg_addr)
        self.seq_print(f"Write access to register {reg.get_name()}"
                       f" at address {reg.get_address()} with data {wdata}")

    def print_r_access(self, reg_addr: int, read_data: int):
        reg = self.map.get_reg_by_offset(reg_addr)
        self.seq_print(f"Read access to register {reg.get_name()}"
                       f"address: {reg.get_address()} data: {read_data}")

    async def reg_write(self, reg_addr: int, write_data: int):
        target_reg = self.map.get_reg_by_offset(reg_addr)
        status = await target_reg.write(write_data,
                                        self.map,
                                        path_t.FRONTDOOR,
                                        check_t.NO_CHECK)
        return status

    async def reg_read(self, reg_addr: int):
        target_reg = self.map.get_reg_by_offset(reg_addr)
        (status, rdata) = await target_reg.read(self.ral.def_map,
                                                path_t.FRONTDOOR,
                                                check_t.NO_CHECK)
        self.seq_print(f"Finish Read with data: {rdata}")
        return status, rdata

    async def program_alu_reg(self, item: AluSeqItem):
        if (self.ral is None):
            raise UVMError("program_alu_reg -- RAL cannot be None")
        self.seq_print("#####################################################")
        self.seq_print("START -- program_alu_reg")

        # Clear
        wdata = 0
        status = await self.reg_write(ALU_REG_CMD_ADDR, wdata)
        if (status == status_t.IS_OK):
            self.seq_print("Clearing CMD")
            self.print_w_access(ALU_REG_CMD_ADDR, wdata)

        # Write the 2 Operands A and B
        wdata = ((item.B << ALU_REG_SRC_ADDR_DATA1_S) | item.A)
        status = await self.reg_write(ALU_REG_SRC_ADDR, wdata)
        if (status == status_t.IS_OK):
            self.seq_print(f"Operand A: {item.A}")
            self.seq_print(f"Operand B: {item.B}")
            self.print_w_access(ALU_REG_SRC_ADDR, wdata)

        # Write OP and START
        wdata = (1 << ALU_REG_CMD_START_S | item.op)
        status = await self.reg_write(ALU_REG_CMD_ADDR, wdata)
        if (status == status_t.IS_OK):
            self.seq_print(f"Operation is: {item.op.name}")
            self.print_w_access(ALU_REG_CMD_ADDR, wdata)

        # Read Till done is asserted
        (status, rdata) = await self.reg_read(ALU_REG_CMD_ADDR)
        while (self.compute_done(rdata) is False):
            (status, rdata) = await self.reg_read(ALU_REG_CMD_ADDR)
        self.print_r_access(ALU_REG_CMD_ADDR, rdata)

        # Read the result
        (status, rdata) = await self.reg_read(ALU_REG_RESULT_ADDR)
        self.print_r_access(ALU_REG_RESULT_ADDR, rdata)
        # Load result back
        item.result = rdata
        self.seq_print("#####################################################")


class RandomSeq(AluReg_base_sequence):
    async def body(self):
        for op in list(Ops):
            cmd_tr = AluSeqItem("cmd_tr", None, None, op)
            cmd_tr.randomize_operands()
            await self.program_alu_reg(cmd_tr)


class MaxSeq(AluReg_base_sequence):
    async def body(self):
        for op in list(Ops):
            cmd_tr = AluSeqItem("cmd_tr", 0xff, 0xff, op)
            await self.program_alu_reg(cmd_tr)


class TestAllSeq(AluReg_base_sequence):
    async def body(self):
        random = RandomSeq("random")
        await random.start()


class TestAllForkSeq(AluReg_base_sequence):
    async def body(self):
        random = RandomSeq("random")
        max = MaxSeq("max")
        random_task = cocotb.start_soon(random.start())
        max_task = cocotb.start_soon(max.start())
        await Combine(Join(random_task), Join(max_task))


class OpSeq(AluReg_base_sequence):
    def __init__(self, name, aa, bb, op):
        super().__init__(name)
        self.aa = aa
        self.bb = bb
        self.op = Ops(op)

    async def body(self):
        cmd_tr = AluSeqItem("cmd_tr", self.aa, self.bb, self.op)
        await self.program_alu_reg(cmd_tr)
        self.result = cmd_tr.result


async def do_add(seqr, aa, bb):
    seq = OpSeq("seq", aa, bb, Ops.ADD)
    await seq.start(seqr)
    return seq.result


async def do_and(seqr, aa, bb):
    seq = OpSeq("seq", aa, bb, Ops.AND)
    await seq.start(seqr)
    return seq.result


async def do_xor(seqr, aa, bb):
    seq = OpSeq("seq", aa, bb, Ops.XOR)
    await seq.start(seqr)
    return seq.result


async def do_mul(seqr, aa, bb):
    seq = OpSeq("seq", aa, bb, Ops.MUL)
    await seq.start(seqr)
    return seq.result


class FibonacciSeq(uvm_sequence, uvm_report_object):
    def __init__(self, name):
        super().__init__(name)

    async def body(self):
        self.seqr = ConfigDB().get(None, "", "SEQR")
        prev_num = 0
        cur_num = 1
        fib_list = [prev_num, cur_num]
        for _ in range(7):
            sum = await do_add(self.seqr, prev_num, cur_num)
            fib_list.append(sum)
            prev_num = cur_num
            cur_num = sum
        self.logger.info("Fibonacci Sequence: " + str(fib_list))
        uvm_root().set_logging_level_hier(CRITICAL)


##############################################################################
# DRIVER
##############################################################################


class Driver(uvm_driver):
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    def start_of_simulation_phase(self):
        self.bfm = TinyAluBfm()

    async def launch_tb(self):
        await self.bfm.reset()

    async def run_phase(self):
        await self.launch_tb()
        while True:
            cmd = await self.seq_item_port.get_next_item()
            if (cmd.read == 0):
                await self.bfm.SW_WRITE(cmd.get_addr(), cmd.wdata)
            else:
                read_data = await self.bfm.SW_READ(cmd.get_addr())
                cmd.rdata = read_data
            self.seq_item_port.item_done()

##############################################################################
# COVERAGE
##############################################################################


class Coverage(uvm_subscriber):
    def end_of_elaboration_phase(self):
        self.cvg = set()

    def write(self, cmd):
        self.logger.info(f"Coverage receiving command {cmd}")
        op = cmd.op
        self.cvg.add(op)

    def report_phase(self):
        try:
            disable_errors = ConfigDB().get(
                self, "", "DISABLE_COVERAGE_ERRORS")
        except UVMConfigItemNotFound:
            disable_errors = False
        if not disable_errors:
            if len(set(Ops) - self.cvg) > 0:
                self.logger.critical(f"Functional coverage error."
                                     f" Missed: {set(Ops)-self.cvg}")
                assert False
            else:
                self.logger.info("Covered all operations")
                assert True

##############################################################################
# Monitor
##############################################################################


class Monitor(uvm_component):
    def __init__(self, name, parent,):
        super().__init__(name, parent)

    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)
        self.bfm = TinyAluBfm()
        self.item = AluSeqItem("Monitor_Item", None, None, Ops.MUL)
        self.done = False

    async def run_phase(self):
        while True:
            # Wait for one clock
            await self.bfm.wait_clock()
            if self.bfm.get_reset() == 1:
                self.done = False
                await self.bfm.capture_valid()
                self.logger.info("Monitor Got a Valid")
                if (self.bfm.get_addr() == ALU_REG_SRC_ADDR):
                    self.logger.info("Monitored ALU SRC ADDR")
                    self.item.A = self.bfm.get_src0()
                    self.item.B = self.bfm.get_src1()
                if (self.bfm.get_addr() == ALU_REG_CMD_ADDR):
                    self.logger.info("Monitored ALU CMD")
                    self.item.op = self.bfm.get_op()
                if (self.bfm.get_addr() == ALU_REG_RESULT_ADDR):
                    self.logger.info("Monitored ALU RESULT")
                    self.item.result = self.bfm.get_result()
                    self.done = True
                if (self.done is True):
                    self.logger.info("Monitor Finished Operation")
                    self.ap.write(self.item)

##############################################################################
# SCOREBOARD
##############################################################################


class Scoreboard(uvm_component):
    def build_phase(self):
        self.result_fifo = uvm_tlm_analysis_fifo("result_fifo", self)

    async def run_phase(self):
        try:
            self.errors = ConfigDB().get(self, "", "CREATE_ERRORS")
        except UVMConfigItemNotFound:
            self.errors = False

        if (self.errors is True):
            self.logger.info("Alu Error negative scenario")

        while True:
            cmd = await self.result_fifo.get()
            (A, B, op_numb, actual_result) = (cmd.A, cmd.B, cmd.op, cmd.result)
            predicted_result = alu_prediction(A, B, op_numb, self.errors)
            if (self.errors is True):
                if predicted_result != actual_result:
                    self.logger.info(f"Error scenario PASSED: 0x{A:02x} "
                                     f"{op_numb.name} "
                                     f"0x{B:02x} = "
                                     f"0x{actual_result:04x}")
                else:
                    self.logger.error(f"Error scenario FAILED: 0x{A:02x} "
                                      f"{op_numb.name} "
                                      f"0x{B:02x} "
                                      f"= 0x{actual_result:04x} "
                                      f"expected 0x{predicted_result:04x}")
            else:
                if predicted_result == actual_result:
                    self.logger.info(f"PASSED: 0x{A:02x} "
                                     f"{op_numb.name} "
                                     f"0x{B:02x} = "
                                     f"0x{actual_result:04x}")
                else:
                    self.logger.error(f"FAILED: 0x{A:02x} "
                                      f"{op_numb.name} "
                                      f"0x{B:02x} "
                                      f"= 0x{actual_result:04x} "
                                      f"expected 0x{predicted_result:04x}")

    def check_phase(self):
        if (self.result_fifo.size() != 0):
            self.logger.critical(f"TEST FAILED main result fifo is not"
                                 f" Empty, there are {self.result_fifo.size()}"
                                 f" left to be compared")

##############################################################################
# ENVIRONMENT
##############################################################################


class AluEnv(uvm_env):
    def build_phase(self):
        self.seqr = uvm_sequencer("seqr", self)
        self.driver = Driver.create("driver", self)
        self.monitor = Monitor("monitor", self)
        self.coverage = Coverage("coverage", self)
        self.scoreboard = Scoreboard("scoreboard", self)
        self.reg_adapter = simple_bus_adapter("reg_adapter")
        self.reg_block = ALU_REG_REG_BLOCK("reg_block")

    def connect_phase(self):
        self.driver.seq_item_port.connect(self.seqr.seq_item_export)
        self.monitor.ap.connect(self.coverage.analysis_export)
        self.monitor.ap.connect(self.scoreboard.result_fifo.analysis_export)
        self.reg_block.def_map.set_sequencer(self.seqr)
        self.reg_block.def_map.set_adapter(self.reg_adapter)
        # share SEQR and RAL across the TB if needed
        ConfigDB().set(None, "*", "SEQR", self.seqr)
        ConfigDB().set(None, "*", "regsiter_model", self.reg_block)

##############################################################################
# TESTS
##############################################################################


@pyuvm.test()
class AluTest(uvm_test):
    """Test ALU with random and max values"""

    def build_phase(self):
        self.env = AluEnv("env", self)

    def end_of_elaboration_phase(self):
        self.test_all = TestAllSeq.create("test_all")

    async def run_phase(self):
        self.raise_objection()

        if cocotb.LANGUAGE == "verilog":
            # Start clock
            clock = Clock(cocotb.top.clk, 1, units="ns")
            cocotb.start_soon(clock.start())

        await self.test_all.start()
        self.drop_objection()


# @pyuvm.test()
# class ParallelTest(AluTest):
#     """Test ALU random and max forked"""

#     def build_phase(self):
#         uvm_factory().set_type_override_by_type(TestAllSeq, TestAllForkSeq)
#         super().build_phase()


@pyuvm.test()
class FibonacciTest(AluTest):
    """Run Fibonacci program"""

    def build_phase(self):
        ConfigDB().set(None, "*", "DISABLE_COVERAGE_ERRORS", True)
        uvm_factory().set_type_override_by_type(TestAllSeq, FibonacciSeq)
        return super().build_phase()


@pyuvm.test()
class AluTestErrors(AluTest):
    """Test ALU with errors on all operations"""

    def build_phase(self):
        super().build_phase()
        ConfigDB().set(None, "*", "CREATE_ERRORS", True)
