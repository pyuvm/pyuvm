from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
from cocotb.queue import QueueEmpty
import cocotb

class ProdCon():
    def __init__(self, dut) -> None:
        self.dut = dut
        self.qq = cocotb.queue.Queue(maxsize = 1)

    async def producer(self, rangenum = 5):
        for ii in range(rangenum):
            print("Putting ", ii)
            await self.qq.put(ii)
    
    async def consumer(self):
        while True:
            print("start clock wait")
            await FallingEdge(self.dut.clk)
            print("saw falling edge")
            datum = await self.qq.get()
            print(datum)

@cocotb.test()
async def stuck(dut):
    """ test clock hang"""
    pc = ProdCon(dut)
    await pc.producer()
    await pc.consumer()
