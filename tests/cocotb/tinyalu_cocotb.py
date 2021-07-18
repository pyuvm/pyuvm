from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
import cocotb
from tinyalu_uvm import *
import pyuvm.utility_classes as utility_classes
import time
import asyncio.queues
from pyuvm import *


class CocotbProxy:
    def __init__(self, dut, label):
        self.dut = dut
        ConfigDB().set(None, "*", label, self)
        self.driver_queue = UVMQueue(maxsize=1)
        self.cmd_mon_queue = UVMQueue(maxsize=0)
        self.result_mon_queue = UVMQueue(maxsize=0)
        self.done = cocotb.triggers.Event(name="Done")

    def send_op(self, aa, bb, op):
        self.driver_queue.put((aa, bb, op))

    def get_cmd(self):
        return self.cmd_mon_queue.get()

    def get_result(self):
        return self.result_mon_queue.get()

    async def reset(self):
        await FallingEdge(self.dut.clk)
        self.dut.reset_n = 0
        self.dut.A = 0
        self.dut.B = 0
        self.dut.op = 0
        await FallingEdge(self.dut.clk)
        self.dut.reset_n = 1
        await FallingEdge(self.dut.clk)

    async def driver_bfm(self):
        self.dut.start = self.dut.A = self.dut.B = 0
        self.dut.op = 0
        while True:
            await FallingEdge(self.dut.clk)
            if self.dut.start == 0 and self.dut.done == 0:
                try:
                    (aa, bb, op) = self.driver_queue.get_nowait()
                    time.sleep(0.1)
                    self.dut.A = aa
                    self.dut.B = bb
                    self.dut.op = op
                    self.dut.start = 1
                except queue.Empty:
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
                self.result_mon_queue.put_nowait(int(self.dut.result.value))
            prev_done = done


def run_uvm_test(test_name):
    root = uvm_root()
    root.run_test(test_name)


async def sleep(delay):
    time.sleep(delay)


# noinspection PyArgumentList,PyAsyncCall
# @cocotb.test()
async def test_alu(dut):
    clock = Clock(dut.clk, 2, units="us")
    cocotb.fork(clock.start())
    proxy = CocotbProxy(dut, "PROXY")
    await proxy.reset()
    cocotb.fork(proxy.driver_bfm())
    cocotb.fork(proxy.cmd_mon_bfm())
    cocotb.fork(proxy.result_mon_bfm())
    await FallingEdge(dut.clk)
    test_thread = threading.Thread(target=run_uvm_test, args=("CocotbAluTest",), name="run_test")
    test_thread.start()
    await proxy.done.wait()
    await FallingEdge(dut.clk)

# noinspection PyArgumentList,PyAsyncCall
@cocotb.test()
async def test_queue(dut):
    "Test basic QUEUE functions"
    qq = utility_classes.UVMQueue(maxsize=1)
    await qq.put(5)
    got = await qq.get()
    assert got == 5
    await qq.put("x")
    peeked = await qq.peek()
    assert "x" == peeked
    got = await qq.get()
    qq.put_nowait(5)
    got = qq.get_nowait()
    assert got == 5
    qq.put_nowait("x")
    peeked = qq.peek_nowait()
    assert "x" == peeked
    got = qq.get_nowait()
    assert got == peeked

async def delay_put(qq, delay, data):
    for dd in data:
        await sleep(delay)
        await qq.put(dd)

async def delay_get(qq, delay):
    ret_dat = []
    await sleep(delay)
    datum = await qq.get()
    ret_dat.append(datum)
    while datum is not None:
        await sleep(delay)
        datum = await qq.get()
        ret_dat.append(datum)
    return ret_dat

async def delay_peek(qq, delay):
    ret_dat = []
    await sleep(delay)
    return await qq.peek()

@cocotb.test()
async def wait_on_queue(dut):
    """Test put and get with waits"""
    clock = Clock(dut.clk, 2, units="us") #make the simualtor wait
    cocotb.fork(clock.start())
    qq = utility_classes.UVMQueue(maxsize=1)
    send_data = [.01,"two", 3, None]
    cocotb.fork(delay_put(qq, .01, send_data))
    got_data = await delay_peek(qq, .01)
    assert got_data == .01
    got_data = await delay_get(qq, .01)

@cocotb.test()
async def nowait_tests(dut):
    """Test the various nowait flavors"""
    qq = utility_classes.UVMQueue(maxsize=1)
    await qq.put(5)
    try:
        qq.put_nowait(6)
        assert False
    except asyncio.queues.QueueFull:
        pass
    try:
        xx = qq.peek_nowait()
        assert xx == 5
    except asyncio.queues.QueueEmpty:
        assert False
    try:
        xx = qq.get_nowait()
        assert xx == 5
    except asyncio.queues.QueueEmpty:
        assert False
    try:
        xx = qq.peek_nowait()
        assert False
    except asyncio.queues.QueueEmpty:
        pass
    try:
        xx = qq.get_nowait()
        assert False
    except asyncio.queues.QueueEmpty:
        pass







