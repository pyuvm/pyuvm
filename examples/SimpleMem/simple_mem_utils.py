"""Helpers for the SimpleMem example.

Defines the transaction enum, a thin Bus Functional Model (BFM) wrapping
the DUT pins, and a tiny golden-model memory used by the scoreboard.
The UVM-side machinery lives in ``testbench.py``.
"""

import enum
import logging

import cocotb
from cocotb.queue import Queue
from cocotb.triggers import FallingEdge, RisingEdge

from pyuvm import Singleton

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


@enum.unique
class MemOp(enum.IntEnum):
    """Transaction kinds carried on the bus."""

    READ = 0
    WRITE = 1


class SimpleMemBfm(metaclass=Singleton):
    """BFM for the SimpleMem bus.

    The driver pushes outbound transactions through ``driver_queue``; the
    BFM drives the pins and, for reads, returns the captured ``rdata``
    via ``driver_rsp_queue``.

    The monitor reads accepted transactions from ``monitor_queue``. The
    monitor BFM is intentionally independent of the driver so the agent
    can be configured PASSIVE without any driver coupling.
    """

    DATA_WIDTH = 32
    ADDR_WIDTH = 8

    def __init__(self):
        self.dut = cocotb.top
        self.driver_queue = Queue(maxsize=1)
        self.driver_rsp_queue = Queue(maxsize=1)
        self.monitor_queue = Queue(maxsize=0)

    async def reset(self):
        await FallingEdge(self.dut.clk)
        self.dut.rst_n.value = 0
        self.dut.req.value = 0
        self.dut.we.value = 0
        self.dut.addr.value = 0
        self.dut.wdata.value = 0
        # Hold reset for a couple of cycles for portability across simulators.
        for _ in range(2):
            await FallingEdge(self.dut.clk)
        self.dut.rst_n.value = 1
        await FallingEdge(self.dut.clk)

    def start_bfm(self):
        """Spawn the driver and monitor BFM tasks."""
        cocotb.start_soon(self._driver_bfm())
        cocotb.start_soon(self._monitor_bfm())

    async def send(self, op, addr, wdata):
        """Queue a transaction for the driver BFM and wait for completion."""
        await self.driver_queue.put((op, addr, wdata))
        rdata = await self.driver_rsp_queue.get()
        return rdata

    async def get_monitored(self):
        return await self.monitor_queue.get()

    async def _driver_bfm(self):
        # Default state.
        self.dut.req.value = 0
        self.dut.we.value = 0
        self.dut.addr.value = 0
        self.dut.wdata.value = 0
        while True:
            op, addr, wdata = await self.driver_queue.get()

            await FallingEdge(self.dut.clk)
            self.dut.req.value = 1
            self.dut.we.value = 1 if op == MemOp.WRITE else 0
            self.dut.addr.value = addr
            self.dut.wdata.value = wdata if op == MemOp.WRITE else 0

            # Wait until the slave grants (single-cycle handshake here, but
            # writing the loop this way keeps the BFM ready for back-pressure
            # variants of the DUT.)
            #
            # start_bfm() is only called after bfm.reset() returns, so every
            # signal we sample here is guaranteed to have a defined value —
            # int(signal.value) is strict (raises ValueError on X/Z) and any
            # surprise X mid-sim becomes a hard failure rather than a silent
            # zero, per pyuvm/pyuvm#379 review.
            while True:
                await RisingEdge(self.dut.clk)
                if int(self.dut.gnt.value) == 1:
                    rdata = int(self.dut.rdata.value) if op == MemOp.READ else 0
                    break

            await FallingEdge(self.dut.clk)
            self.dut.req.value = 0
            self.dut.we.value = 0
            self.dut.addr.value = 0
            self.dut.wdata.value = 0

            await self.driver_rsp_queue.put(rdata)

    async def _monitor_bfm(self):
        # Sample on rising edges so the monitor sees exactly what the DUT
        # commits each cycle and is fully decoupled from the driver.
        #
        # start_bfm() is only invoked after bfm.reset() has driven rst_n
        # high, so we never need to gate on rst_n here — and int() is
        # left strict so any X/Z surprise mid-sim raises ValueError
        # rather than getting silently coerced to zero.
        while True:
            await RisingEdge(self.dut.clk)
            if int(self.dut.req.value) == 1 and int(self.dut.gnt.value) == 1:
                op = MemOp.WRITE if int(self.dut.we.value) == 1 else MemOp.READ
                addr = int(self.dut.addr.value)
                wdata = int(self.dut.wdata.value) if op == MemOp.WRITE else 0
                rdata = int(self.dut.rdata.value) if op == MemOp.READ else 0
                await self.monitor_queue.put((op, addr, wdata, rdata))


class GoldenMem:
    """In-memory reference model used by the scoreboard.

    Mirrors the DUT's reset value (all zeros) and applies each observed
    WRITE; predicts the rdata for each observed READ.
    """

    def __init__(self, size):
        self._mem = [0] * size

    def write(self, addr, data):
        self._mem[addr] = data

    def predict_read(self, addr):
        return self._mem[addr]
