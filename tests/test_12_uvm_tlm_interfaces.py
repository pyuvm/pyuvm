import pyuvm_unittest
from pyuvm import *


class s12_uvm_tlm_interfaces_TestCase (pyuvm_unittest.pyuvm_TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mc = self.my_comp("mc")
        self.pte = self.TestPutExport("pte", self.mc)
        self.gte = self.TestGetExport("gte", None)

    class my_comp(uvm_component):...
    class TestPutExportBase(uvm_export_base):
        def __init__(self, name, parent=None):
            super().__init__(name, parent)
            self.data = None

    class TestBlockingPutExport(TestPutExportBase):
        def put(self, data):
            self.data = data

    class TestNonBlockingPutExport(TestPutExportBase):
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

    class TestGetExportBase(uvm_export_base):
        def __init__(self, name="", parent = None):
            super().__init__(name, parent)
            self.data = None

    class TestBlockingGetExport(TestGetExportBase):
        def get(self):
            return self.data

    class TestNonBlockingGetExport(TestGetExportBase):
        def  __int__(self, name, parent):
            super().__init__(name, parent)
            self.empty = None

        def try_get(self):
            if not self.empty:
                return True, self.data
            return False, None

        def can_get(self):
            return not self.empty

    class TestGetExport(TestBlockingGetExport, TestNonBlockingGetExport):...

    class TestBlockingPeekExport(TestBlockingGetExport):

        def peek(self):
            return self.get()

    class TestNonBlockingPeekExport(TestNonBlockingGetExport):

        def try_peek(self):
            return self.try_get()

        def can_peek(self):
            return self.can_peek()

    class TestPeekExport(TestBlockingPeekExport, TestNonBlockingPeekExport):...

    class TestNonBlockingPeekExport(TestNonBlockingGetExport):

        def try_peek(self):
            return self.try_get()

        def can_peek(self):
            return self.can_get()

    class TestGetPeekExport(TestGetExport, TestPeekExport):...

    def test_uvm_blocking_put_port(self):
        bpp = uvm_blocking_put_port("bpp", self.mc)
        with self.assertRaises(UVMTLMConnectionError):
            bpp.put(0)
        bpp.connect(self.pte)
        bpp.put(5)

    def test_uvm_non_blocking_put_port(self):
        pp = uvm_nonblocking_put_port("pp", self.mc)
        self.pte.data = 0
        with self.assertRaises(UVMTLMConnectionError):
            __ = pp.try_put("data")
        pp.connect(self.pte)
        self.pte.blocked = True
        self.assertFalse(pp.try_put(55))
        self.assertNotEqual(55, self.pte.data)
        self.pte.blocked = False
        self.assertTrue(pp.try_put(55))
        self.assertEqual(55, self.pte.data)

    def test_uvm_put_port(self):
        pp = uvm_put_port("pp", self.mc)
        with self.assertRaises(UVMTLMConnectionError):
            pp.put(5)
        pp.connect(self.pte)
        pp.put(5)
        self.assertEqual(5, self.pte.data)
        self.pte.blocked = True
        self.assertFalse(pp.try_put(0xdeadbee))
        self.assertNotEqual(0xdeadbee, self.pte.data)
        self.pte.blocked = False
        self.assertTrue(pp.try_put(0xdeadbee))
        self.assertEqual(0xdeadbee, self.pte.data)

    def test_uvm_blocking_get_port(self):
        gp = uvm_blocking_get_port("gp", self.mc)
        with self.assertRaises(UVMTLMConnectionError):
            __ = gp.get()
        gp.connect(self.gte)
        self.gte.data = 0xdeadbeef
        self.assertEqual(0xdeadbeef, gp.get())

    def test_uvm_non_blocking_get_port(self):
        gp = uvm_nonblocking_get_port("gp", self.mc)
        with self.assertRaises(UVMTLMConnectionError):
            __, __ = gp.try_get()
        gp.connect(self.gte)
        self.gte.empty = True
        self.gte.data = "Data"
        success, data = gp.try_get()
        self.assertFalse(success)
        self.assertIsNone(data)
        self.gte.empty = False
        success, data = gp.try_get()
        self.assertEqual("Data", data)
        self.assertTrue(success)

    def test_uvm_get_port(self):
        gp = uvm_get_port("gp", self.mc)
        with self.assertRaises(UVMTLMConnectionError):
            __, __ = gp.try_get()
        with self.assertRaises(UVMTLMConnectionError):
            __ = gp.get()
        gp.connect(self.gte)
        self.gte.data = 0xdeadbeef
        self.assertEqual(0xdeadbeef, gp.get())
        self.gte.empty = True
        self.gte.data = "Data"
        success, data = gp.try_get()
        self.assertFalse(success)
        self.assertIsNone(data)
        self.gte.empty = False
        success, data = gp.try_get()
        self.assertEqual("Data", data)
        self.assertTrue(success)





    
