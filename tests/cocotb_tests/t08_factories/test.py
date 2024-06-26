import cocotb
import inspect
import factory_tests as t08


@cocotb.test() # pylint: disable=no-value-for-parameter
async def test_08_factory(dut):
    """Tests different aspects of the factory"""
    tc08 = t08.s08_factory_classes_TestCase()
    methods = inspect.getmembers(t08.s08_factory_classes_TestCase)#, predicate=inspect.ismethod)
    for mm in methods:
        (name,_) = mm
        if name.startswith("test_"):
            print(name)
            test = getattr(tc08, name)
            tc08.setUp()
            if inspect.iscoroutinefunction(test):
                await test()
            else:
                test()
            tc08.tearDown()
    assert True


