from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, Timer
from cocotb.queue import QueueEmpty
import cocotb
from cocotb.queue import QueueEmpty
from tinyalu_uvm import *


class CocotbProxy:
    def __init__(self, dut):
        self.dut = dut
        tr = FallingEdge(dut.clk)
        self.driver_queue = UVMQueue(maxsize=1, trigger=tr)
        self.cmd_mon_queue = UVMQueue(maxsize=0, trigger=tr)
        self.result_mon_queue = UVMQueue(maxsize=0, trigger=tr)
        self.done = cocotb.triggers.Event(name="Done")

    async def send_op(self, aa, bb, op):
        print("IN SEND OP")
        while True:
            await FallingEdge(self.dut.clk)
            print("LOOPING ON CLOCK IN SEND_OP")
            try:
                print("SENDING ",(aa,bb,op))
                self.driver_queue.put_nowait((aa, bb, op))
                print("SENT COMMAND", (aa, bb, op))
                return
            except QueueFull:
                print("QUEUE FULL")
                continue

    async def get_cmd(self):
        while True:
            await FallingEdge(self.dut.clk)
            try:
                cmd =  self.cmd_mon_queue.get_nowait()
                return cmd
            except QueueEmpty:
                continue


    async def get_result(self):
        while True:
            await FallingEdge(self.dut.clk)
            try:
                cmd =  self.result_mon_queue.get_nowait()
                return cmd
            except QueueEmpty:
                continue

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
        self.dut.start = self.dut.A = self.dut.B = 0
        self.dut.op = 0
        while True:
            await FallingEdge(self.dut.clk)
            if self.dut.start.value == 0 and self.dut.done.value == 0:
                try:
                    (aa, bb, op) = self.driver_queue.get_nowait()
                    print(f"GOT ITEM: {aa}, {bb}, {op}")
                    self.dut.A = aa
                    self.dut.B = bb
                    self.dut.op = op
                    self.dut.start = 1
                except QueueEmpty:
                    continue
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
                self.cmd_mon_queue.put_nowait((int(self.dut.A), int(self.dut.B), int(self.dut.op)))
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
                print(f"PUT RESULT: {int(self.dut.result)} ")
                self.result_mon_queue.put_nowait(int(self.dut.result))
            prev_done = done


# noinspection PyArgumentList
@cocotb.test()
async def test_alu(dut):
    proxy = CocotbProxy(dut)
    ConfigDB().set(None, "*", "PROXY", proxy)
    ConfigDB().set(None, "*", "DUT", dut)
    await proxy.reset()
    cocotb.fork(proxy.driver_bfm())
    cocotb.fork(proxy.cmd_mon_bfm())
    cocotb.fork(proxy.result_mon_bfm())
    cocotb.fork(uvm_root().run_test("AluTest", FallingEdge(dut.clk)))
    await ClockCycles(dut.clk, 100)



