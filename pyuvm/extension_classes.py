import cocotb

from pyuvm import uvm_root


def test(
    timeout_time=None,
    timeout_unit="step",
    expect_fail=False,
    expect_error=(),
    skip=False,
    stage=None,
):
    version_info = tuple(int(n) for n in cocotb.__version__.split("."))
    print(version_info)
    if version_info >= (1, 7, 0) and stage is None:
        stage = 0

    def decorator(cls):

        # create cocotb.test object to be picked up RegressionManager
        @cocotb.test(
            timeout_time=timeout_time,
            timeout_unit=timeout_unit,
            expect_fail=expect_fail,
            expect_error=expect_error,
            skip=skip,
            stage=stage,
        )
        async def test(_):
            await uvm_root().run_test(cls)

        test.class_ = cls
        test.__name__ = cls.__name__
        test.__qualname__ = cls.__qualname__
        test.__doc__ = cls.__doc__
        test.__module__ = cls.__module__

        # returns decorator class unmodified
        return test

    return decorator
