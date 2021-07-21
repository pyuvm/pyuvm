import cocotb
import inspect
import tests

@cocotb.test()
async def test_08_factory(dut):
    """Tests different aspects of the factory"""
    print("****** Running test ******")
    tc08 = tests.TestHolder()
    methods = inspect.getmembers(tests.TestHolder)#, predicate=inspect.ismethod)
    for mm in methods:
        (name,function) = mm
        if name.startswith("test_"):
            test = getattr(tc08, name)
            tc08.setUp()
            print("******* Running ", name)
            test()
            tc08.tearDown()
    assert True


