import uvm_unittest
from pyuvm import * # pylint: disable=unused-wildcard-import
import cocotb
from cocotb.triggers import Timer


async def waitabit(abit=5):
    await Timer(1, units="us")
class s12_uvm_tlm_interfaces_TestCase(uvm_unittest.uvm_TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if uvm_root().has_child("my_root"):
            self.my_root = uvm_root().get_child("my_root")
        else:
            self.my_root = uvm_component("my_root", None)


    def setUp(self):
        ObjectionHandler().run_phase_done_flag = False
        self.my_root.clear_children()


    def tearDown(self):
        ObjectionHandler().run_phase_done_flag = True
    class my_comp(uvm_component):
        ...

    # Put
    class TestPutExportBase(uvm_port_base):
        def __init__(self, name, parent=None):
            super().__init__(name, parent)
            self.data = None

    class TestBlockingPutExport(TestPutExportBase, uvm_blocking_put_export):
        async def put(self, data):
            self.data = data

    class TestNonBlockingPutExport(TestPutExportBase, uvm_nonblocking_put_export):
        def __init__(self, name=None, parent=None):
            super().__init__(name, parent)
            self.blocked = None

        def try_put(self, data):
            if not self.blocked:
                self.data = data
            return not self.blocked

        def can_put(self):
            return not self.blocked

    class TestPutExport(TestBlockingPutExport, TestNonBlockingPutExport):
        ...

    # Get
    class TestGetExportBase:
        def __init__(self, name="", parent=None):
            super().__init__(name, parent)
            self.data = None
            self.empty = None

    class TestBlockingGetExport(TestGetExportBase, uvm_blocking_get_export):
        async def get(self):
            return self.data

    class TestNonBlockingGetExport(TestGetExportBase, uvm_nonblocking_get_export):

        def try_get(self):
            if not self.empty:
                return True, self.data
            return False, None

        def can_get(self):
            return not self.empty

    class TestGetExport(TestBlockingGetExport, TestNonBlockingGetExport):
        ...

    # Peek
    class TestBlockingPeekExport(TestGetExportBase, uvm_blocking_peek_export):
        async def peek(self):
            return self.data

    class TestNonBlockingPeekExport(TestGetExportBase, uvm_nonblocking_peek_export):

        def try_peek(self):
            if not self.empty:
                return True, self.data
            else:
                return False, None

        def can_peek(self):
            return self.can_peek()

    class TestPeekExport(TestBlockingPeekExport, TestNonBlockingPeekExport):
        ...

    # GetPeek
    class TestBlockingGetPeekExport(TestBlockingGetExport, TestBlockingPeekExport):
        ...

    class TestNonBlockingGetPeekExport(TestNonBlockingGetExport, TestNonBlockingPeekExport):
        ...

    class TestGetPeekExport(TestBlockingGetPeekExport, TestNonBlockingGetPeekExport):
        ...

    # Transport
    class TestTransportExportBase(uvm_port_base):
        def __init__(self, name, parent):
            super().__init__(name, parent)
            self.put_data = None
            self.get_data = None
            self.blocked = True

    class TestBlockingTransportExport(TestTransportExportBase, uvm_blocking_transport_export):
        async def transport(self, put_data):
            self.put_data = put_data
            return self.get_data

    class TestNonBlockingTransportExport(TestTransportExportBase, uvm_nonblocking_transport_export):
        def nb_transport(self, put_data):
            if self.blocked:
                return False, None
            else:
                self.put_data = put_data
                return True, self.get_data

    class TestTransportExport(TestBlockingTransportExport, TestNonBlockingTransportExport):
        ...

    # Master
    class TestBlockingMasterExport(TestBlockingPutExport, TestBlockingGetPeekExport):
        ...

    class TestNonBlockingMasterExport(TestNonBlockingPutExport, TestNonBlockingGetPeekExport):
        ...

    class TestMasterExport(TestBlockingMasterExport, TestNonBlockingMasterExport):
        ...

    # Slave
    class TestBlockingSlaveExport(TestBlockingPutExport, TestBlockingGetPeekExport):
        ...

    class TestNonBlockingSlaveExport(TestNonBlockingPutExport, TestNonBlockingGetPeekExport):
        ...

    class TestSlaveExport(TestBlockingSlaveExport, TestNonBlockingSlaveExport):
        ...

    class TestInvalidExport(uvm_port_base):
        """
        Used to guarantee a port type error
        """
        ...

    # Put

    # Common predefined port tests: put, get, peek, get_peek, transport, master, slave

    def make_components(self, port_cls, export_cls):
        """
        Make the components for a port test in a child-free component
        :param port_cls:
        :param export_cls:
        :return: port, export, invalid
        """
        self.my_root.clear_children()
        port = port_cls("port", self.my_root)
        port2 = port_cls("port2", self.my_root)
        export = export_cls("export", self.my_root)
        invalid = self.TestInvalidExport("invalid", self.my_root)
        return port, port2, export, invalid

    async def exercise_blocking_put(self, port_cls, export_cls):
        (bpp, bpp2, export, invalid) = self.make_components(port_cls, export_cls)
        with self.assertRaises(UVMTLMConnectionError):
            await bpp.put(0)
        with self.assertRaises(UVMTLMConnectionError):
            bpp.connect(invalid)
        bpp.connect(export)
        bpp2.connect(bpp)
        # test first port
        await bpp.put(5)
        self.assertEqual(export.data, 5)
        # test port connected to port
        await bpp2.put(15)
        self.assertEqual(export.data, 15)

    def exercise_nonblocking_put(self, port_cls, export_cls):
        (port, port2, export, invalid) = self.make_components(port_cls, export_cls)
        export.data = 0
        with self.assertRaises(UVMTLMConnectionError):
            __ = port.try_put("data")
        with self.assertRaises(UVMTLMConnectionError):
            __ = port.connect(invalid)
        port.connect(export)
        port2.connect(port)
        export.blocked = True
        # test first port
        self.assertFalse(port.try_put(55))
        self.assertNotEqual(55, export.data)
        export.blocked = False
        self.assertTrue(port.try_put(55))
        self.assertEqual(55, export.data)
        # test port connected to port
        export.blocked = True
        self.assertFalse(port.try_put(10))
        self.assertNotEqual(10, export.data)
        export.blocked = False
        self.assertTrue(port.try_put(10))
        self.assertEqual(10, export.data)

    async def exercise_blocking_get(self, port_cls, export_cls):
        (port, port2, export, invalid) = self.make_components(port_cls, export_cls)
        with self.assertRaises(UVMTLMConnectionError):
            __ = await port.get()
        with self.assertRaises(UVMTLMConnectionError):
            __ = port.connect(invalid)
        port.connect(export)
        port2.connect(port)
        # test port
        export.data = 0xdeadbeef
        get_data = await port.get()
        self.assertEqual(0xdeadbeef, get_data)
        # test port connected to port
        export.data = 0xdeadbee2
        get_data = await port2.get()
        self.assertEqual(0xdeadbee2, get_data)

    def exercise_nonblocking_get(self, port_cls, export_cls):
        (port, port2, export, invalid) = self.make_components(port_cls, export_cls)
        with self.assertRaises(UVMTLMConnectionError):
            __, __ = port.try_get()
        with self.assertRaises(UVMTLMConnectionError):
            __ = port.connect(invalid)
        port.connect(export)
        port2.connect(port)
        # tests port
        export.empty = True
        export.data = "Data"
        success, data = port.try_get()
        self.assertFalse(success)
        self.assertIsNone(data)
        export.empty = False
        success, data = port.try_get()
        self.assertEqual("Data", data)
        self.assertTrue(success)
        # test port connected to port
        export.empty = True
        export.data = "Data2"
        success, data = port2.try_get()
        self.assertFalse(success)
        self.assertIsNone(data)
        export.empty = False
        success, data = port2.try_get()
        self.assertEqual("Data2", data)
        self.assertTrue(success)

    async def exercise_blocking_peek(self, port_cls, export_cls):
        (port, port2, export, invalid) = self.make_components(port_cls, export_cls)
        with self.assertRaises(UVMTLMConnectionError):
            __ = await port.peek()
        with self.assertRaises(UVMTLMConnectionError):
            port.connect(invalid)
        port.connect(export)
        port2.connect(port)
        # test port
        export.data = 0xdeadbeef
        peek_data = await port.peek()
        self.assertEqual(0xdeadbeef, peek_data)
        # test port connected to port
        export.data = 0xdeadbe2f
        peek_data = await port.peek()
        self.assertEqual(0xdeadbe2f, peek_data)

    def exercise_nonblocking_peek(self, port_cls, export_cls):
        (port, port2, export, invalid) = self.make_components(port_cls, export_cls)
        with self.assertRaises(UVMTLMConnectionError):
            __, __ = port.try_peek()
        with self.assertRaises(UVMTLMConnectionError):
            port.connect(invalid)
        port.connect(export)
        port2.connect(port)
        # test port
        export.empty = True
        export.data = "Data"
        success, data = port.try_peek()
        self.assertFalse(success)
        self.assertIsNone(data)
        export.empty = False
        success, data = port.try_peek()
        self.assertEqual("Data", data)
        self.assertTrue(success)
        # test port connected to port
        export.empty = True
        export.data = "Data2"
        success, data = port2.try_peek()
        self.assertFalse(success)
        self.assertIsNone(data)
        export.empty = False
        success, data = port2.try_peek()
        self.assertEqual("Data2", data)
        self.assertTrue(success)

    async def exercise_blocking_get_peek(self, port_cls, export_cls):
        await self.exercise_blocking_get(port_cls, export_cls)
        await self.exercise_blocking_peek(port_cls, export_cls)

    def exercise_nonblocking_get_peek(self, port_cls, export_cls):
        self.exercise_nonblocking_get(port_cls, export_cls)
        self.exercise_nonblocking_peek(port_cls, export_cls)

    async def exercise_get_peek(self, port_cls, export_cls):
        await self.exercise_blocking_get_peek(port_cls, export_cls)
        self.exercise_nonblocking_get_peek(port_cls, export_cls)

    async def exercise_blocking_transport(self, port_cls, export_cls):
        (port, port2, export, invalid) = self.make_components(port_cls, export_cls)
        with self.assertRaises(UVMTLMConnectionError):
            __ = await port.transport("sent")
        with self.assertRaises(UVMTLMConnectionError):
            port.connect(invalid)
        port.connect(export)
        port2.connect(port)
        # test port
        export.get_data = "returned"
        returned_data = await port.transport("sent")
        self.assertEqual("returned", returned_data)
        # test port connected to port
        export.get_data = "2returned"
        returned_data = await port2.transport("sent")
        self.assertEqual("2returned", returned_data)

    def exercise_nonblocking_transport(self, port_cls, export_cls):
        (port, port2, export, invalid) = self.make_components(port_cls, export_cls)
        with self.assertRaises(UVMTLMConnectionError):
            __, __ = port.nb_transport("sent")
        with self.assertRaises(UVMTLMConnectionError):
            port.connect(invalid)
        port.connect(export)
        port2.connect(port)
        # test port
        export.blocked = True
        export.get_data = "returned"
        success, data = port.nb_transport("sent")
        self.assertFalse(success)
        self.assertIsNone(data)
        export.blocked = False
        success, data = port.nb_transport("sent")
        self.assertEqual("returned", data)
        self.assertTrue(success)
        # test port connected to port
        export.blocked = True
        export.get_data = "returned"
        success, data = port2.nb_transport("sent")
        self.assertFalse(success)
        self.assertIsNone(data)
        export.blocked = False
        success, data = port2.nb_transport("sent")
        self.assertEqual("returned", data)
        self.assertTrue(success)

    def exercise_slave_do(self, port_cls, export_cls):
        pass

    async def test_uvm_blocking_put_port(self):
        await self.exercise_blocking_put(uvm_blocking_put_port, self.TestBlockingPutExport)

    def test_uvm_non_blocking_put_port(self):
        self.exercise_nonblocking_put(uvm_nonblocking_put_port, self.TestNonBlockingPutExport)

    async def test_uvm_put_port(self):
        await self.exercise_blocking_put(uvm_put_port, self.TestPutExport)
        self.exercise_nonblocking_put(uvm_put_port, self.TestPutExport)

    async def test_uvm_blocking_get_port(self):
        await self.exercise_blocking_get(uvm_blocking_get_port, self.TestBlockingGetExport)

    def test_uvm_non_blocking_get_port(self):
        self.exercise_nonblocking_get(uvm_nonblocking_get_port, self.TestNonBlockingGetExport)

    async def test_uvm_get_port(self):
        await self.exercise_blocking_get(uvm_get_port, self.TestGetExport)
        self.exercise_nonblocking_get(uvm_get_port, self.TestGetExport)

    async def test_uvm_blocking_peek_port(self):
        await self.exercise_blocking_peek(uvm_blocking_peek_port, self.TestBlockingPeekExport)

    def test_uvm_non_blocking_peek_port(self):
        self.exercise_nonblocking_peek(uvm_nonblocking_peek_port, self.TestNonBlockingPeekExport)

    async def test_uvm_peek_port(self):
        await self.exercise_blocking_peek(uvm_peek_port, self.TestPeekExport)
        self.exercise_nonblocking_peek(uvm_peek_port, self.TestPeekExport)

    async def test_uvm_blocking_get_peek_port(self):
        await self.exercise_blocking_get_peek(uvm_blocking_get_peek_port, self.TestBlockingGetPeekExport)

    def test_uvm_non_blocking_get_peek_port(self):
        self.exercise_nonblocking_get_peek(uvm_nonblocking_get_peek_port, self.TestNonBlockingGetPeekExport)

    async def test_uvm_get_peek_port(self):
        await self.exercise_get_peek(uvm_get_peek_port, self.TestGetPeekExport)

    async def test_uvm_blocking_transport_port(self):
        await self.exercise_blocking_transport(uvm_blocking_transport_port, self.TestBlockingTransportExport)

    def test_uvm_non_blocking_transport_port(self):
        self.exercise_nonblocking_transport(uvm_nonblocking_transport_port, self.TestNonBlockingTransportExport)

    async def test_uvm_transport_port(self):
        await self.exercise_blocking_transport(uvm_transport_port, self.TestTransportExport)
        self.exercise_nonblocking_transport(uvm_transport_port, self.TestTransportExport)

    async def test_uvm_blocking_master_port(self):
        await self.exercise_blocking_put(uvm_blocking_master_port, self.TestBlockingMasterExport)
        await self.exercise_blocking_get_peek(uvm_blocking_master_port, self.TestBlockingMasterExport)

    def test_uvm_nonblocking_master_port(self):
        self.exercise_nonblocking_put(uvm_nonblocking_master_port, self.TestNonBlockingMasterExport)
        self.exercise_nonblocking_get_peek(uvm_nonblocking_master_port, self.TestNonBlockingMasterExport)

    async def test_uvm_master_port(self):
        self.exercise_nonblocking_put(uvm_master_port, self.TestMasterExport)
        self.exercise_nonblocking_get_peek(uvm_master_port, self.TestMasterExport)
        await self.exercise_blocking_put(uvm_master_port, self.TestMasterExport)
        await self.exercise_blocking_get_peek(uvm_master_port, self.TestMasterExport)

    async def test_uvm_blocking_slave_port(self):
        await self.exercise_blocking_put(uvm_blocking_slave_port, self.TestBlockingSlaveExport)
        await self.exercise_blocking_get_peek(uvm_blocking_slave_port, self.TestBlockingSlaveExport)

    def test_uvm_nonblocking_slave_port(self):
        self.exercise_nonblocking_put(uvm_nonblocking_slave_port, self.TestNonBlockingSlaveExport)
        self.exercise_nonblocking_get_peek(uvm_nonblocking_slave_port, self.TestNonBlockingSlaveExport)

    async def test_uvm_slave_port(self):
        self.exercise_nonblocking_put(uvm_slave_port, self.TestSlaveExport)
        self.exercise_nonblocking_get_peek(uvm_slave_port, self.TestSlaveExport)
        await self.exercise_blocking_put(uvm_slave_port, self.TestSlaveExport)
        await self.exercise_blocking_get_peek(uvm_slave_port, self.TestSlaveExport)

    def test_uvm_tlm_fifo_size(self):
        """
        12.2.8.2.2
        :return:
        """

        ff = uvm_tlm_fifo("ff", self.my_root)
        size = ff.size()
        self.assertEqual(1, size)
        ff0 = uvm_tlm_fifo("ff0", self.my_root, 0)
        size = ff0.size()
        self.assertEqual(0, size)
        ff2 = uvm_tlm_fifo("ff2", self.my_root, 2)
        size = ff2.size()
        self.assertEqual(2, size)

    async def test_uvm_tlm_fifo_used(self):
        """
        12.2.8.2.3
        :return:
        """
        ff = uvm_tlm_fifo("ff", self.my_root, 3)
        pp = uvm_put_port("pp", self.my_root)
        pp.connect(ff.put_export)
        await pp.put(1)
        await pp.put(2)
        await pp.put(3)
        self.assertEqual(3, ff.used())

    async def test_uvm_tlm_fifo_is_empty(self):
        """
        12.2.8.2.4
        :return:
        """
        ff = uvm_tlm_fifo("ff", None)
        self.assertTrue(ff.is_empty())
        pp = uvm_put_port("pp", None)
        pp.connect(ff.put_export)
        gp = uvm_get_port("gp", None)
        gp.connect(ff.get_export)
        await pp.put(1)
        self.assertFalse(ff.is_empty())
        __ = await gp.get()
        self.assertTrue(ff.is_empty())

    def make_fifo(self, fifo_type) -> uvm_tlm_fifo_base:
        self.my_root.clear_children()
        fifo = fifo_type("fifo", self.my_root)
        return fifo

    @staticmethod
    async def do_blocking_put(put_port, data_list):
        for data in data_list:
            await put_port.put(data)

    @staticmethod
    async def do_blocking_get(get_port, data_list):
        while True:
            datum = await get_port.get()
            if datum is not None:
                data_list.append(datum)
            else:
                break

    @staticmethod
    async def do_blocking_peek(peek_port, data_list):
        datum = await peek_port.peek()
        data_list.append(datum)


    async def test_fifo_blocking(self):
        fifo = self.make_fifo(uvm_tlm_fifo)
        pp = uvm_blocking_put_port("pp", self.my_root)
        gp = uvm_blocking_get_port("gp", self.my_root)
        pk = uvm_blocking_peek_port("pk", self.my_root)
        gpp = uvm_blocking_get_peek_port("gpp", self.my_root)
        pp.connect(fifo.blocking_put_export)    
        gp.connect(fifo.blocking_get_export)
        pk.connect(fifo.blocking_peek_export)
        gpp.connect(fifo.blocking_get_peek_export)
        put_data = [1, 'f', 3, 'c', None]
        peek_data = []
        get_data = []
        cocotb.start_soon(self.do_blocking_put(pp, put_data))
        await self.do_blocking_peek(gpp, peek_data)
        await self.do_blocking_get(gpp, get_data)
        self.assertEqual(put_data[:-1], get_data)
        self.assertEqual(put_data[0], peek_data[0])
        peek_data = []
        get_data = []
        fifo.flush()
        cocotb.start_soon(self.do_blocking_put(pp,put_data))
        await self.do_blocking_peek(gpp, peek_data)
        await self.do_blocking_get(gpp, get_data)
        self.assertTrue(put_data[0], peek_data[0])
        self.assertEqual(put_data[:-1], get_data)
        pass

    @staticmethod
    async def do_nonblocking_put(put_port, data_list):
        for data in data_list:
            while not put_port.try_put(data):
                await waitabit()
                
    @staticmethod
    async def do_nonblocking_get(get_port, data_list):
        while True:
            success, datum = get_port.try_get()
            if success:
                if datum is not None:
                    data_list.append(datum)
                else:
                    break
            else:
                await waitabit()

    @staticmethod
    async def do_nonblocking_peek(peek_port, data_list):
        data_list.append(peek_port.try_peek())

    async def test_fifo_nonblocking(self):
        fifo = self.make_fifo(uvm_tlm_fifo)
        pp = uvm_nonblocking_put_port("pp", self.my_root)
        gp = uvm_nonblocking_get_port("gp", self.my_root)
        pk = uvm_nonblocking_peek_port("pk", self.my_root)
        pp.connect(fifo.nonblocking_put_export)
        gp.connect(fifo.nonblocking_get_export)
        pk.connect(fifo.nonblocking_peek_export)
        put_data = [10, 20, 30, 'c0', None]
        get_data = []
        peek_data = []
        self.assertFalse(pk.can_peek())
        await self.do_nonblocking_peek(pk, peek_data)
        success, data = peek_data.pop()
        self.assertFalse(success)
        self.assertIsNone(data)
        await waitabit()
        cocotb.start_soon(self.do_nonblocking_put(pp, put_data))
        self.assertTrue(pk.can_peek())
        await self.do_nonblocking_peek(pk, peek_data)
        success, data = peek_data.pop()
        self.assertTrue(success)
        self.assertEqual(data, put_data[0])
        await self.do_nonblocking_get(gp, get_data)
        self.assertEqual(put_data[:-1], get_data)
        # now with get_peek
        gpp = uvm_nonblocking_get_peek_port("gpp", self.my_root)
        gpp.connect(fifo.nonblocking_get_peek_export)
        get_data = []
        peek_data = []
        self.assertFalse(pk.can_peek())
        await self.do_nonblocking_peek(gpp, peek_data)
        success, data = peek_data.pop()
        self.assertFalse(success)
        self.assertIsNone(data)
        cocotb.start_soon(self.do_nonblocking_put(pp, put_data))
        await Timer(1, units="us")
        self.assertTrue(pk.can_peek())
        await self.do_nonblocking_peek(gpp, peek_data)
        success, data = peek_data.pop()
        self.assertTrue(success)
        self.assertEqual(data, put_data[0])
        await self.do_nonblocking_get(gpp, get_data)
        self.assertEqual(put_data[:-1], get_data)
