import cocotb
import test_sw
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
from queue import Queue, Empty
import tester
import threading


class CocoTBBFM():

    def __init__(self, dut):
        self.dut = dut
        self.queue = Queue(maxsize=1)
        print(f"made queue {self.queue}")
        self.done = cocotb.triggers.Event(name="Done")

    def send_num(self, num):
        print(f"in: {num} to {self.queue}")
        self.queue.put(num)

    async def start(self):
        while True:
            await RisingEdge(self.dut.clk)
            try:
                print(f"trying to get from {self.queue}")
                numb = await self.queue.get()
                print(f"got: {numb}")
                self.dut.data_in = numb
            except Empty:
                print("not_there")
                pass

    async def reset(self):
        await FallingEdge(self.dut.clk)
        self.dut.reset_n = 0
        await FallingEdge(self.dut.clk)
        self.dut.reset_n = 1
        await RisingEdge(self.dut.clk)

    def done(self):
        self.done.set()


def run_test(test):
    tester.Tester.run_test(test)


@cocotb.test()
async def test_alu(dut):
    clock = Clock(dut.clk, 2, units="us")
    cocotb.start_soon(clock.start())
    bfm = CocoTBBFM(dut)
    stim = test_sw.Stim(5,dut, bfm)
    await bfm.reset()
    cocotb.start_soon(bfm.start())
    tt = threading.Thread(target=run_test, args=(stim.numb_gen_test,), name="Run Thread")
    tt.start()
    await bfm.done.wait()




