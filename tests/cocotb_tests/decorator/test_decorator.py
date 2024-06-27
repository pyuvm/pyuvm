import inspect
from pyuvm import *
import pyuvm


class MySingleton(metaclass=pyuvm.Singleton):
    def __init__(self):
        self.datum = None
class MySingleton2(MySingleton):
    pass

class MySingleton3(MySingleton):
    pass

@pyuvm.test()
class NewSingleton(uvm_test):
    def build_phase(self):
        self.mysingleton = MySingleton()

    def check_phase(self):
        assert self.mysingleton.datum is None

    async def run_phase(self):
        self.raise_objection()
        self.drop_objection()


@pyuvm.test()
class SetDatumTo42Test(uvm_test):
    def build_phase(self):
        self.mysingleton = MySingleton()

    async def run_phase(self):
        self.raise_objection()
        self.mysingleton.datum = 42
        self.drop_objection()

@pyuvm.test()
class CheckDatumisNone(uvm_test):
    def build_phase(self):
        self.mysingleton = MySingleton()

    def check_phase(self):
        assert self.mysingleton.datum is None

    async def run_phase(self):
        self.raise_objection()
        self.drop_objection()


@pyuvm.test()
class SetDatumTo42AgainTest(uvm_test):
    def build_phase(self):
        self.mysingleton = MySingleton()

    async def run_phase(self):
        self.raise_objection()
        self.mysingleton.datum = 42
        self.drop_objection()

@pyuvm.test(keep_singletons=True)
class CheckDatumis42(uvm_test):
    def build_phase(self):
        self.mysingleton = MySingleton()

    def check_phase(self):
        assert self.mysingleton.datum == 42

    async def run_phase(self):
        self.raise_objection()
        self.drop_objection()

@pyuvm.test()
class SetDatumTo442(uvm_test):
    def build_phase(self):
        self.mysingleton = MySingleton()

    async def run_phase(self):
        self.raise_objection()
        self.mysingleton.datum = 442
        self.drop_objection()

@pyuvm.test(keep_set=set([MySingleton]))
class CheckDatumis442(uvm_test):
    def build_phase(self):
        self.mysingleton = MySingleton()

    def check_phase(self):
        assert self.mysingleton.datum == 442

    async def run_phase(self):
        self.raise_objection()
        self.drop_objection()

@pyuvm.test()
class SetMultipleSingletons(uvm_test):
    def build_phase(self):
        self.mysingleton = MySingleton()
        self.mysingleton2 = MySingleton2()
        self.mysingleton3 = MySingleton3()

    async def run_phase(self):
        self.raise_objection()
        self.mysingleton.datum = 111
        self.mysingleton2.datum = 222
        self.mysingleton3.datum = 333
        self.drop_objection()

pyuvm.test()
class CheckMultipleSingletonAreNone(uvm_test):
    def build_phase(self):
        self.mysingleton = MySingleton()
        self.mysingleton2 = MySingleton2()
        self.mysingleton3 = MySingleton3()

    def check_phase(self):
        assert self.mysingleton.datum is None
        assert self.mysingleton2.datum is None
        assert self.mysingleton3.datum is None

    async def run_phase(self):
        self.raise_objection()
        self.drop_objection()

@pyuvm.test()
class SetMultipleSingletonsAgain(SetMultipleSingletons):
    pass

@pyuvm.test(keep_singletons=True)
class CheckMultipleSingletonAreSet(uvm_test):
    def build_phase(self):
        self.mysingleton = MySingleton()
        self.mysingleton2 = MySingleton2()
        self.mysingleton3 = MySingleton3()

    def check_phase(self):
        assert self.mysingleton.datum == 111
        assert self.mysingleton2.datum == 222
        assert self.mysingleton3.datum == 333

    async def run_phase(self):
        self.raise_objection()
        self.drop_objection()

@pyuvm.test(keep_set=set([MySingleton, MySingleton3]))
class CheckMultipleSingletonAreSetAgain(uvm_test):
    def build_phase(self):
        self.mysingleton = MySingleton()
        self.mysingleton2 = MySingleton2()
        self.mysingleton3 = MySingleton3()

    def check_phase(self):
        assert self.mysingleton.datum == 111
        assert self.mysingleton2.datum is None
        assert self.mysingleton3.datum == 333

    async def run_phase(self):
        self.raise_objection()
        self.drop_objection()