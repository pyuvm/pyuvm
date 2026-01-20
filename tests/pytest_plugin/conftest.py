# SPDX-License-Identifier: Apache-2.0

"""Common fixtures and configurations used by all tests ``test_*.py`` defined in this directory."""

from pathlib import Path

from cocotb_tools.pytest.hdl import HDL
from pytest import Parser, PytestPluginManager, fixture, hookimpl

# The root of the pyuvm project (repository)
PROJECT_ROOT: Path = Path(__file__).parent.parent.parent.resolve()

# List of pytest plugins to enable
PLUGINS: tuple[str, ...] = (
    "cocotb_tools.pytest.plugin",
    "pyuvm_tools.pytest.plugin",
)


@hookimpl(tryfirst=True)
def pytest_addoption(parser: Parser, pluginmanager: PytestPluginManager) -> None:
    """Load pytest cocotb/pyuvm plugin in early stage of pytest when adding options to pytest.

    This will allow to automatically load plugin when invoking ``pytest`` with ``tests/pytest_plugin`` argument
    without need of providing additional ``-p cocotb_tools.pytest.plugin -p pyuvm_tools.pytest.plugin`` arguments.

    Most users in their projects will load plugin by defining an entry point in ``pyproject.toml`` file:

    .. code:: toml

        [project.entry-points.pytest11]
        cocotb = "cocotb_tools.pytest.plugin"
        pyuvm = "pyuvm_tools.pytest.plugin"

    Args:
        parser: Instance of command line arguments parser used by pytest.
        pluginmanager: Instance of pytest plugin manager.
    """
    for plugin in PLUGINS:
        if not pluginmanager.has_plugin(plugin):
            pluginmanager.import_plugin(plugin)  # import and register plugin


# The "hdl" fixture is defined in the cocotb pytest plugin and it is used to define HDL design
# that will be built and tested. Created "tinyalu" fixture can be used in cocotb runner test functions
# to invoke the tinyalu.test() method that will run HDL simulator with cocotb tests for this HDL design.
@fixture
def tinyalu(hdl: HDL) -> HDL:
    """Define HDL design for the ``TinyALU`` module."""
    src: Path = PROJECT_ROOT / "examples" / "TinyALU" / "hdl"

    # TODO: This can be removed after merging https://github.com/cocotb/cocotb/pull/5243
    # Setting explicitly name of toplevel will be optional in cocotb pytest plugin
    # Default value will be implicitly based on the last added HDL source file
    hdl.toplevel = "tinyalu"

    # The "toplevel_lang" attribute, if not specified via the --cocotb-toplevel-lang=<vhdl|verilog> option,
    # is set to "vhdl" for NVC and GHDL simulators, to "verilog" for Verilator and Icarus simulators, set empty for others
    if hdl.toplevel_lang == "vhdl":
        hdl.sources = [
            src / "vhdl" / "single_cycle_add_and_xor.vhd",
            src / "vhdl" / "three_cycle_mult.vhd",
            src / "vhdl" / "tinyalu.vhd",
        ]
    else:
        hdl.sources = [
            src / "verilog" / "tinyalu.sv",
        ]

    # TODO: This can be removed after merging https://github.com/cocotb/cocotb/pull/5243
    # The hdl.build() method will be implicitly invoked by the hdl.test() method if it was not called explicitly
    hdl.build()

    # Return defined HDL design that will be tested
    return hdl
