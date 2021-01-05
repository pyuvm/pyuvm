from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, RisingEdge
from tinyalu_uvm import *
import threading
import cocotb



class AluDriverBfm():
    def __init__(self, dut, label):
        self.dut = dut
        ConfigDB().set(None, "*", label, self)
        self.driver_queue = UVMQueue(maxsize=1)
        self.cmd_mon_queue = UVMQueue(maxsize=0)
        self.result_mon_queue = UVMQueue(maxsize=0)
        self.done = cocotb.triggers.Event(name="Done")

    def send_op(self, cmd):
        self.driver_queue.put(cmd)

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

    async def start(self):
       cocotb.fork(self.driver_bfm())
       cocotb.fork(self.cmd_mon_bfm())
       cocotb.fork(self.result_mon_bfm())

    async def driver_bfm(self):
        self.dut.start = 0
        self.dut.A = 0
        self.dut.B = 0
        self.dut.op = 0
        while True:
            await RisingEdge(self.dut.clk)
            if self.dut.start == 0 and self.dut.done == 0:
                try:
                    cmd = self.driver_queue.get(timeout=0.1)
                    self.dut.A = cmd.A
                    self.dut.B = cmd.B
                    self.dut.op = int(cmd.op.value)
                    self.dut.start = 1
                except queue.Empty:
                    pass
            elif self.dut.start == 1:
                if self.dut.done.value == 1:
                    self.dut.start = 0
                    self.dut.op = 0


    async def cmd_mon_bfm(self):
        prev_start = 0
        while True:
            await FallingEdge(self.dut.clk)
            if self.dut.start == 1:
                if prev_start == 0:
                    try:
                        self.cmd_mon_queue.put_nowait((int(self.dut.A), int(self.dut.B), int(self.dut.op)))
                    except queue.Full:
                        raise RuntimeError("Full analysis FIFO?")
                else:
                    pass
            prev_start = int(self.dut.start.value)

    async def result_mon_bfm(self):
        prev_done = 0
        while True:
            await FallingEdge(self.dut.clk)
            done = int(self.dut.done)
            if done == 1 and prev_done == 0:
                self.result_mon_queue.put_nowait(int(self.dut.result))
            prev_done = done

def run_uvm_test(test_name):
    root = uvm_root()
    root.run_test(test_name)


@cocotb.test()
async def test_alu(dut):
    ConfigDB().set(None, "*", "DUT", dut)
    clock = Clock(dut.clk, 2, units="us")
    cocotb.fork(clock.start())
    bfm = AluDriverBfm(dut, "ALUDRIVERBFM")
    await bfm.reset()
    cocotb.fork(bfm.start())
    await FallingEdge(dut.clk)
    test_thread = threading.Thread(target=run_uvm_test, args=("alu_test",), name="run_test")
    test_thread.start()
    await bfm.done.wait()




