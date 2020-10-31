import pyuvm_unittest
from pyuvm import *


class s12_uvm_tlm_interfaces_TestCase (pyuvm_unittest.pyuvm_TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.my_root = uvm_component("my_root")



    class my_comp(uvm_component):...

    # Put
    class TestPutExportBase(uvm_export_base):
        def __init__(self, name, parent=None):
            super().__init__(name, parent)
            self.data = None

    class TestBlockingPutExport(TestPutExportBase, uvm_blocking_put_export):
        def put(self, data):
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

    class TestPutExport(TestBlockingPutExport, TestNonBlockingPutExport):...

    # Get
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

    # Peek
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

    # GetPeek
    class TestBlockingGetPeekExport(TestBlockingGetExport, TestBlockingPeekExport):...

    class TestNonBlockingGetPeekExport(TestNonBlockingGetExport, TestNonBlockingPeekExport):...

    class TestGetPeekExport(TestBlockingGetPeekExport, TestNonBlockingGetPeekExport):...

    # Transport
    class TestTransportExportBase(uvm_export_base):
        def __init__(self, name, parent):
            super().__init__(name, parent)
            self.put_data = None
            self.get_data = None
            self.blocked = True

    class TestBlockingTransportExport(TestTransportExportBase, uvm_blocking_transport_export):
        def transport(self, put_data):
            self.put_data = put_data
            return self.get_data

    class TestNonBlockingTransportExport(TestTransportExportBase, uvm_nonblocking_transport_export):
        def nb_transport(self,put_data):
            if self.blocked:
                return False, None
            else:
                self.put_data = put_data
                return True, self.get_data

    class TestTransportExport(TestBlockingTransportExport, TestNonBlockingTransportExport):...

    # Master
    class TestBlockingMasterExport(TestBlockingPutExport, TestNonBlockingGetPeekExport):
        ...

    class TestNonBlockingMasterExport(TestNonBlockingPutExport, TestNonBlockingGetPeekExport):
        ...

    class TestMasterExport(TestBlockingMasterExport, TestNonBlockingMasterExport):
        ...

    # Slave
    class TestBlockingSlaveExport(TestBlockingPutExport, TestNonBlockingGetPeekExport):
        ...

    class TestNonBlockingSlaveExport(TestNonBlockingPutExport, TestNonBlockingGetPeekExport):
        ...

    class TestSlaveExport(TestBlockingSlaveExport, TestNonBlockingSlaveExport):
        ...

    class TestInvalidExport(uvm_export_base):
        """
        Used to guarantee a port type error
        """
        ...

    # Put

    # Common predefined port tests: put, get, peek, get_peek, transport, master, slave

    def make_test_components(self, port_cls, export_cls):
        """
        Make the components for a port test in a child-free component
        :param port_cls:
        :param export_cls:
        :return: port, export, invalid
        """
        self.my_root.clear_children()
        port = port_cls("port", self.my_root)
        export = export_cls("export", self.my_root)
        invalid = self.TestInvalidExport("invalid", self.my_root)
        return port, export, invalid

    def blocking_put_test(self, port_cls, export_cls):
        (bpp, export, invalid) = self.make_test_components(port_cls, export_cls)
        with self.assertRaises(UVMTLMConnectionError):
            bpp.put(0)
        with self.assertRaises(UVMTLMConnectionError):
            bpp.connect(invalid)
        bpp.connect(export)
        bpp.put(5)
        self.assertEqual(export.data, 5)

    def nonblocking_put_test(self, port_cls, export_cls):
        (port, export, invalid) = self.make_test_components(port_cls,export_cls)
        export.data = 0
        with self.assertRaises(UVMTLMConnectionError):
            __ = port.try_put("data")
        with self.assertRaises(UVMTLMConnectionError):
            __ = port.connect(invalid)
        port.connect(export)
        export.blocked = True
        self.assertFalse(port.try_put(55))
        self.assertNotEqual(55, export.data)
        export.blocked = False
        self.assertTrue(port.try_put(55))
        self.assertEqual(55, export.data)

    def blocking_get_test(self, port_cls, export_cls):
        (port, export, invalid) = self.make_test_components(port_cls,export_cls)
        with self.assertRaises(UVMTLMConnectionError):
            __ = port.get()
        with self.assertRaises(UVMTLMConnectionError):
            __ = port.connect(invalid)
        port.connect(export)
        export.data = 0xdeadbeef
        self.assertEqual(0xdeadbeef, port.get())

    def nonblocking_get_test(self, port_cls, export_cls):
        (port, export, invalid) = self.make_test_components(port_cls,export_cls)
        with self.assertRaises(UVMTLMConnectionError):
            __, __ = port.try_get()
        with self.assertRaises(UVMTLMConnectionError):
            __ = port.connect(invalid)
        port.connect(export)
        export.empty = True
        export.data = "Data"
        success, data = port.try_get()
        self.assertFalse(success)
        self.assertIsNone(data)
        export.empty = False
        success, data = port.try_get()
        self.assertEqual("Data", data)
        self.assertTrue(success)

    def blocking_peek_test(self, port_cls, export_cls):
        (port, export, invalid) = self.make_test_components(port_cls,export_cls)
        with self.assertRaises(UVMTLMConnectionError):
            __ = port.peek()
        with self.assertRaises(UVMTLMConnectionError):
            port.connect(invalid)
        port.connect(export)
        export.data = 0xdeadbeef
        self.assertEqual(0xdeadbeef, port.peek())


    def nonblocking_peek_test(self, port_cls, export_cls):
        (port, export, invalid) = self.make_test_components(port_cls,export_cls)
        with self.assertRaises(UVMTLMConnectionError):
            __, __ = port.try_peek()
        with self.assertRaises(UVMTLMConnectionError):
            port.connect(invalid)
        port.connect(export)
        export.empty = True
        export.data = "Data"
        success, data = port.try_peek()
        self.assertFalse(success)
        self.assertIsNone(data)
        export.empty = False
        success, data = port.try_peek()
        self.assertEqual("Data", data)
        self.assertTrue(success)


    def blocking_get_peek_test(self,port_cls, export_cls):
        pass

    def nonblocking_get_peek_test(self, port_cls, export_cls):
        pass

    def blocking_transport_test(self, port_cls, export_cls):
        (port, export, invalid) = self.make_test_components(port_cls,export_cls)
        with self.assertRaises(UVMTLMConnectionError):
            __ = port.transport("sent")
        with self.assertRaises(UVMTLMConnectionError):
            port.connect(invalid)
        port.connect(export)
        export.get_data = "returned"
        returned_data = port.transport("sent")
        self.assertEqual("returned", returned_data)

    def nonblocking_transport_test(self,  port_cls, export_cls):
        (port, export, invalid) = self.make_test_components(port_cls,export_cls)
        with self.assertRaises(UVMTLMConnectionError):
            __, __ = port.nb_transport("sent")
        with self.assertRaises(UVMTLMConnectionError):
            port.connect(invalid)
        port.connect(export)
        export.blocked = True
        export.get_data = "returned"
        success, data = port.nb_transport("sent")
        self.assertFalse(success)
        self.assertIsNone(data)
        export.blocked = False
        success, data = port.nb_transport("sent")
        self.assertEqual("returned", data)
        self.assertTrue(success)


    def master_test(self, port_cls, export_cls):
        pass

    def slave_test(self, port_cls, export_cls):
        pass

    def test_uvm_blocking_put_port(self):
        self.blocking_put_test(uvm_blocking_put_port, self.TestBlockingPutExport)

    def test_uvm_non_blocking_put_port(self):
        self.nonblocking_put_test(uvm_nonblocking_put_port, self.TestNonBlockingPutExport)

    def test_uvm_put_port(self):
        self.blocking_put_test(uvm_put_port, self.TestPutExport)
        self.nonblocking_put_test(uvm_put_port, self.TestPutExport)

    def test_uvm_blocking_get_port(self):
        self.blocking_get_test(uvm_blocking_get_port, self.TestBlockingGetExport)

    def test_uvm_non_blocking_get_port(self):
        self.nonblocking_get_test(uvm_nonblocking_get_port, self.TestNonBlockingGetExport)

    def test_uvm_get_port(self):
        self.blocking_get_test(uvm_get_port, self.TestGetExport)
        self.nonblocking_get_test(uvm_get_port, self.TestGetExport)

    def test_uvm_blocking_peek_port(self):
        self.blocking_peek_test(uvm_blocking_peek_port, self.TestBlockingPeekExport)

    def test_uvm_non_blocking_peek_port(self):
        self.nonblocking_peek_test(uvm_nonblocking_peek_port, self.TestNonBlockingPeekExport)

    def test_peek_port(self):
        self.blocking_peek_test(uvm_peek_port, self.TestPeekExport)
        self.nonblocking_peek_test(uvm_peek_port, self.TestPeekExport)

    def test_uvm_blocking_transport_port(self):
        self.blocking_transport_test(uvm_blocking_transport_port, self.TestBlockingTransportExport)

    def test_uvm_non_blocking_transport_port(self):
        self.nonblocking_transport_test(uvm_nonblocking_transport_port, self.TestNonBlockingTransportExport)

    def test_transport_port(self):
        self.blocking_transport_test(uvm_transport_port, self.TestTransportExport)
        self.nonblocking_transport_test(uvm_transport_port, self.TestTransportExport)


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





    
