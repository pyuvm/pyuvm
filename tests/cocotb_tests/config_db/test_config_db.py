import pyuvm_unittest
from pyuvm import *

class config_db_TestCase(pyuvm_unittest.pyuvm_TestCase):

    def __init__(self, clock, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clock = clock

    def tearDown(self) -> None:
        super().tearDown()
        ConfigDB().clear()

    def test_context_None(self):
        cdb = ConfigDB()
        # simple set/get
        cdb.set(None, "*", "LABEL", 5)
        with self.assertRaises(error_classes.UVMError):
            cdb.exists(None, "*", "LABEL")
        self.assertTrue(cdb.exists(None, "A", "LABEL"))
        datum = cdb.get(None, "A", "LABEL")
        self.assertEqual(5, datum)
        with self.assertRaises(error_classes.UVMConfigItemNotFound):
            cdb.get(None, "A", "NOT THERE")
        self.assertFalse(cdb.exists(None, "A", "NOT THERE"))
        cdb.set(None, "top.B.C", "OTHER_LABEL", 88)
        datum = cdb.get(None, "top.B.C", "OTHER_LABEL")
        self.assertEqual(88, datum)
        with self.assertRaises(error_classes.UVMConfigItemNotFound):
            _ = cdb.get(None, "A", "OTHER_LABEL")
        cdb.set(None, "", "BLANK", 99)
        datum = cdb.get(None, "", "BLANK")
        self.assertEqual(99, datum)

    def test_empty_db(self):
        cdb = ConfigDB()
        with self.assertRaises(error_classes.UVMConfigItemNotFound):
            cdb.get(None, "A", "LABEL")

        cdb.set(None, "A", "LABEL", 5)
        datum = cdb.get(None, "A", "LABEL")
        self.assertEqual(5, datum)

        with self.assertRaises(error_classes.UVMConfigItemNotFound):
            cdb.get(None, "B", "LABEL")

        cdb.set(None, "B", "OTHER_LABEL", 88)
        datum = cdb.get(None, "B", "OTHER_LABEL")
        self.assertEqual(88, datum)

        with self.assertRaises(error_classes.UVMConfigItemNotFound):
            cdb.get(None, "B", "LABEL")

    async def test_context(self):
        class comp(uvm_component):
            def build_phase(self):
                self.cdb_set("XXC", 93, "")
        class test(uvm_test):
            def build_phase(self):
                self.xx = comp("xx", self)
                self.cdb_set("XXC", 855, "")
            async def run_phase(self):
                self.raise_objection()
                time.sleep(0.1)
                self.drop_objection()

        cdb = ConfigDB()
        cdb.is_tracing = True
        await uvm_root().run_test("test", self.clock)
        cdb.set(uvm_root(), '*', "LABEL", 55)
        datum = cdb.get(uvm_root(), "tt", "LABEL")
        self.assertEqual(55, datum)
        utt = uvm_root().get_child("uvm_test_top")
        cdb.set(utt, "*", "WC", 99)
        datum = cdb.get(utt, "xx", "WC")
        self.assertEqual(99, datum)
        datum = utt.xx.cdb_get("XXC", "")
        self.assertEqual(93, datum)

    async def test_wildards(self):
        class comp(uvm_component):
            def build_phase(self):
                self.numb = ConfigDB().get(self, "", "CONFIG")
        class test(uvm_test):
            def build_phase(self):
                ConfigDB().set(self, "*", "CONFIG", 88)
                self.cc1 = comp("cc1", self)
                self.cc2 = comp("cc", self)
            async def run_phase(self):
                self.raise_objection()
                time.sleep(0.1)
                self.drop_objection()
        await uvm_root().run_test("test", self.clock)
        utt = uvm_root().get_child("uvm_test_top")
        self.assertEqual(88, utt.cc1.numb)
        self.assertEqual(88, utt.cc2.numb)

    async def test_one_wildard(self):
        class comp(uvm_component):
            def build_phase(self):
                self.numb = ConfigDB().get(self, "", "CONFIG")
        class test(uvm_test):
            def build_phase(self):
                ConfigDB().set(self, "*", "CONFIG", 88)
                ConfigDB().set(self, "cc2", "CONFIG", 66)
                self.cc1 = comp("cc1", self)
                self.cc2 = comp("cc2", self)
                self.cc3 = comp("cc3", self)

            async def run_phase(self):
                self.raise_objection()
                time.sleep(0.1)
                self.drop_objection()
        await uvm_root().run_test("test", self.clock)
        utt = uvm_root().get_child("uvm_test_top")
        self.assertEqual(88, utt.cc1.numb)
        self.assertEqual(66, utt.cc2.numb)
        self.assertEqual(88, utt.cc3.numb)

    async def test_precedence(self):
        class bottom(uvm_component):
            def build_phase(self):
                self.numb = ConfigDB().get(self, "", "CONFIG")

        class comp(uvm_component):
            def build_phase(self):
                ConfigDB().set(self, "*", "CONFIG", 55)
                self.bot = bottom("bot", self)

        class test(uvm_test):
            def build_phase(self):
                ConfigDB().set(self, "cc1.*", "CONFIG", 88)
                self.cc1 = comp("cc1", self)

            async def run_phase(self):
                self.raise_objection()
                time.sleep(0.1)
                self.drop_objection()

        await uvm_root().run_test("test", self.clock)
        utt = uvm_root().get_child("uvm_test_top")
        self.assertEqual(88, utt.cc1.bot.numb)

    async def test_wildcard_hierarchy_in_context(self):
        class Printer(uvm_component):
            def build_phase(self):
                self.msg = ConfigDB().get(self, "", "MSG")

        class PrintTest(uvm_test):
            def build_phase(self):
                self.pmsg = f"Hooray for {self.get_name()}!"
                self.mmsg = "Settle down, you too."
                self.rmsg = "What's going on?"
                ConfigDB().set(self, 'p?', "MSG", self.pmsg)
                ConfigDB().set(self, 'm*', "MSG", self.mmsg)
                ConfigDB().set(self, '*', "MSG",  self.rmsg)
                self.p1 = Printer("p1", self)
                self.p2 = Printer("p2", self)
                self.mediator = Printer("mediator", self)
                self.reporters = Printer("reporters", self)
            async def run_phase(self):
                self.raise_objection()
                self.drop_objection()

        await uvm_root().run_test("PrintTest", self.clock)
        utt = uvm_root().get_child("uvm_test_top")
        self.assertEqual(utt.pmsg, utt.p1.msg)
        self.assertEqual(utt.pmsg, utt.p2.msg)
        self.assertEqual(utt.mmsg, utt.mediator.msg)
        self.assertEqual(utt.rmsg, utt.reporters.msg)


    async def test_wildcard_hierarchy_at_root(self):
        class Printer(uvm_component):
            def build_phase(self):
                self.msg = ConfigDB().get(self, "", "MSG")

        class PrintTest(uvm_test):
            def build_phase(self):
                self.pmsg = f"Hooray for {self.get_name()}!"
                self.mmsg = "Settle down, you too."
                self.rmsg = "What's going on?"
                ConfigDB().set(None, '*p?', "MSG", self.pmsg)
                ConfigDB().set(None, '*me*', "MSG", self.mmsg)
                ConfigDB().set(None, '*', "MSG",  self.rmsg)
                self.p1 = Printer("p1", self)
                self.p2 = Printer("p2", self)
                self.mediator = Printer("mediator", self)
                self.reporters = Printer("reporters", self)
            async def run_phase(self):
                self.raise_objection()
                self.drop_objection()

        await uvm_root().run_test("PrintTest", self.clock)
        utt = uvm_root().get_child("uvm_test_top")
        self.assertEqual(utt.pmsg, utt.p1.msg)
        self.assertEqual(utt.pmsg, utt.p2.msg)
        self.assertEqual(utt.mmsg, utt.mediator.msg)
        self.assertEqual(utt.rmsg, utt.reporters.msg)

