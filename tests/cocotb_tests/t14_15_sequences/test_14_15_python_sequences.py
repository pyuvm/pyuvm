
import uvm_unittest
from pyuvm import *
import cocotb
import asyncio
from cocotb.utils import get_sim_time
from cocotb.triggers import Timer


class DataHolder(metaclass=Singleton):
    def __init__(self):
        self.datum = None
        self.dict_ = {}
        self.virtual_seq_error = None


class SeqItem(uvm_sequence_item):
    def __init__(self, name):
        super().__init__(name)
        self.op = None
        self.result = None
        self.data = 0

    def __str__(self):
        return f"id: {id(self)} data: {self.data}   result: {self.result}"


class ItemDoneRespSeqDriver(uvm_driver):
    async def run_phase(self):
        while True:
            op_item = await self.seq_item_port.get_next_item()
            op_item.data += 1
            self.seq_item_port.item_done(op_item)


class HandleRespSeqDriver(uvm_driver):
    async def run_phase(self):
        while True:
            op_item = await self.seq_item_port.get_next_item()
            op_item.result = op_item.data + 1
            self.seq_item_port.item_done()


class py1415_sequence_TestCase(uvm_unittest.uvm_TestCase):

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

    def tearDown(self):
        ObjectionHandler().run_phase_done_flag = None

    @staticmethod
    async def putter(put_method, data):
        for datum in data:
            if asyncio.iscoroutinefunction(put_method):
                await put_method(datum)
            else:
                put_method(datum)

    async def getter(self, get_method, done_method=None):
        while True:
            datum = await get_method()
            if datum.get_name() == 'end':
                break
            if done_method is not None:
                done_method()
            self.result_list.append(datum)

    async def response_getter(self, get_response_method, txn_id_list=[]):
        if len(txn_id_list) == 0:
            self.result_list = [await get_response_method(None)]
        else:
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
        cocotb.start_soon(self.getter(get_method, done_method))
        send_list = [self.ItemClass("5"),
                     self.ItemClass("3"), self.ItemClass('two')]
        await self.putter(put_method, send_list + [self.ItemClass('end')])
        await cocotb.triggers.Timer(1)
        self.assertEqual(send_list, self.result_list)

    async def run_get_response(self, put_method, get_response_method):
        send_list = []
        for ii in range(5):
            send_list.append(self.ItemClass(txn_id=ii))
        cocotb.start_soon(self.response_getter(get_response_method, [4, 2]))
        await self.putter(put_method, send_list)
        await cocotb.triggers.Timer(1)
        result = [xx.transaction_id for xx in self.result_list]
        self.assertEqual([4, 2], result)
        self.result_list = []
        cocotb.start_soon(self.response_getter(get_response_method, [5]))
        await self.putter(put_method,
                          [self.ItemClass(txn_id=10),
                           self.ItemClass(txn_id=11)])
        await cocotb.triggers.Timer(1)
        await self.putter(put_method, [self.ItemClass(txn_id=5)])
        await cocotb.triggers.Timer(1)
        self.assertTrue(5, self.result_list[0].transaction_id)

    async def test_ResponseQueue_put_get(self):
        rq = ResponseQueue()
        try:
            await self.run_put_get(rq.put, rq.get)
        except AssertionError as ae:
            print("ERROR: ", ae)
            raise

    async def test_ResponseQueue_get_response(self):
        rq = ResponseQueue()
        try:
            await self.run_get_response(rq.put, rq.get_response)
        except AssertionError as ae:
            print("ERROR: ", ae)
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

    async def test_premature_item_done(self):
        sip = uvm_seq_item_port("sip", self.my_root)
        sie = uvm_seq_item_export("sie", self.my_root)
        sip.connect(sie)
        with self.assertRaises(error_classes.UVMSequenceError):
            sip.item_done()

    async def test_base_virtual_sequence(self):
        class basic_seq(uvm_sequence):
            def __init__(self, name, result_list):
                super().__init__(name)
                self.rl = result_list

            async def body(self):
                self.rl.append('body')

        seq = basic_seq("basic_seq", self.result_list)
        await seq.start()
        self.assertEqual('body', self.result_list[0])

    class timeout_sequencer(uvm_sequencer):
        def __init__(self, name, parent):
            super().__init__(name, parent)

        async def run_phase(self):
            while True:
                next_item = await self.seq_q.get()
                next_item.start_condition.set()
                next_item.start_condition.clear()

    async def seq_item_port_getter(self, sip=None):
        datum = await sip.get_next_item()
        self.result_list.append(datum)

    async def test_run_sequence(self):
        ObjectionHandler().run_phase_done_flag = None

        class Seq(uvm_sequence):
            async def body(self):
                op = SeqItem("op")
                await self.start_item(op)
                op.data = 0
                await self.finish_item(op)
                DataHolder().datum = (op.result == (op.data + 1))

        class SeqTest(uvm_test):
            def build_phase(self):
                self.seqr = uvm_sequencer("seqr", self)
                self.driver = HandleRespSeqDriver("driver", self)

            def connect_phase(self):
                self.driver.seq_item_port.connect(self.seqr.seq_item_export)

            def end_of_elaboration_phase(self):
                self.set_logging_level_hier(PYUVM_DEBUG)

            async def run_phase(self):
                self.raise_objection()
                seq = Seq("seq")
                await seq.start(self.seqr)
                self.drop_objection()

        await uvm_root().run_test("SeqTest")
        self.assertTrue(DataHolder().datum)

    async def test_put_response(self):
        ObjectionHandler().run_phase_done_flag = None

        class PutRespSeqDriver(uvm_driver):
            async def run_phase(self):
                while True:
                    op_item = await self.seq_item_port.get_next_item()
                    op_item.data += 1
                    self.seq_item_port.put_response(op_item)
                    self.seq_item_port.item_done()

        class Seq(uvm_sequence):
            async def body(self):
                op = SeqItem("op")
                await self.start_item(op)
                op.data = 0
                await self.finish_item(op)
                result = await self.get_response()
                DataHolder().datum = (result.data == 1)

        class SeqTest(uvm_test):
            def build_phase(self):
                self.seqr = uvm_sequencer("seqr", self)
                self.driver = PutRespSeqDriver("driver", self)

            def connect_phase(self):
                self.driver.seq_item_port.connect(self.seqr.seq_item_export)

            async def run_phase(self):
                self.raise_objection()
                seq = Seq("seq")
                await seq.start(self.seqr)
                self.drop_objection()

        await uvm_root().run_test("SeqTest")
        self.assertTrue(DataHolder().datum)

    async def test_item_done_response(self):
        ObjectionHandler().run_phase_done_flag = None

        class Seq(uvm_sequence):
            async def body(self):
                op = SeqItem("op")
                await self.start_item(op)
                op.data = 0
                await self.finish_item(op)
                result = await self.get_response()
                DataHolder().datum = (op.data == 1)

        class SeqTest(uvm_test):
            def build_phase(self):
                self.seqr = uvm_sequencer("seqr", self)
                self.driver = ItemDoneRespSeqDriver("driver", self)

            def connect_phase(self):
                self.driver.seq_item_port.connect(self.seqr.seq_item_export)

            async def run_phase(self):
                self.raise_objection()
                seq = Seq("seq")
                await seq.start(self.seqr)
                self.drop_objection()

        await uvm_root().run_test("SeqTest")
        self.assertTrue(DataHolder().datum)

    async def test_multiple_seq_runs(self):
        ObjectionHandler().run_phase_done_flag = None

        class Seq(uvm_sequence):
            def __init__(self, name):
                super().__init__(name)
                self.runner_name = None  # pleasing the linter

            async def body(self):
                op = SeqItem("op")
                await self.start_item(op)
                op.data = DataHolder().dict_[self.runner_name]
                await self.finish_item(op)
                self.result = await self.get_response()

        class SeqAgent(uvm_agent):
            def build_phase(self):
                self.seqr = uvm_sequencer("seqr", self)
                self.driver = ItemDoneRespSeqDriver("driver", self)
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
                await seq.start(self.seqr)
                DataHolder().dict_[self.get_name()] = seq.result.data
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

    async def test_virtual_sequence(self):
        DataHolder().virtual_seq_error = False

        class IncSeq(uvm_sequence):
            async def body(self):
                for nn in range(5):
                    op = SeqItem("op")
                    await self.start_item(op)
                    op.data = nn
                    await self.finish_item(op)
                    error = op.data + 1 != op.result
                    if error:
                        print("!!!!!!INC ERROR!!!!")
                        DataHolder().virtual_seq_error = error
                        break

        class DecSeq(uvm_sequence):
            async def body(self):
                for nn in range(5):
                    op = SeqItem("op")
                    await self.start_item(op)
                    op.data = nn
                    await self.finish_item(op)
                    error = op.data + 1 != op.result
                    if error:
                        print("!!!!!!DEC ERROR!!!!")
                        DataHolder().virtual_seq_error = error
                        break

        class TopSeq(uvm_sequence):
            async def body(self):
                seqr = ConfigDB().get(None, "", "SEQR")
                inc = IncSeq("inc")
                await inc.start(seqr)
                if DataHolder().virtual_seq_error:
                    return
                dec = DecSeq("dec")
                await dec.start(seqr)

        class SeqTest(uvm_test):
            def build_phase(self):
                self.seqr = uvm_sequencer("seqr", self)
                self.driver = HandleRespSeqDriver("driver", self)
                ConfigDB().set(None, "*", "SEQR", self.seqr)

            def connect_phase(self):
                self.driver.seq_item_port.connect(self.seqr.seq_item_export)

            async def run_phase(self):
                self.raise_objection()
                self.top = TopSeq("top")
                await self.top.start()
                self.drop_objection()

        await uvm_root().run_test("SeqTest")
        self.assertFalse(DataHolder().virtual_seq_error)

    async def test_start_soon_sequence(self):
        DataHolder().virtual_seq_error = False

        class IncSeq(uvm_sequence):
            async def body(self):
                for nn in range(5):
                    op = SeqItem("op")
                    await self.start_item(op)
                    op.data = nn
                    await self.finish_item(op)
                    error = op.data + 1 != op.result
                    if error:
                        DataHolder().virtual_seq_error = error
                        break

        class DecSeq(uvm_sequence):
            async def body(self):
                for nn in range(5):
                    op = SeqItem("op")
                    await self.start_item(op)
                    op.data = nn
                    await self.finish_item(op)
                    error = op.data + 1 != op.result
                    if error:
                        DataHolder().virtual_seq_error = error
                        break

        class TopSeq(uvm_sequence):
            async def body(self):
                seqr = ConfigDB().get(None, "", "SEQR")
                inc = IncSeq("inc")
                dec = DecSeq("dec")
                cocotb.start_soon(inc.start(seqr))
                cocotb.start_soon(dec.start(seqr))

        class SeqTest(uvm_test):
            def build_phase(self):
                self.seqr = uvm_sequencer("seqr", self)
                self.driver = HandleRespSeqDriver("driver", self)
                ConfigDB().set(None, "*", "SEQR", self.seqr)

            def connect_phase(self):
                self.driver.seq_item_port.connect(self.seqr.seq_item_export)

            async def run_phase(self):
                self.raise_objection()
                self.top = TopSeq("top")
                await self.top.start()
                self.drop_objection()

        await uvm_root().run_test("SeqTest")
        self.assertFalse(DataHolder().virtual_seq_error)

    async def test_start_item_timing(self):
        ObjectionHandler().run_phase_done_flag = None

        class DelaySeqDriver(uvm_driver):

            def __init__(self, name, parent, start_delay_ns, finish_delay_ns):
                super().__init__(name, parent)
                self.start_delay_ns = start_delay_ns
                self.finish_delay_ns = finish_delay_ns

            async def run_phase(self):
                while True:
                    await Timer(self.start_delay_ns, units="ns")
                    op_item = await self.seq_item_port.get_next_item()
                    op_item.result = op_item.data + 1
                    await Timer(self.finish_delay_ns, units="ns")
                    self.seq_item_port.item_done()

        class Seq(uvm_sequence):
            async def body(self):
                op = SeqItem("op")
                DataHolder().start_item_call_time = get_sim_time(units="ns")
                uvm_root().logger.info("CALLING START_ITEM")
                await self.start_item(op)
                uvm_root().logger.info("BACK FROM START_ITEM")
                DataHolder().start_item_return_time = get_sim_time(units="ns")
                op.data = 0
                DataHolder().finish_item_call_time = get_sim_time(units="ns")
                await self.finish_item(op)
                DataHolder().finish_item_return_time = get_sim_time(units="ns")
                DataHolder().datum = (op.result == (op.data + 1))

        class SeqTest(uvm_test):
            def build_phase(self):
                self.seqr = uvm_sequencer("seqr", self)
                self.driver = DelaySeqDriver("driver", self, 5, 7)

            def connect_phase(self):
                self.driver.seq_item_port.connect(self.seqr.seq_item_export)

            def end_of_elaboration_phase(self):
                self.set_logging_level_hier(PYUVM_DEBUG)

            async def run_phase(self):
                self.raise_objection()
                seq = Seq("seq")
                await seq.start(self.seqr)
                self.drop_objection()

        await uvm_root().run_test("SeqTest")
        start_item_time = DataHolder().start_item_call_time
        start_return_time = DataHolder().start_item_return_time
        finish_item_call_time = DataHolder().finish_item_call_time
        finish_item_return_time = DataHolder().finish_item_return_time

        self.assertFalse(start_item_time == start_return_time)
        self.assertFalse(start_return_time == finish_item_return_time)
        self.assertTrue(start_return_time == finish_item_call_time)
        self.assertTrue(start_item_time + 5 == start_return_time)
        self.assertTrue(finish_item_call_time + 7 == finish_item_return_time)
