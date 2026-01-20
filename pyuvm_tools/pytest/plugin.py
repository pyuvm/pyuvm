# SPDX-License-Identifier: Apache-2.0

"""Pytest plugin that allows to collect and run pyuvm tests by cocotb pytest plugin."""

from collections.abc import Generator, Iterable
from functools import wraps
from inspect import Parameter, signature

from pytest import (
    Class,
    Collector,
    Config,
    Function,
    Item,
    Mark,
    Module,
    hookimpl,
    mark,
)

from pyuvm import uvm_root, uvm_test


@hookimpl(tryfirst=True)
def pytest_configure(config: Config) -> None:
    """Set plugin options and configure it."""
    config.addinivalue_line("markers", "pyuvm_test: Mark class as PyUVM test")
    config.addinivalue_line(
        "markers", "pyuvm_fixtures: Request fixtures for PyUVM test"
    )

    # Register internal plugin for pre and post processing actions for pytest hooks
    config.pluginmanager.register(_HookWrappers(), "pyuvm_hook_wrappers")


@hookimpl(tryfirst=True)
def pytest_pycollect_makeitem(
    collector: Module | Class, name: str, obj: object
) -> Item | Collector | list[Item | Collector] | None:
    """Pytest hook called on every collected object from Python module or class.

    Args:
        collector: Instance that is collecting objects from Python module or class.
        name: Name of collected object in Python module or class.
        obj: Collected object from Python module or class.

    Returns:
        Created pytest item (test) or collector (Python module -> Python class).
    """
    # Must be a class inherit from the uvm_test class
    if not isinstance(obj, type) or not issubclass(obj, uvm_test):
        # If not, delegate handling collected object to other plugins
        return None  # delegate to other plugins

    # Pytest treads classes as nested scoped namespaces for tests
    # We need to create a test function that will not override pyuvm test object class
    test_obj_name: str = f"__{name}"  # compatible with the @cocotb.test decorator

    # If test function was already defined or this is not an UVM test, do nothing
    # It will be or it was already created by other iteration of the pytest_pycollect_makeitem hook
    if hasattr(collector.obj, test_obj_name) or not _is_uvm_test(collector, name, obj):
        return []  # do nothing

    # Retrieve pytest markers from collected object
    markers: list[Mark] = list(getattr(obj, "pytestmark", ()))

    # Named argument "dut" is a pytest fixture defined in cocotb pytest plugin and it is required
    @wraps(obj)
    async def test_obj(*args: object, **kwargs: object) -> None:
        # Assign pytest fixtures to object class
        for key, value in kwargs.items():
            setattr(obj, key, value)

        await uvm_root().run_test(obj)

    if not any(marker.name == "cocotb_test" for marker in markers):
        markers.append(mark.cocotb_test().mark)

    # Add pytest markers test function
    setattr(test_obj, "pytestmark", markers)

    # Store created test function in Python module or class
    # Needed by the pytest code introspection mechanism that will retrieve parameter types, signature, file and line location
    setattr(collector.obj, test_obj_name, test_obj)

    # Delegate creating a pytest item (test) from collected object to other plugins (cocotb pytest plugin)
    return collector.ihook.pytest_pycollect_makeitem(
        collector=collector,
        name=test_obj_name,
        obj=test_obj,
    )


class _HookWrappers:
    """Hook wrappers for pytest hooks."""

    @hookimpl(trylast=True, wrapper=True)
    def pytest_pycollect_makeitem(
        self, collector: Module | Class, name: str, obj: object
    ) -> Generator[
        None,
        Item | Collector | list[Item | Collector] | None,
        list[Item | Collector] | None,
    ]:
        """Pre and post processing actions for the :func:`!pytest_pycollect_makeitem` hook.

        Args:
            collector: Instance that is collecting objects from Python module or class.
            name: Name of collected object in Python module or class.
            obj: Collected object from Python module or class.

        Returns:
            Created pytest item (test) or collector (Python module -> Python class).
        """
        # Add pytest fixtures to pyuvm test
        _update_test_signature(collector, name, obj)

        result: Item | Collector | list[Item | Collector] | None = yield

        if result is None:
            return None

        items: list[Item | Collector] = result if isinstance(result, list) else [result]

        for item in items:
            # Remove the "__" prefix from name of test function
            if isinstance(item, Function) and item.name.startswith("__"):
                item.name = item.name.removeprefix("__")
                item._nodeid = item.nodeid.replace("::__", "::")
                item.extra_keyword_matches.add(item.name)

        return items


def _is_uvm_test(collector: Module | Class, name: str, obj: object) -> bool:
    """Check if collected object from Python module or class is UVM test.

    Args:
        collector: Instance that is collecting objects from Python module or class.
        name: Name of collected object in Python module or class.
        obj: Collected object from Python module or class.

    Returns:
        :data:`True` if collected object is UVM test. Otherwise :data:`False`.
    """
    if collector.istestclass(obj, name):
        # It is following the pytest name convention for tests that must start with the Test prefix
        return True

    # Test was marked with the @pytest.mark.pyuvm_test marker
    markers: Iterable[Mark] | None = getattr(obj, "pytestmark", None)

    return any(marker.name == "pyuvm_test" for marker in markers or ())


def _update_test_signature(collector: Module | Class, name: str, obj: object) -> None:
    """Update test signature of collected object from Python module.

    Args:
        collector: Instance that is collecting objects from Python module or class.
        name: Name of collected object in Python module or class.
        obj: Collected object from Python module or class.
    """
    # pyuvm test as cocotb test starts from the "__" name prefix
    if not name.startswith("__"):
        return

    # pyuvm test (class type) is stored in the same Python module like cocotb test
    cls = getattr(collector.obj, name[2:], None)

    # Get test function (optionally it can be wrapped)
    func = getattr(obj, "__func__", obj)

    # Object class type MUST be uvm_test and collected object MUST be callable
    if (
        cls is None
        or not isinstance(cls, type)
        or not issubclass(cls, uvm_test)
        or not callable(func)
    ):
        return

    # ``@functools.wraps(uvm_test)`` will wrap function but use signature from the ``uvm_test.__init__(name, parent)``
    # The pytest introspection mechanism will treat all function arguments as fixtures
    # For "name" and "parent" will raise an error about not defined fixtures. We need to override these arguments
    sig = signature(func)

    # Requested pytest fixtures
    args: set[str] = set()

    # Get @pytest.mark.* markers from test function
    markers: Iterable[Mark] | None = getattr(obj, "pytestmark", None)

    for marker in markers or ():
        # @pytest.mark.parametrize("x,y", ((1, 2), (3, 4)))
        if marker.name == "parametrize" and marker.args:
            args.update(marker.args[0].split(","))

        # @pytest.mark.pyuvm_fixtures("caplog", "tmp_path")
        elif marker.name == "pyuvm_fixtures":
            args.update(marker.args)

    # Compose new arguments for test function
    parameters: list[Parameter] = [
        Parameter(name=arg, kind=Parameter.POSITIONAL_OR_KEYWORD) for arg in args
    ]

    # Override signature of test function with new arguments to make pytest happy
    setattr(func, "__signature__", sig.replace(parameters=parameters))
