import pyuvm_unittest
import threading
import time
import pyuvm.utility_classes as utility_classes

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
        self.uvmq = utility_classes.UVMQueue(maxsize=1,  time_to_die=self.EndIt, sleep_time=self.sleep_timer)

    def put_data(self, data_list, block=True, timeout=None, ):
        for datum in data_list:
            self.uvmq.put(datum, block=block, timeout=timeout)

    def get_data(self, block=True, timeout=None):
        while True:
            datum = self.uvmq.get(block=block,timeout=timeout)
            self.got_data.append(datum)

    def test_put_Queue_timeout(self):
        put_thread = threading.Thread(target=self.put_data, args=([1,2,3],), name="put_data")
        put_thread.start()
        time.sleep(self.sleep_timer * 4)
        self.assertTrue(put_thread.is_alive())
        self.EndFlag = True
        time.sleep(self.sleep_timer * 4)
        self.assertFalse(put_thread.is_alive())

    def test_get_Queue_timeout(self):
        get_thread = threading.Thread(target=self.get_data, name="get_data")
        get_thread.start()
        time.sleep(self.sleep_timer * 4)
        self.assertTrue(get_thread.is_alive())
        self.EndFlag = True
        time.sleep(self.sleep_timer * 4)
        self.assertFalse(get_thread.is_alive())

    def test_data_transfer(self):
        data_list = [1,"2", "three", None]
        put_thread = threading.Thread(target=self.put_data, args=(data_list,), name="put_data")
        get_thread = threading.Thread(target=self.get_data, name="get_data")
        put_thread.start()
        time.sleep(self.sleep_timer * 4)
        self.assertTrue(put_thread.is_alive())
        get_thread.start()
        time.sleep(self.sleep_timer * 4)
        self.assertFalse(put_thread.is_alive())
        self.assertTrue(get_thread.is_alive())
        self.assertEqual(data_list, self.got_data)
        self.EndFlag=True
        time.sleep(self.sleep_timer * 4)
        self.assertFalse(get_thread.is_alive())




