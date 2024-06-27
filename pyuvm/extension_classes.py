import functools
import inspect

import cocotb

from pyuvm import uvm_root
from pyuvm._utils import cocotb_version_info


def test(
    timeout_time=None,
    timeout_unit="step",
    expect_fail=False,
    expect_error=(),
    skip=False,
    stage=None,
    keep_singletons=False,
    keep_set=set(),
):
    if cocotb_version_info >= (1, 7, 0) and stage is None:
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
        @functools.wraps(cls)
        async def test(_):
            await uvm_root().run_test(
                cls, keep_singletons=keep_singletons, keep_set=keep_set
            )

        if cocotb_version_info < (2, 0):
            # adds cocotb.test object to caller's module
            caller_frame = inspect.stack()[1]
            caller_module = inspect.getmodule(caller_frame[0])
            setattr(caller_module, f"test_{test._id}", test)

        # returns decorator class unmodified
        return cls

    return decorator
