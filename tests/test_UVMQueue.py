import pyuvm_unittest
import pyuvm.utility_classes as utility_classes
import cocotb
from cocotb.scheduler import Scheduler

class UVMQueue_TestCase (pyuvm_unittest.pyuvm_TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.EndFlag = False
        self.sleep_timer = 0.05
        self.got_data=[]

    def EndIt(self):
        return self.EndFlag

    def setUp(self):
        self.EndFlag = False
        self.uvmq = utility_classes.UVMQueue(maxsize=1)

    async def put_data(self, data_list):
        for datum in data_list:
            await self.uvmq.put(datum)

    async def get_data(self):
        while True:
            datum = await self.uvmq.get()
            self.got_data.append(datum)

    async def data_transfer(self):
        await self.put_data(self. data_list)
        await self.get_data()

    def test_data_transfer(self):
        self.data_list = [1,"2", "three", None]
        Scheduler.start_soon(self.data_transfer())
        self.assertEqual(self.data_list, self.got_data)


