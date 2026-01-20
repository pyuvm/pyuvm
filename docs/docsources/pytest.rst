.. _pytest-support:

**************
Pytest Support
**************

The :mod:`cocotb_tools.pytest.plugin` with the :mod:`pyuvm_tools.pytest.plugin` provides full `pytest`_ integration with cocotb and PyUVM.

For more details please visit the official Cocotb documentation about `Pytest Support`_.


.. _pytest-plugin-enable:

Enabling the Plugin
===================

:py:mod:`pyuvm_tools.pytest.plugin` can be enabled in various ways.

In a Python project
-------------------

When using the `pyproject.toml`_ file (recommended way):

.. code:: toml

    [project.entry-points.pytest11]
    cocotb = "cocotb_tools.pytest.plugin"
    pyuvm = "pyuvm_tools.pytest.plugin"

When using the ``pytest.ini`` file:

.. code:: ini

    [pytest]
    addopts = -p cocotb_tools.pytest.plugin -p pyuvm_tools.pytest.plugin

When using the ``setup.cfg`` file:

.. code:: ini

    [options.entry_points]
    pytest11 =
      cocotb = cocotb_tools.pytest.plugin
      cocotb = pyuvm_tools.pytest.plugin

When using the ``setup.py`` file:

.. code:: python

    from setuptools import setup

    setup(
        # ...,
        entry_points={
            "pytest11": [
                "cocotb = cocotb_tools.pytest.plugin",
                "pyuvm = pyuvm_tools.pytest.plugin",
            ],
        },
    )

In a non-Python project
-----------------------

By defining the global variable ``pytest_plugins`` when using a ``conftest.py`` file
(which must be located in the root of the project):

.. code:: python

    pytest_plugins = ("cocotb_tools.pytest.plugin", "pyuvm_tools.pytest.plugin")

By defining the ``PYTEST_PLUGINS`` environment variable:

.. code:: shell

    export PYTEST_PLUGINS="cocotb_tools.pytest.plugin,pyuvm_tools.pytest.plugin"

By using the ``-p <plugin>`` option when invoking the `pytest`_ command line interface:

.. code:: shell

    pytest -p cocotb_tools.pytest.plugin -p pyuvm_tools.pytest.plugin ...


.. _pytest-plugin-fixtures:

Fixtures
========

The :deco:`!pytest.mark.pyuvm_fixtures` can be used to request `pytest`_ fixtures by PyUVM test:

.. code:: python

    # test_*.py

    from typing import Any
    from pathlib import Path

    import pytest
    from pytest import LogCaptureFixture
    from pyuvm import uvm_test


    @pytest.mark.pyuvm_fixtures("tmp_path", "caplog", "dut")
    class TestDUTFeature(uvm_test):
        """Test DUT feature with requested pytest fixtures."""

        dut: Any
        tmp_path: Path
        caplog: LogCaptureFixture

        def build_phase(self) -> None:
            """Build UVM components."""
            assert self.dut is not None
            assert self.tmp_path
            assert self.caplog


Parametrize
===========

The :deco:`pytest.mark.parametrize` fixture can be used to parametrize PyUVM test:

.. code:: python

    # test_*.py

    import pytest
    from pyuvm import uvm_test


    @pytest.mark.parametrize("x", (1, 2))
    @pytest.mark.parametrize("y", (3, 4, 5))
    class TestDUTFeature(uvm_test):
        """Test DUT feature with different parameters."""

        x: int = 0
        y: int = 0

        def build_phase(self) -> None:
            """Build UVM components."""
            assert self.x in (1, 2)
            assert self.y in (3, 4, 5)


.. _pytest-plugin-examples:

Examples
========

Define a new HDL design by using the :class:`cocotb_tools.pytest.hdl.HDL` fixture in the ``tests/conftest.py`` file:

.. code:: python

    # tests/conftest.py

    """Common fixtures and configurations used by all tests ``test_*.py`` defined in this directory."""

    from pathlib import Path

    import pytest
    from cocotb_tools.pytest.hdl import HDL

    # The root of the project (repository), assuming the "tests" directory
    PROJECT_ROOT: Path = Path(__file__).parent.parent.resolve()


    @pytest.fixture
    def sample_module(hdl: HDL) -> HDL:
        """Define HDL design by adding HDL source files to it.

        Args:
            hdl: Fixture created by the cocotb pytest plugin, representing a HDL design.

        Returns:
            Representation of HDL design with added HDL source files.
        """
        hdl.sources = (
            # List HDL source files,
            PROJECT_ROOT / "hdl" / "sample_module.sv",
        )

        return hdl


Define a cocotb runner with PyUVM tests in ``tests/test_*.py`` file:

.. code:: python

    # tests/test_sample_module.py

    from cocotb_tools.pytest.hdl import HDL
    from pyuvm import uvm_test


    def test_sample_module(sample_module: HDL) -> None:
        """Build and test HDL module with pyuvm tests."""
        sample_module.test()


    class TestSampleModuleFeature1(uvm_test):
        """Test feature 1."""


    class TestSampleModuleFeature2(uvm_test):
        """Test feature 2."""


To list all available tests:

.. code:: shell

    pytest -v --collect-only

To run all tests:

.. code:: shell

    pytest

To run specific test:

.. code:: shell

    pytest -k TestSampleModuleFeature2


.. _pytest: https://docs.pytest.org/en/stable/contents.html
.. _pyproject.toml: https://packaging.python.org/en/latest/specifications/pyproject-toml/
.. _Pytest Support: https://docs.cocotb.org/en/development/pytest.html
