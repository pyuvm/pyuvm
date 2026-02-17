# SPDX-License-Identifier: Apache-2.0

"""Testing the pyuvm pytest plugin by using the ``TinyALU`` module as reference."""

from pathlib import Path
from typing import Any

import pytest
from cocotb_tools.pytest.hdl import HDL
from pytest import LogCaptureFixture

import pyuvm
from pyuvm import uvm_test


# NOTE: @pytest.mark.cocotb_runner can be removed after merging https://github.com/cocotb/cocotb/pull/5260
@pytest.mark.cocotb_runner
def test_tinyalu(tinyalu: HDL) -> None:
    """Build and test the ``TinyALU`` module with cocotb/pyuvm tests defined in this file."""
    tinyalu.test()


async def test_tinyalu_with_cocotb(dut) -> None:
    """Direct testing by using the ``cocotb`` directly."""


class TestBase(uvm_test):
    """test base for all tests."""

    async def run_phase(self) -> None:
        self.raise_objection()
        print(f"{self.__class__!r}: Hello from run phase!")
        self.drop_objection()


# With the pyuvm pytest plugin, decorators are not needed. Requirements:
# - Name for test MUST start with the "Test" prefix
# - It MUST be a class inherit from the :class:`pyuvm.uvm_test` class (directly or indirectly)
class TestTinyALUWithoutDecorators(TestBase):
    """pyuvm test without need of using :deco:`pyuvm.test` or :deco:`!pytest.mark.pyuvm_test` decorators."""


# Pytest marker provided by the pyuvm pytest plugin
# It allows to use any name for test. No need for the "Test" prefix
@pytest.mark.pyuvm_test
class TinyALUWithPytestMarker(TestBase):
    """pyuvm test marked with the :deco:`!pytest.mark.pyuvm_test` decorator."""


@pyuvm.test()
class TinyALUWithPyUVMDecorator(TestBase):
    """pyuvm test marked with the :deco:`pyuvm.test` decorator (old-way)."""


@pyuvm.test()
@pytest.mark.parametrize("x", (1, 2))
@pytest.mark.parametrize("y", (3, 4))
@pytest.mark.pyuvm_fixtures("tmp_path", "caplog", "dut")
class TinyALUParametrizeWithPyUVMDecorator(TestBase):
    """pyuvm test marked with the :deco:`pyuvm.test` decorator (old-way)."""

    dut: Any
    tmp_path: Path
    caplog: LogCaptureFixture
    x: int = 0
    y: int = 0

    def build_phase(self) -> None:
        assert self.dut is not None
        assert self.tmp_path
        assert self.caplog
        assert self.x in (1, 2)
        assert self.y in (3, 4)


@pytest.mark.parametrize("a", (True, False))
@pytest.mark.parametrize("b", ("x", "y"))
@pytest.mark.pyuvm_fixtures("dut", "caplog")
class TestTinyALUParametrizeWithoutDecorators(TestBase):
    """pyuvm test without need of using :deco:`pyuvm.test` or :deco:`!pytest.mark.pyuvm_test` decorators."""

    dut: Any
    caplog: LogCaptureFixture
    a: bool = False
    b: str = ""

    def build_phase(self) -> None:
        assert self.dut is not None
        assert self.caplog
        assert self.a in (True, False)
        assert self.b in ("x", "y")
