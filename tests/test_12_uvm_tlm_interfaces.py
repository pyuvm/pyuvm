import pyuvm_unittest
from pyuvm import *


class s12_uvm_tlm_interfaces_TestCase (pyuvm_unittest.pyuvm_TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mc = self.my_comp("mc")
        self.blocking_pute = self.TestBlockingPutExport("blocking_pute", self.mc)
        self.nonblocking_pute = self.TestBlockingPutExport("nonblocking_pute", self.mc)
        self.pute = self.TestPutExport("pute", self.mc)
        self.blocking_gete = self.TestBlockingGetExport("blocking_gete", self.mc)
        self.non_blocking_gete = self.TestNonBlockingGetExport("nonblocking_gete", self.mc)
        self.gete = self.TestGetExport("gete", self.mc)
        self.blocking_peeke = self.TestBlockingPeekExport("blocking_peeke", self.mc)
        self.non_blocking_peeke = self.TestNonBlockingPeekExport("non_blocking_peeke", self.mc)
        self.peeke = self.TestPeekExport("peeke", self.mc)
        self.blocking_transporte = self.TestBlockingTransportExport("blocking_transporte", self.mc)
        self.transporte = self.TestTransportExport("trane", self.mc)

    class my_comp(uvm_component):...
    class TestPutExportBase(uvm_export_base):
        def __init__(self, name, parent=None):
            super().__init__(name, parent)
            self.data = None

    class TestBlockingPutExport(TestPutExportBase, uvm_blocking_put_export):
        def put(self, data):
            self.data = data

    class TestNonBlockingPutExport(TestPutExportBase, uvm_nonblocking_put_export):
        def __init__(self, name=None, parent = None):
            super().__init__(name, parent)
            self.blocked = None

        def try_put(self, data):
            if not self.blocked:
                self.data = data
            return not self.blocked

        def can_put(self):
            return not self.blocked

    class TestPutExport(TestBlockingPutExport, TestNonBlockingPutExport):...

    class TestGetExportBase():
        def __init__(self, name="", parent = None):
            super().__init__(name, parent)
            self.data = None
            self.empty = None

    class TestBlockingGetExport(TestGetExportBase, uvm_blocking_get_export):
        def get(self):
            return self.data

    class TestNonBlockingGetExport(TestGetExportBase, uvm_nonblocking_get_export):

        def try_get(self):
            if not self.empty:
                return True, self.data
            return False, None

        def can_get(self):
            return not self.empty

    class TestGetExport(TestBlockingGetExport, TestNonBlockingGetExport):...

    class TestBlockingPeekExport(TestGetExportBase, uvm_blocking_peek_export):
        def peek(self):
            return self.data

    class TestNonBlockingPeekExport(TestGetExportBase, uvm_nonblocking_peek_export):

        def try_peek(self):
            if not self.empty:
                return True, self.data
            else:
                return False, None



        def can_peek(self):
            return self.can_peek()

    class TestPeekExport(TestBlockingPeekExport, TestNonBlockingPeekExport):...

    class TestNonBlockingPeekExport(TestGetExportBase, uvm_nonblocking_peek_export):

        def try_peek(self):
            return self.try_get()

        def can_peek(self):
            return self.can_get()

    class TestBlockingGetPeekExport(TestBlockingGetExport, TestBlockingPeekExport):...

    class TestNonBlockingGetPeekExport(TestNonBlockingGetExport, TestNonBlockingPeekExport):...

    class TestGetPeekExport(TestBlockingGetPeekExport, TestNonBlockingGetPeekExport):...

    class TestTransportExportBase(uvm_export_base):
        def __init__(self, name, parent):
            super().__init__(name, parent)
            self.put_data = None
            self.get_data = None
            self.blocked = True

    class TestBlockingTransportExport(TestTransportExportBase):
        def transport(self, put_data):
            self.put_data = put_data
            return self.get_data

    class TestNonBlockingTransportExport(TestTransportExportBase):
        def nb_transport(self,put_data):
            if self.blocked:
                return False, None
            else:
                return True, self.transport(put_data)

    class TestTransportExport(TestBlockingTransportExport, TestNonBlockingTransportExport):...

    class TestBlockingMasterExport(TestBlockingPutExport, TestNonBlockingGetPeekExport):
        ...

    class TestNonBlockingMasterExport(TestNonBlockingPutExport, TestNonBlockingGetPeekExport):
        ...

    class TestMasterExport(TestBlockingMasterExport, TestNonBlockingMasterExport):
        ...

    class TestBlockingSlaveExport(TestBlockingPutExport, TestNonBlockingGetPeekExport):
        ...

    class TestNonBlockingSlaveExport(TestNonBlockingPutExport, TestNonBlockingGetPeekExport):
        ...

    class TestSlaveExport(TestBlockingSlaveExport, TestNonBlockingSlaveExport):
        ...

    def test_uvm_blocking_put_port(self):
        bpp = uvm_blocking_put_port("bpp", self.mc)
        with self.assertRaises(UVMTLMConnectionError):
            bpp.put(0)
        with self.assertRaises(UVMTLMConnectionError):
            bpp.connect(self.gete)
        bpp.connect(self.pute)
        bpp.put(5)

    def test_uvm_non_blocking_put_port(self):
        pp = uvm_nonblocking_put_port("pp", self.mc)
        self.pute.data = 0
        with self.assertRaises(UVMTLMConnectionError):
            __ = pp.try_put("data")
        pp.connect(self.pute)
        self.pute.blocked = True
        self.assertFalse(pp.try_put(55))
        self.assertNotEqual(55, self.pute.data)
        self.pute.blocked = False
        self.assertTrue(pp.try_put(55))
        self.assertEqual(55, self.pute.data)

    def test_uvm_put_port(self):
        pp = uvm_put_port("pp", self.mc)
        with self.assertRaises(UVMTLMConnectionError):
            pp.put(5)
        pp.connect(self.pute)
        pp.put(5)
        self.assertEqual(5, self.pute.data)
        self.pute.blocked = True
        self.assertFalse(pp.try_put(0xdeadbee))
        self.assertNotEqual(0xdeadbee, self.pute.data)
        self.pute.blocked = False
        self.assertTrue(pp.try_put(0xdeadbee))
        self.assertEqual(0xdeadbee, self.pute.data)

    def test_uvm_blocking_get_port(self):
        gp = uvm_blocking_get_port("gp", self.mc)
        with self.assertRaises(UVMTLMConnectionError):
            __ = gp.get()
        gp.connect(self.gete)
        self.gete.data = 0xdeadbeef
        self.assertEqual(0xdeadbeef, gp.get())

    def test_uvm_non_blocking_get_port(self):
        gp = uvm_nonblocking_get_port("gp", self.mc)
        with self.assertRaises(UVMTLMConnectionError):
            __, __ = gp.try_get()
        gp.connect(self.gete)
        self.gete.empty = True
        self.gete.data = "Data"
        success, data = gp.try_get()
        self.assertFalse(success)
        self.assertIsNone(data)
        self.gete.empty = False
        success, data = gp.try_get()
        self.assertEqual("Data", data)
        self.assertTrue(success)

    def test_uvm_get_port(self):
        gp = uvm_get_port("gp", self.mc)
        with self.assertRaises(UVMTLMConnectionError):
            __, __ = gp.try_get()
        with self.assertRaises(UVMTLMConnectionError):
            __ = gp.get()
        gp.connect(self.gete)
        self.gete.data = 0xdeadbeef
        self.assertEqual(0xdeadbeef, gp.get())
        self.gete.empty = True
        self.gete.data = "Data"
        success, data = gp.try_get()
        self.assertFalse(success)
        self.assertIsNone(data)
        self.gete.empty = False
        success, data = gp.try_get()
        self.assertEqual("Data", data)
        self.assertTrue(success)

    def test_uvm_blocking_peek_port(self):
        gp = uvm_blocking_peek_port("gp", self.mc)
        with self.assertRaises(UVMTLMConnectionError):
            __ = gp.peek()
        gp.connect(self.peeke)
        self.peeke.data = 0xdeadbeef
        self.assertEqual(0xdeadbeef, gp.peek())

    def test_uvm_non_blocking_peek_port(self):
        gp = uvm_nonblocking_peek_port("gp", self.mc)
        with self.assertRaises(UVMTLMConnectionError):
            __, __ = gp.try_peek()
        gp.connect(self.peeke)
        self.peeke.empty = True
        self.peeke.data = "Data"
        success, data = gp.try_peek()
        self.assertFalse(success)
        self.assertIsNone(data)
        self.peeke.empty = False
        success, data = gp.try_peek()
        self.assertEqual("Data", data)
        self.assertTrue(success)

    def test_peek_port(self):
        gp = uvm_peek_port("gp", self.mc)
        with self.assertRaises(UVMTLMConnectionError):
            __, __ = gp.try_peek()
        with self.assertRaises(UVMTLMConnectionError):
            __ = gp.peek()
        gp.connect(self.peeke)
        self.peeke.data = 0xdeadbeef
        self.assertEqual(0xdeadbeef, gp.peek())
        self.peeke.empty = True
        self.peeke.data = "Data"
        success, data = gp.try_peek()
        self.assertFalse(success)
        self.assertIsNone(data)
        self.peeke.empty = False
        success, data = gp.try_peek()
        self.assertEqual("Data", data)
        self.assertTrue(success)

    def test_uvm_blocking_transport_port(self):
        gp = uvm_blocking_transport_port("gp", self.mc)
        with self.assertRaises(UVMTLMConnectionError):
            __ = gp.transport("sent")
        gp.connect(self.transporte)
        self.transporte.get_data = "returned"
        self.assertEqual("returned", gp.transport("sent"))

    def test_uvm_non_blocking_transport_port(self):
        gp = uvm_nonblocking_transport_port("gp", self.mc)
        with self.assertRaises(UVMTLMConnectionError):
            __, __ = gp.nb_transport("sent")
        gp.connect(self.transporte)
        self.transporte.blocked = True
        self.transporte.get_data = "returned"
        success, data = gp.nb_transport("sent")
        self.assertFalse(success)
        self.assertIsNone(data)
        self.transporte.blocked = False
        success, data = gp.nb_transport("sent")
        self.assertEqual("returned", data)
        self.assertTrue(success)

    def test_transport_port(self):
        gp = uvm_transport_port("gp", self.mc)
        with self.assertRaises(UVMTLMConnectionError):
            __, __ = gp.nb_transport("sent")
        with self.assertRaises(UVMTLMConnectionError):
            __ = gp.transport("sent")
        gp.connect(self.transporte)
        self.transporte.get_data = 0xdeadbeef
        self.assertEqual(0xdeadbeef, gp.transport("sent"))
        self.transporte.blocked = True
        self.transporte.get_data = "Data"
        success, data = gp.nb_transport("sent")
        self.assertFalse(success)
        self.assertIsNone(data)
        self.transporte.blocked = False
        success, data = gp.nb_transport("sent")
        self.assertEqual("Data", data)
        self.assertTrue(success)


    def test_tlm_fifo_size(self):
        """
        12.2.8.2.2
        :return:
        """
        ff = uvm_tlm_fifo("ff", None)
        size = ff.size()
        self.assertEqual(1,size)
        ff0 = uvm_tlm_fifo("ff0", None, 0)
        size = ff0.size()
        self.assertEqual(0, size)
        ff2 = uvm_tlm_fifo("ff2", None, 2)
        size = ff2.size()
        self.assertEqual(2, size)

    def test_tlm_fifo_used(self):
        """
        12.2.8.2.3
        :return:
        """
        ff = uvm_tlm_fifo("ff", None, 3)
        pp = uvm_put_port("pp", None)
        pp.connect(ff.put_export)
        pp.put(1)
        pp.put(2)
        pp.put(3)
        self.assertEqual(3, ff.used())

    def test_tlm_fifo_is_empty(self):
        ff = uvm_tlm_fifo("ff",None)
        self.assertTrue(ff.is_empty())
        pp = uvm_put_port("pp", None)
        pp.connect(ff.put_export)
        gp = uvm_get_port("gp", None)
        gp.connect(ff.get_export)
        pp.put(1)
        self.assertFalse(ff.is_empty())
        __ = gp.get()
        self.assertTrue(ff.is_empty())





    
