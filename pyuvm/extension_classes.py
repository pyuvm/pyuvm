import functools
import inspect

import cocotb

from pyuvm._utils import cocotb_version_info
from pyuvm.s13_uvm_component import uvm_root


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
        test_dec_args = {
            "timeout_time": timeout_time,
            "timeout_unit": timeout_unit,
            "expect_fail": expect_fail,
            "expect_error": expect_error,
            "skip": skip,
            "stage": stage,
        }

        if cocotb_version_info >= (2, 0):
            # This sets the test name so that it can be selected appropriately using
            # COCOTB_TEST_FILTER in 2.0+. <2.0 won't have this luxury.
            test_dec_args["name"] = cls.__name__

        # create cocotb.test object to be picked up RegressionManager
        @cocotb.test(**test_dec_args)
        @functools.wraps(cls)
        async def test_obj(_):
            await uvm_root().run_test(
                cls, keep_singletons=keep_singletons, keep_set=keep_set
            )

        # adds cocotb.test object to caller's module
        caller_frame = inspect.stack()[1]
        caller_module = inspect.getmodule(caller_frame[0])
        if cocotb_version_info < (2, 0):
            setattr(caller_module, f"test_{test_obj._id}", test_obj)
        else:
            # In 2.0+ cocotb tests don't have a numbered ID.
            # This is fine since because we set "name" above, we can use the actual
            # test name when selecting individual tests rather than "test_{n}".
            setattr(caller_module, f"__{cls.__name__}", test_obj)

        # returns decorator class unmodified
        return cls

    return decorator
