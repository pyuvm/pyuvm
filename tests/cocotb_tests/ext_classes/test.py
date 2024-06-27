import inspect
import test_12_uvm_tlm_interfaces as test_mod
from pyuvm import *
import pyuvm
import cocotb


async def run_tests(dut):
    tests_pass = {}
    t12 = test_mod.s12_uvm_tlm_interfaces_TestCase()
    methods = inspect.getmembers(test_mod.s12_uvm_tlm_interfaces_TestCase)  # predicate=inspect.ismethod)
    for mm in methods:
        (name, _) = mm
        if name.startswith("test_"):
            test = getattr(t12, name)
            t12.setUp()
            try:
                if inspect.iscoroutinefunction(test):
                    await test(dut)
                else:
                    test()
                tests_pass[name] = True
            except AssertionError:
                tests_pass[name] = False
            t12.tearDown()
    any_failed = False
    for test in tests_pass:
        if tests_pass[test]:
            pf = "Pass   "
        else:
            pf = "FAILED "
            any_failed = True
        print(f"{pf} {test}")
    assert not any_failed


class FIFO(uvm_component):
    def build_phase(self):
        self.fifo = uvm_tlm_analysis_fifo("fifo", self)
        self.gp = uvm_get_port("gp", self)

    def connect_phase(self):
        self.gp.connect(self.fifo.get_export)

    def start_of_simulation_phase(self):
        self.data = []

    async def run_phase(self):
        while True:
            datum = await self.gp.get()
            self.data.append(datum)


class Subscriber(uvm_subscriber):
    def start_of_simulation_phase(self):
        self.data = []

    def write(self, datum):
        self.data.append(datum)


class Export(uvm_analysis_export):
    def start_of_simulation_phase(self):
        self.data = []

    def write(self, datum):
        self.data.append(datum)


@pyuvm.test()
class AnalysisTest(uvm_test):
    def build_phase(self):
        self.gp = uvm_get_port("gp", self)
        self.ap1 = uvm_analysis_port("ap1", self)
        self.ap2 = uvm_analysis_port("ap2", self)
        self.export = Export("export", self)
        self.fifo = FIFO("fifo", self)
        self.subscriber = Subscriber("subscriber", self)

    def connect_phase(self):
        self.ap1.connect(self.ap2)
        self.ap2.connect(self.export)
        self.ap2.connect(self.subscriber.analysis_export)
        self.ap2.connect(self.fifo.fifo.analysis_export)

    async def run_phase(self):
        self.raise_objection()
        self.data_list = [1, '1', 2, 'two']
        for datum in self.data_list:
            self.ap1.write(datum)
        self.drop_objection()

    def check_phase(self):
        assert self.data_list == self.subscriber.data
        assert self.data_list == self.export.data
        assert self.data_list == self.fifo.data
