from cocotb.triggers import FallingEdge,  Join
import cocotb
from pyuvm import UVMQueue

class QTester():
    def __init__(self, dut) -> None:
        self.qq = UVMQueue(1)
        self.dut = dut

    async def producer(self, rr = 5):
        numbers = list(range(rr))
        numbers += [None]
        for ii in numbers:
            await self.qq.put(ii, FallingEdge(self.dut.clk))

    async def consumer(self):
        ii = await self.qq.get(FallingEdge(self.dut.clk))
        while ii is not None:
            print(ii)
            ii = await self.qq.get(FallingEdge(self.dut.clk))

@cocotb.test()
async def test_alu(dut):
    """Trying out the queue"""
    qt = QTester(dut)
    cocotb.fork(qt.producer())
    await qt.consumer()
#    Join(cocotb.fork(cocotb.fork(qt.producer()), cocotb.fork(qt.consumer())))
