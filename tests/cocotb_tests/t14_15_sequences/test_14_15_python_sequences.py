import pyuvm_unittest
from pyuvm import *
import cocotb
import time


class DataHolder(metaclass=Singleton):
    def __init__(self):
        self.datum = None
        self.dict_ = {}
        self.virtual_seq_error = None


class py1415_sequence_TestCase(pyuvm_unittest.pyuvm_TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result_list = []
        if uvm_root().has_child("my_root"):
            self.my_root = uvm_root().get_child("my_root")
        else:
            self.my_root = uvm_component("my_root", None)

    def setUp(self):
        ObjectionHandler().run_phase_done_flag = False
        self.my_root.clear_children()
        uvm_root().clear_hierarchy()
        self.result_list = []
        ObjectionHandler.clear_singletons()

    def tearDown(self):
        ObjectionHandler().run_phase_done_flag = None
        uvm_factory.clear_singletons()


    @staticmethod
    async def putter(put_method, data):
        for datum in data:
            await put_method(datum)

    async def getter(self, get_method, done_method=None):
        while True:
            datum = await get_method()
            if datum.get_name() == 'end':
                break
            if done_method is not None:
                await done_method()
            self.result_list.append(datum)

    async def response_getter(self, get_response_method, txn_id_list):
        for txn_id in txn_id_list:
            datum = await get_response_method(txn_id)
            self.result_list.append(datum)


    class ItemClass(uvm_sequence_item):
        def __init__(self, name="seq_item", txn_id=0):
            super().__init__(name)
            self.transaction_id = txn_id
            self.condition = cocotb.triggers.Event()

        def __str__(self):
            return str(self.transaction_id)

    async def run_put_get(self, put_method, get_method, done_method=None):
        cocotb.fork(self.getter(get_method, done_method))
        send_list = [self.ItemClass("5"), self.ItemClass("3"), self.ItemClass('two')]
        await self.putter(put_method, send_list + [self.ItemClass('end')])
        await cocotb.triggers.Timer(1)
        self.assertEqual(send_list, self.result_list)

    async def run_get_response(self, put_method, get_response_method):
        send_list = []
        for ii in range(5):
            send_list.append(self.ItemClass(txn_id=ii))
        cocotb.fork(self.response_getter(get_response_method, [4, 2]))
        await self.putter(put_method, send_list)
        await cocotb.triggers.Timer(1)
        result = [xx.transaction_id for xx in self.result_list]
        self.assertEqual([4, 2], result)
        self.result_list = []
        cocotb.fork(self.response_getter(get_response_method, [5]))
        await self.putter(put_method, [self.ItemClass(txn_id=10), self.ItemClass(txn_id=11)])
        await cocotb.triggers.Timer(1)
        await self.putter(put_method, [self.ItemClass(txn_id=5)])
        await cocotb.triggers.Timer(1)
        self.assertTrue(5, self.result_list[0].transaction_id)

    async def test_ResponseQueue_put_get(self):
        rq = ResponseQueue()
        try:
            await self.run_put_get(rq.put, rq.get)
        except AssertionError as ae:
            print("ERROR: ",ae)

    async def test_ResponseQueue_get_response(self):
        rq = ResponseQueue()
        try:
            await self.run_get_response(rq.put, rq.get_response)
        except AssertionError as ae:
            print("ERROR: ",ae)
            raise

    async def test_uvm_item_export_check(self):
        sip = uvm_seq_item_port("sip", self.my_root)
        bpe = uvm_blocking_put_export("bpe", self.my_root)
        with self.assertRaises(error_classes.UVMTLMConnectionError):
            sip.connect(bpe)

    async def test_uvm_item_port_put_get(self):
        sip = uvm_seq_item_port("sip", self.my_root)
        sie = uvm_seq_item_export("sie", self.my_root)
        sip.connect(sie)
        await self.run_get_response(sip.put_response, sip.get_response)

    async def test_uvm_item_port_put_req_get_next_item(self):
        sip = uvm_seq_item_port("sip", self.my_root)
        sie = uvm_seq_item_export("sie", self.my_root)
        sip.connect(sie)
        await self.run_put_get(sip.put_req, sip.get_next_item, sip.item_done)

    async def tqst_too_much_get_item(self):
        sip = uvm_seq_item_port("sip", self.my_root)
        sie = uvm_seq_item_export("sie", self.my_root)
        sip.connect(sie)
        sip.put_req(self.ItemClass(txn_id=0))
        sip.put_req(self.ItemClass(txn_id=1))
        await sip.get_next_item()
        with self.assertRaises(error_classes.UVMSequenceError):
            await sip.get_next_item()

    async def tqst_premature_item_done(self):
        sip = uvm_seq_item_port("sip", self.my_root)
        sie = uvm_seq_item_export("sie", self.my_root)
        sip.connect(sie)
        with self.assertRaises(error_classes.UVMSequenceError):
            sip.item_done()

    @staticmethod
    def waiter(condition):
        with condition:
            condition.wait()

    async def tqst_double_item_done(self):
        sip = uvm_seq_item_port("sip", self.my_root)
        sie = uvm_seq_item_export("sie", self.my_root)
        sip.connect(sie)
        sip.put_req(self.ItemClass(txn_id=0))
        sip.put_req(self.ItemClass(txn_id=1))
        item = await sip.get_next_item()
        thread = threading.Thread(target=self.waiter, args=(item.condition,), name="double_item_done")
        thread.start()
        sip.item_done()
        with self.assertRaises(error_classes.UVMSequenceError):
            sip.item_done()
        with item.condition:
            item.condition.notify_all()

    async def tqst_item_done(self):
        sip = uvm_seq_item_port("sip", self.my_root)
        sie = uvm_seq_item_export("sie", self.my_root)
        sip.connect(sie)
        req = uvm_sequence_item("req")
        rsp = uvm_sequence_item("rsp")
        # There are three threads that test item_done
        # start_item: The thread that is waiting for start_item
        # finish_item: The thread that is waiting for finish_item
        # get_response: the thread that is waiting for get_response
        finish_item_thread = threading.Thread(target=self.waiter, args=(req.finish_condition,), name="finish_item")
        rsp_thread = threading.Thread(target=self.response_getter, args=(sip.get_response, [None]), name="rsp")

        finish_item_thread.start()
        rsp_thread.start()
        time.sleep(.01)
        sip.put_req(req)
        req_back = await sip.get_next_item()
        time.sleep(.01)
        # testing start_item
        self.assertEqual(req, req_back)
        self.assertTrue(finish_item_thread.is_alive())
        self.assertTrue(rsp_thread.is_alive())
        # testing item_done
        # Should finish the finish_item thread and the rsp thread.
        sip.item_done(rsp)
        time.sleep(.01)
        self.assertEqual(rsp, self.result_list[0])
        self.assertFalse(finish_item_thread.is_alive())
        self.assertFalse(rsp_thread.is_alive())
        finish_item_thread.join()
        rsp_thread.join()

    async def tqst_uvm_sequencer_put_get_response(self):
        seqr = uvm_sequencer("seqr", self.my_root)
        sip = uvm_seq_item_port("sip", self.my_root)
        sip.connect(seqr.seq_item_export)
        self.run_get_response(sip.put_response, seqr.get_response)

    async def tqst_uvm_sequencer_put_req_get_next_item(self):
        seqr = uvm_sequencer("seqr", self.my_root)
        sip = uvm_seq_item_port("sip", self.my_root)
        sip.connect(seqr.seq_item_export)
        self.run_put_get(sip.put_req, seqr.get_next_item, sip.item_done)

    async def tqst_seqr_item_done(self):
        seqr = uvm_sequencer("seqr", self.my_root)
        sip = uvm_seq_item_port("sip", self.my_root)
        sip.connect(seqr.seq_item_export)
        req = uvm_sequence_item("req")
        rsp = uvm_sequence_item("rsp")
        # There are three threads that test item_done
        # start_item: The thread that is waiting for start_item
        # finish_item: The thread that is waiting for finish_item
        # get_response: the thread that is waiting for get_response
        finish_item_thread = threading.Thread(target=self.waiter, args=(req.finish_condition,), name="finish_item")
        rsp_thread = threading.Thread(target=self.response_getter, args=(sip.get_response, [None]), name="rsp")

        finish_item_thread.start()
        rsp_thread.start()
        time.sleep(.01)
        sip.put_req(req)
        req_back = await sip.get_next_item()
        time.sleep(.01)
        # testing start_item
        self.assertEqual(req, req_back)
        self.assertTrue(finish_item_thread.is_alive())
        self.assertTrue(rsp_thread.is_alive())
        # testing item_done
        # Should finish the finish_item thread and the rsp thread.
        sip.item_done(rsp)
        time.sleep(.01)
        self.assertEqual(rsp, self.result_list[0])
        self.assertFalse(finish_item_thread.is_alive())
        self.assertFalse(rsp_thread.is_alive())
        finish_item_thread.join()
        rsp_thread.join()

    # Time to test the sequence itself.
    async def tqst_base_virtual_sequence(self):
        class basic_seq(uvm_sequence):
            def __init__(self, name, result_list):
                super().__init__(name)
                self.rl = result_list

            def body(self):
                self.rl.append('body')

        seq = basic_seq("basic_seq", self.result_list)
        seq.start()
        self.assertEqual('body', self.result_list[0])

    class timeout_sequencer(uvm_sequencer):
        def __init__(self, name, parent):
            super().__init__(name, parent)

        async def run_phase(self):
            while True:
                try:
                    next_item = self.seq_q.get()
                    with next_item.start_condition:
                        next_item.start_condition.set()
                        next_item.start_condition.clear()
                except queue.Empty:
                    time.sleep(0.05)

    async def seq_item_port_getter(self, sip=None):
        datum = await sip.get_next_item()
        self.result_list.append(datum)

    async def tqst_simple_get_item(self):
        class seq(uvm_sequence):
            async def body(self):
                txn = uvm_sequence_item("txn")
                await self.start_item(txn)
                txn.datum = 55
                await self.finish_item(txn)

        seqr = self.timeout_sequencer("seqr", self.my_root)
        run_thread = threading.Thread(target=seqr.run_phase, name="seqr.run_phase")
        run_thread.start()
        sip = uvm_seq_item_port("sip", self.my_root)
        sip.connect(seqr.seq_item_export)
        ss = seq("ss")
        start_thread = threading.Thread(target=ss.start, args=(seqr,), name="start_thread")
        start_thread.start()
        time.sleep(.1)
        item = await sip.get_next_item()
        sip.item_done()
        ObjectionHandler().run_phase_done_flag = True
        time.sleep(.1)
        self.assertEqual(55, item.datum)

    async def tqst_run_sequence(self):
        ObjectionHandler().run_phase_done_flag = None

        class SeqItem(uvm_sequence_item):
            def __init__(self, name):
                super().__init__(name)
                self.op = None
                self.result = None

        class SeqDriver(uvm_driver):
            async def run_phase(self):
                while True:
                    op_item = self.seq_item_port.get_next_item()
                    op_item.result = op_item.data + 1
                    self.seq_item_port.item_done()

        class Seq(uvm_sequence):
            def body(self):
                op = SeqItem("op")
                self.start_item(op)
                op.data = 0
                self.finish_item(op)
                DataHolder().datum = (op.result == (op.data + 1))

        class SeqTest(uvm_test):
            def build_phase(self):
                self.seqr = uvm_sequencer("seqr", self)
                self.driver = SeqDriver("driver", self)

            def connect_phase(self):
                self.driver.seq_item_port.connect(self.seqr.seq_item_export)

            async def run_phase(self):
                self.raise_objection()
                seq = Seq("seq")
                seq.start(self.seqr)
                self.drop_objection()

        await uvm_root().run_test("SeqTest")
        self.assertTrue(DataHolder().datum)

    async def tqst_put_response(self):
        ObjectionHandler().run_phase_done_flag = None

        class SeqItem(uvm_sequence_item):
            def __init__(self, name):
                super().__init__(name)
                self.op = None
                self.result = None

        class SeqDriver(uvm_driver):
            async def run_phase(self):
                while True:
                    op_item = self.seq_item_port.get_next_item()
                    self.seq_item_port.put_response(op_item.data + 1)
                    self.seq_item_port.item_done()

        class Seq(uvm_sequence):
            def body(self):
                op = SeqItem("op")
                self.start_item(op)
                op.data = 0
                self.finish_item(op)
                result = self.get_response()
                DataHolder().datum = (result == (op.data + 1))

        class SeqTest(uvm_test):
            def build_phase(self):
                self.seqr = uvm_sequencer("seqr", self)
                self.driver = SeqDriver("driver", self)

            def connect_phase(self):
                self.driver.seq_item_port.connect(self.seqr.seq_item_export)

            async def run_phase(self):
                self.raise_objection()
                seq = Seq("seq")
                seq.start(self.seqr)
                self.drop_objection()

        await uvm_root().run_test("SeqTest")
        self.assertTrue(DataHolder().datum)

    async def tqst_item_done_response(self):
        ObjectionHandler().run_phase_done_flag = None

        class SeqItem(uvm_sequence_item):
            def __init__(self, name):
                super().__init__(name)
                self.op = None
                self.result = None

        class SeqDriver(uvm_driver):
            async def run_phase(self):
                while True:
                    op_item = self.seq_item_port.get_next_item()
                    self.seq_item_port.item_done(op_item.data + 1)

        class Seq(uvm_sequence):
            def body(self):
                op = SeqItem("op")
                self.start_item(op)
                op.data = 0
                self.finish_item(op)
                result = self.get_response()
                DataHolder().datum = (result == (op.data + 1))

        class SeqTest(uvm_test):
            def build_phase(self):
                self.seqr = uvm_sequencer("seqr", self)
                self.driver = SeqDriver("driver", self)

            def connect_phase(self):
                self.driver.seq_item_port.connect(self.seqr.seq_item_export)

            async def run_phase(self):
                self.raise_objection()
                seq = Seq("seq")
                seq.start(self.seqr)
                self.drop_objection()

        await uvm_root().run_test("SeqTest")
        self.assertTrue(DataHolder().datum)

    async def tqst_multiple_seq_runs(self):
        ObjectionHandler().run_phase_done_flag = None

        class SeqItem(uvm_sequence_item):
            def __init__(self, name):
                super().__init__(name)
                self.op = None
                self.result = None

        class SeqDriver(uvm_driver):
            async def run_phase(self):
                while True:
                    op_item = self.seq_item_port.get_next_item()
                    self.seq_item_port.item_done(op_item.data + 1)

        class Seq(uvm_sequence):
            def __init__(self, name):
                super().__init__(name)
                self.runner_name = None  # pleasing the linter

            def body(self):
                op = SeqItem("op")
                self.start_item(op)
                op.data = DataHolder().dict_[self.runner_name]
                self.finish_item(op)
                self.result = self.get_response()

        class SeqAgent(uvm_agent):
            def build_phase(self):
                self.seqr = uvm_sequencer("seqr", self)
                self.driver = SeqDriver("driver", self)
                ConfigDB().set(None, "*", "SEQR", self.seqr)

            def connect_phase(self):
                self.driver.seq_item_port.connect(self.seqr.seq_item_export)

        class SeqRunner(uvm_component):

            def connect_phase(self):
                self.seqr = self.cdb_get("SEQR")

            async def run_phase(self):
                self.raise_objection()
                seq = Seq("seq")
                seq.runner_name = self.get_name()
                seq.start(self.seqr)
                DataHolder().dict_[self.get_name()] = seq.result
                self.drop_objection()

        class SeqTest(uvm_test):
            def build_phase(self):
                self.agent = SeqAgent("seq1", self)
                DataHolder().dict_["run1"] = 5
                DataHolder().dict_["run2"] = 25
                self.run1 = SeqRunner("run1", self)
                self.run2 = SeqRunner("run2", self)

        await uvm_root().run_test("SeqTest")
        self.assertEqual(26, DataHolder().dict_["run2"])
        self.assertEqual(6, DataHolder().dict_["run1"])

    async def tqst_virtual_sequence(self):
        DataHolder().virtual_seq_error = False

        class SeqItem(uvm_sequence_item):
            def __init__(self, name):
                super().__init__(name)
                self.numb = self.result = None

            def __str__(self):
                return f"numb: {self.numb}   result: {self.result}"

        class SeqDriver(uvm_driver):
            async def run_phase(self):
                while True:
                    op_item = self.seq_item_port.get_next_item()
                    op_item.result = op_item.numb + 1
                    self.seq_item_port.item_done()

        class IncSeq(uvm_sequence):
            def body(self):
                for nn in range(5):
                    op = SeqItem("op")
                    self.start_item(op)
                    op.numb = nn
                    self.finish_item(op)
                    error = op.numb + 1 != op.result
                    if error:
                        DataHolder().virtual_seq_error = error
                        break

        class DecSeq(uvm_sequence):
            def body(self):
                for nn in range(5):
                    op = SeqItem("op")
                    self.start_item(op)
                    op.numb = nn
                    self.finish_item(op)
                    error = op.numb + 1 != op.result
                    if error:
                        DataHolder().virtual_seq_error = error
                        break

        class TopSeq(uvm_sequence):
            def body(self):
                seqr = ConfigDB().get(None, "", "SEQR")
                inc = IncSeq("inc")
                inc.start(seqr)
                if DataHolder().virtual_seq_error:
                    return
                dec = DecSeq("dec")
                dec.start(seqr)

        class SeqTest(uvm_test):
            def build_phase(self):
                self.seqr = uvm_sequencer("seqr", self)
                self.driver = SeqDriver("driver", self)
                ConfigDB().set(None, "*", "SEQR", self.seqr)

            def connect_phase(self):
                self.driver.seq_item_port.connect(self.seqr.seq_item_export)

            async def run_phase(self):
                self.raise_objection()
                self.top = TopSeq("top")
                self.top.start()
                self.drop_objection()

        await uvm_root().run_test("SeqTest")
        self.assertFalse(DataHolder().virtual_seq_error)

    async def tqst_fork_sequence(self):
        DataHolder().virtual_seq_error = False

        class SeqItem(uvm_sequence_item):
            def __init__(self, name):
                super().__init__(name)
                self.numb = self.result = None

            def __str__(self):
                return f"numb: {self.numb}   result: {self.result}"

        class SeqDriver(uvm_driver):
            async def run_phase(self):
                while True:
                    op_item = self.seq_item_port.get_next_item()
                    op_item.result = op_item.numb + 1
                    self.seq_item_port.item_done()

        class IncSeq(uvm_sequence):
            def body(self):
                for nn in range(5):
                    op = SeqItem("op")
                    self.start_item(op)
                    op.numb = nn
                    self.finish_item(op)
                    error = op.numb + 1 != op.result
                    if error:
                        DataHolder().virtual_seq_error = error
                        break

        class DecSeq(uvm_sequence):
            def body(self):
                for nn in range(5):
                    op = SeqItem("op")
                    self.start_item(op)
                    op.numb = nn
                    self.finish_item(op)
                    error = op.numb + 1 != op.result
                    if error:
                        DataHolder().virtual_seq_error = error
                        break

        class TopSeq(uvm_sequence):
            def body(self):
                seqr = ConfigDB().get(None, "", "SEQR")
                inc = IncSeq("inc")
                dec = DecSeq("dec")
                inc_thread = uvm_sequence.fork(inc, seqr)
                dec_thread = uvm_sequence.fork(dec, seqr)
                inc_thread.join()
                dec_thread.join()

        class SeqTest(uvm_test):
            def build_phase(self):
                self.seqr = uvm_sequencer("seqr", self)
                self.driver = SeqDriver("driver", self)
                ConfigDB().set(None, "*", "SEQR", self.seqr)

            def connect_phase(self):
                self.driver.seq_item_port.connect(self.seqr.seq_item_export)

            async def run_phase(self):
                self.raise_objection()
                self.top = TopSeq("top")
                self.top.start()
                self.drop_objection()

        await uvm_root().run_test("SeqTest")
        self.assertFalse(DataHolder().virtual_seq_error)
