import enum
import logging

import cocotb
from cocotb.triggers import FallingEdge, RisingEdge

from pyuvm import utility_classes

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


@enum.unique
class Ops(enum.IntEnum):
    """Legal ops for the TinyALU"""

    ADD = 1
    AND = 2
    XOR = 3
    MUL = 4


def alu_prediction(A, B, op, error=False):
    """Python model of the TinyALU"""
    assert isinstance(op, Ops), "The tinyalu op must be of type Ops"
    if op == Ops.ADD:
        result = A + B
    elif op == Ops.AND:
        result = A & B
    elif op == Ops.XOR:
        result = A ^ B
    elif op == Ops.MUL:
        result = A * B
    if error:
        result = result + 1
    return result


def get_int(signal):
    try:
        sig = int(signal.value)
    except ValueError:
        sig = 0
    return sig


class TinyAluBfm(metaclass=utility_classes.Singleton):
    def __init__(self):
        self.dut = cocotb.top

    # clock generation
    async def wait_clock(self, cycles=1):
        """wait for clock pulses"""
        for cycle in range(cycles):
            await RisingEdge(self.dut.clk)

    async def SW_READ(self, sw_addr: int):
        await FallingEdge(self.dut.clk)
        self.dut.valid.value = 1
        self.dut.read.value = 1
        self.dut.addr.value = sw_addr
        await FallingEdge(self.dut.clk)
        self.dut.valid.value = 0
        return int(self.dut.rdata.value)

    async def SW_WRITE(self, sw_addr: int, sw_data: int):
        await FallingEdge(self.dut.clk)
        self.dut.valid.value = 1
        self.dut.read.value = 0
        self.dut.addr.value = sw_addr
        self.dut.wdata.value = sw_data
        self.dut.wmask.value = 15
        await FallingEdge(self.dut.clk)
        self.dut.valid.value = 0

    async def reset(self):
        self.dut.reset_n.value = 0
        await self.wait_clock(1)
        self.dut.reset_n.value = 1
        await self.wait_clock(1)

    async def capture_valid(self):
        await RisingEdge(self.dut.valid)
        await FallingEdge(self.dut.clk)

    async def operation_finished(self):
        await RisingEdge(self.dut.regblock.CMD_done_q)
        await self.wait_clock(1)

    def get_addr(self):
        return self.dut.addr.value

    def get_src0(self):
        return int(self.dut.regblock.SRC_data0_q.value)

    def get_src1(self):
        return int(self.dut.regblock.SRC_data1_q.value)

    def get_op(self):
        if self.dut.regblock.CMD_op_q.value != 0:
            return Ops(int(self.dut.regblock.CMD_op_q.value))
        else:
            return 0

    def get_result(self):
        return int(self.dut.result.value)

    def get_reset(self):
        return self.dut.reset_n.value
