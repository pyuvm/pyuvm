from cocotb.triggers import FallingEdge
import cocotb
from cocotb.queue import Queue

class ProdCon():
    def __init__(self, dut) -> None:
        self.dut = dut
        self.qq = Queue(maxsize = 1)
        self.ev = cocotb.triggers.Event()

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
            if datum == 4:
                self.ev.set()

    async def go(self):
        cocotb.fork(self.producer())
        cocotb.fork(self.consumer())
        await self.ev.wait()

@cocotb.test()
async def stuck(dut):
    """ test clock hang"""
    pc = ProdCon(dut)
    await pc.go()
