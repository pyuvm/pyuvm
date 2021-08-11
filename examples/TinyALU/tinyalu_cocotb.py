from cocotb.triggers import FallingEdge
import cocotb
from cocotb.queue import QueueEmpty
from tinyalu_uvm import *
"""
import debugpy
listen_host, listen_port = debugpy.listen(("localhost", 5678))
cocotb.log.info("Waiting for Python debugger attach"
" on {}:{}".format(listen_host, listen_port))
# Suspend execution until debugger attaches
debugpy.wait_for_client()
# Break into debugger for user control
breakpoint()  # or debugpy.breakpoint() on 3.6 and below
"""


class CocotbProxy:
    def __init__(self, dut):
        self.dut = dut
        self.driver_queue = UVMQueue(maxsize=1)
        self.cmd_mon_queue = UVMQueue(maxsize=0)
        self.result_mon_queue = UVMQueue(maxsize=0)

    async def send_op(self, aa, bb, op):
        await self.driver_queue.put((aa, bb, op))

    async def get_cmd(self):
        cmd = await self.cmd_mon_queue.get()
        return cmd

    async def get_result(self):
        result = await self.result_mon_queue.get()
        return result

    async def reset(self):
        await FallingEdge(self.dut.clk)
        self.dut.reset_n <= 0
        self.dut.A <= 0
        self.dut.B <= 0
        self.dut.op <= 0
        await FallingEdge(self.dut.clk)
        self.dut.reset_n <= 1
        await FallingEdge(self.dut.clk)

    async def driver_bfm(self):
        self.dut.start <= 0
        self.dut.A <= 0
        self.dut.B <= 0
        self.dut.op <= 0
        while True:
            await FallingEdge(self.dut.clk)
            if self.dut.start.value == 0 and self.dut.done.value == 0:
                try:
                    (aa, bb, op) = self.driver_queue.get_nowait()
                    self.dut.A = aa
                    self.dut.B = bb
                    self.dut.op = op
                    self.dut.start = 1
                except QueueEmpty:
                    pass
            elif self.dut.start == 1:
                if self.dut.done.value == 1:
                    self.dut.start = 0

    async def cmd_mon_bfm(self):
        prev_start = 0
        while True:
            await FallingEdge(self.dut.clk)
            try:
                start = int(self.dut.start.value)
            except ValueError:
                start = 0
            if start == 1 and prev_start == 0:
                self.cmd_mon_queue.put_nowait((int(self.dut.A),
                                               int(self.dut.B),
                                               int(self.dut.op)))
            prev_start = start

    async def result_mon_bfm(self):
        prev_done = 0
        while True:
            await FallingEdge(self.dut.clk)
            try:
                done = int(self.dut.done)
            except ValueError:
                done = 0

            if done == 1 and prev_done == 0:
                result = int(self.dut.result)
                self.result_mon_queue.put_nowait(result)
            prev_done = done


@cocotb.test()
async def test_alu(dut):
    proxy = CocotbProxy(dut)
    ConfigDB().set(None, "*", "PROXY", proxy)
    ConfigDB().set(None, "*", "DUT", dut)
    await proxy.reset()
    cocotb.fork(proxy.driver_bfm())
    cocotb.fork(proxy.cmd_mon_bfm())
    cocotb.fork(proxy.result_mon_bfm())
    await uvm_root().run_test("AluTest")
