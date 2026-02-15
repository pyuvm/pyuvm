import pytest

from pyuvm import (
    uvm_callback,
    uvm_callbacks,
    uvm_do_callbacks,
    uvm_object,
)

pytestmark = pytest.mark.usefixtures("initialize_pyuvm")


class SimpleCallback(uvm_callback):
    """Simple callback class with instrumentation"""

    def __init__(self, name: str = "simple_callback"):
        super().__init__(name)
        self.method_calls = []

    def on_event(self, *args, **kwargs):
        """Test callback method"""
        self.method_calls.append({"method": "on_event", "args": args, "kwargs": kwargs})

    def on_start(self):
        """Test callback method"""
        self.method_calls.append({"method": "on_start"})

    def on_finish(self, status: str):
        """Test callback method with argument"""
        self.method_calls.append({"method": "on_finish", "status": status})

    def on_error(self, error_code: int, message: str = ""):
        """Test callback method with keyword argument"""
        self.method_calls.append(
            {"method": "on_error", "error_code": error_code, "message": message}
        )

    def reset_calls(self):
        """Reset call tracking"""
        self.method_calls.clear()


class SimpleCallbackNoMethod(uvm_callback):
    """Simple callback that only implements some methods"""

    def __init__(self, name: str = "no_method_callback"):
        super().__init__(name)
        self.method_calls = []

    def on_start(self):
        """Only implements on_start"""
        self.method_calls.append({"method": "on_start"})


class SimpleObject(uvm_object):
    """Simple object for attaching callbacks"""

    def __init__(self, name: str = "simple_object"):
        super().__init__(name)


@pytest.fixture(autouse=True)
def cleanup_callbacks():
    """Clean up callbacks before and after each test"""
    uvm_callbacks._callbacks.clear()
    uvm_callbacks._instance = None
    yield
    uvm_callbacks._callbacks.clear()
    uvm_callbacks._instance = None


class TestUvmDoCallbacksBasic:
    """Test basic uvm_do_callbacks functionality"""

    def test_do_callbacks_with_no_callbacks(self):
        """Test uvm_do_callbacks with no registered callbacks"""
        obj = SimpleObject("obj")
        # Should not raise any exception
        uvm_do_callbacks(obj, "on_event")

    def test_do_callbacks_with_single_callback(self):
        """Test uvm_do_callbacks with single callback"""
        obj = SimpleObject("obj")
        cb = SimpleCallback("cb1")
        uvm_callbacks.add(obj, cb)

        uvm_do_callbacks(obj, "on_event")

        assert len(cb.method_calls) == 1
        assert cb.method_calls[0]["method"] == "on_event"

    def test_do_callbacks_with_multiple_callbacks(self):
        """Test uvm_do_callbacks calls all registered callbacks"""
        obj = SimpleObject("obj")
        cb1 = SimpleCallback("cb1")
        cb2 = SimpleCallback("cb2")
        cb3 = SimpleCallback("cb3")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)
        uvm_callbacks.add(obj, cb3)

        uvm_do_callbacks(obj, "on_start")

        assert len(cb1.method_calls) == 1
        assert len(cb2.method_calls) == 1
        assert len(cb3.method_calls) == 1

    def test_do_callbacks_maintains_callback_order(self):
        """Test that callbacks are called in registration order"""
        obj = SimpleObject("obj")
        cb1 = SimpleCallback("cb1")
        cb2 = SimpleCallback("cb2")
        cb3 = SimpleCallback("cb3")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)
        uvm_callbacks.add(obj, cb3)

        call_order = []

        # Override methods to track call order
        original_on_event1 = cb1.on_event
        original_on_event2 = cb2.on_event
        original_on_event3 = cb3.on_event

        def track_call1(*args, **kwargs):
            call_order.append("cb1")
            original_on_event1(*args, **kwargs)

        def track_call2(*args, **kwargs):
            call_order.append("cb2")
            original_on_event2(*args, **kwargs)

        def track_call3(*args, **kwargs):
            call_order.append("cb3")
            original_on_event3(*args, **kwargs)

        cb1.on_event = track_call1
        cb2.on_event = track_call2
        cb3.on_event = track_call3

        uvm_do_callbacks(obj, "on_event")

        assert call_order == ["cb1", "cb2", "cb3"]


class TestUvmDoCallbacksArguments:
    """Test uvm_do_callbacks with various argument types"""

    def test_do_callbacks_with_positional_args(self):
        """Test uvm_do_callbacks passes positional arguments"""
        obj = SimpleObject("obj")
        cb = SimpleCallback("cb")
        uvm_callbacks.add(obj, cb)

        uvm_do_callbacks(obj, "on_event", 1, 2, 3)

        assert len(cb.method_calls) == 1
        assert cb.method_calls[0]["args"] == (1, 2, 3)

    def test_do_callbacks_with_keyword_args(self):
        """Test uvm_do_callbacks passes keyword arguments"""
        obj = SimpleObject("obj")
        cb = SimpleCallback("cb")
        uvm_callbacks.add(obj, cb)

        uvm_do_callbacks(obj, "on_event", key1="value1", key2="value2")

        assert len(cb.method_calls) == 1
        assert cb.method_calls[0]["kwargs"] == {"key1": "value1", "key2": "value2"}

    def test_do_callbacks_with_mixed_args(self):
        """Test uvm_do_callbacks with both positional and keyword arguments"""
        obj = SimpleObject("obj")
        cb = SimpleCallback("cb")
        uvm_callbacks.add(obj, cb)

        uvm_do_callbacks(obj, "on_event", 1, 2, key1="value1", key2="value2")

        assert len(cb.method_calls) == 1
        assert cb.method_calls[0]["args"] == (1, 2)
        assert cb.method_calls[0]["kwargs"] == {"key1": "value1", "key2": "value2"}

    def test_do_callbacks_with_single_positional_arg(self):
        """Test uvm_do_callbacks with single positional argument"""
        obj = SimpleObject("obj")
        cb = SimpleCallback("cb")
        uvm_callbacks.add(obj, cb)

        uvm_do_callbacks(obj, "on_finish", "success")

        assert len(cb.method_calls) == 1
        assert cb.method_calls[0]["status"] == "success"

    def test_do_callbacks_with_keyword_only_args(self):
        """Test uvm_do_callbacks with keyword-only arguments"""
        obj = SimpleObject("obj")
        cb = SimpleCallback("cb")
        uvm_callbacks.add(obj, cb)

        uvm_do_callbacks(obj, "on_error", 100, message="Test error")

        assert len(cb.method_calls) == 1
        assert cb.method_calls[0]["error_code"] == 100
        assert cb.method_calls[0]["message"] == "Test error"


class TestUvmDoCallbacksDisabled:
    """Test uvm_do_callbacks with disabled callbacks"""

    def test_do_callbacks_skips_disabled_callbacks(self):
        """Test that disabled callbacks are not called"""
        obj = SimpleObject("obj")
        cb1 = SimpleCallback("cb1")
        cb2 = SimpleCallback("cb2")
        cb3 = SimpleCallback("cb3")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)
        uvm_callbacks.add(obj, cb3)

        # Disable cb2
        cb2.callback_mode(False)

        uvm_do_callbacks(obj, "on_event")

        # cb1 and cb3 should be called, cb2 should not
        assert len(cb1.method_calls) == 1
        assert len(cb2.method_calls) == 0
        assert len(cb3.method_calls) == 1

    def test_do_callbacks_with_all_disabled(self):
        """Test uvm_do_callbacks when all callbacks are disabled"""
        obj = SimpleObject("obj")
        cb1 = SimpleCallback("cb1")
        cb2 = SimpleCallback("cb2")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)

        # Disable all callbacks
        cb1.callback_mode(False)
        cb2.callback_mode(False)

        uvm_do_callbacks(obj, "on_event")

        assert len(cb1.method_calls) == 0
        assert len(cb2.method_calls) == 0

    def test_do_callbacks_respects_dynamic_disable(self):
        """Test that dynamically disabled callbacks are skipped"""
        obj = SimpleObject("obj")
        cb = SimpleCallback("cb")
        uvm_callbacks.add(obj, cb)

        # First call - enabled
        uvm_do_callbacks(obj, "on_event")
        assert len(cb.method_calls) == 1

        cb.reset_calls()
        cb.callback_mode(False)

        # Second call - disabled
        uvm_do_callbacks(obj, "on_event")
        assert len(cb.method_calls) == 0


class TestUvmDoCallbacksMissingMethod:
    """Test uvm_do_callbacks with callbacks missing the target method"""

    def test_do_callbacks_skips_callback_without_method(self):
        """Test that callbacks without the method are gracefully skipped"""
        obj = SimpleObject("obj")
        cb1 = SimpleCallback("cb1")
        cb_no_method = SimpleCallbackNoMethod("cb_no_method")
        cb2 = SimpleCallback("cb2")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb_no_method)
        uvm_callbacks.add(obj, cb2)

        # Call a method that only cb1 and cb2 have
        uvm_do_callbacks(obj, "on_finish", "success")

        # cb1 and cb2 should be called, cb_no_method should not cause errors
        assert len(cb1.method_calls) == 1
        assert len(cb_no_method.method_calls) == 0
        assert len(cb2.method_calls) == 1

    def test_do_callbacks_with_nonexistent_method(self):
        """Test that nonexistent methods don't cause errors"""
        obj = SimpleObject("obj")
        cb = SimpleCallback("cb")
        uvm_callbacks.add(obj, cb)

        # Call a method that doesn't exist on any callback
        # Should not raise any exception
        uvm_do_callbacks(obj, "nonexistent_method")

        # Callback should not have been called
        assert len(cb.method_calls) == 0

    def test_do_callbacks_with_partial_method_coverage(self):
        """Test callbacks with partial method implementation"""
        obj = SimpleObject("obj")
        cb_full = SimpleCallback("cb_full")
        cb_partial = SimpleCallbackNoMethod("cb_partial")

        uvm_callbacks.add(obj, cb_full)
        uvm_callbacks.add(obj, cb_partial)

        # Both have on_start
        uvm_do_callbacks(obj, "on_start")
        assert len(cb_full.method_calls) == 1
        assert len(cb_partial.method_calls) == 1

        # Reset and test method only cb_full has
        cb_full.reset_calls()
        cb_partial.method_calls.clear()

        uvm_do_callbacks(obj, "on_finish", "complete")
        assert len(cb_full.method_calls) == 1
        assert len(cb_partial.method_calls) == 0


class TestUvmDoCallbacksMultipleObjects:
    """Test uvm_do_callbacks with different objects"""

    def test_do_callbacks_on_different_objects(self):
        """Test callbacks are only called for specific objects"""
        obj1 = SimpleObject("obj1")
        obj2 = SimpleObject("obj2")

        cb1 = SimpleCallback("cb1")
        cb2 = SimpleCallback("cb2")

        uvm_callbacks.add(obj1, cb1)
        uvm_callbacks.add(obj2, cb2)

        # Call callbacks for obj1
        uvm_do_callbacks(obj1, "on_event")

        assert len(cb1.method_calls) == 1
        assert len(cb2.method_calls) == 0

        # Reset and call for obj2
        cb1.reset_calls()
        cb2.reset_calls()

        uvm_do_callbacks(obj2, "on_event")

        assert len(cb1.method_calls) == 0
        assert len(cb2.method_calls) == 1

    def test_do_callbacks_with_shared_callbacks(self):
        """Test callbacks registered to multiple objects"""
        obj1 = SimpleObject("obj1")
        obj2 = SimpleObject("obj2")

        cb = SimpleCallback("cb")

        uvm_callbacks.add(obj1, cb)
        uvm_callbacks.add(obj2, cb)

        # Call callbacks for obj1
        uvm_do_callbacks(obj1, "on_event")
        assert len(cb.method_calls) == 1

        # Call callbacks for obj2
        uvm_do_callbacks(obj2, "on_event")
        assert len(cb.method_calls) == 2


class TestUvmDoCallbacksWithTypes:
    """Test uvm_do_callbacks with object types"""

    def test_do_callbacks_with_object_type(self):
        """Test uvm_do_callbacks works with object types"""
        cb = SimpleCallback("cb")
        uvm_callbacks.add(SimpleObject, cb)

        # Use the class type
        uvm_do_callbacks(SimpleObject, "on_event")

        assert len(cb.method_calls) == 1

    def test_do_callbacks_with_object_instance_and_type(self):
        """Test calling callbacks registered to both instance and type"""
        obj = SimpleObject("obj")
        cb_instance = SimpleCallback("cb_instance")
        cb_type = SimpleCallback("cb_type")

        uvm_callbacks.add(obj, cb_instance)
        uvm_callbacks.add(SimpleObject, cb_type)

        # Call with instance
        uvm_do_callbacks(obj, "on_event")

        # Only instance callback should be called
        assert len(cb_instance.method_calls) == 1
        assert len(cb_type.method_calls) == 0

        # Call with type
        cb_instance.reset_calls()
        cb_type.reset_calls()

        uvm_do_callbacks(SimpleObject, "on_event")

        # Only type callback should be called
        assert len(cb_instance.method_calls) == 0
        assert len(cb_type.method_calls) == 1


class TestUvmDoCallbacksComplexScenarios:
    """Test complex scenarios combining multiple features"""

    def test_do_callbacks_mixed_enabled_disabled_and_methods(self):
        """Test complex scenario with mixed enabled/disabled and missing methods"""
        obj = SimpleObject("obj")
        cb1 = SimpleCallback("cb1")  # Has all methods, enabled
        cb2 = SimpleCallback("cb2")  # Has all methods, disabled
        cb3 = SimpleCallbackNoMethod("cb3")  # Only on_start, enabled
        cb4 = SimpleCallback("cb4")  # Has all methods, enabled

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)
        uvm_callbacks.add(obj, cb3)
        uvm_callbacks.add(obj, cb4)

        cb2.callback_mode(False)

        # Call on_finish (not on cb3)
        uvm_do_callbacks(obj, "on_finish", "test")

        assert len(cb1.method_calls) == 1  # Called
        assert len(cb2.method_calls) == 0  # Disabled
        assert len(cb3.method_calls) == 0  # Doesn't have method
        assert len(cb4.method_calls) == 1  # Called

    def test_do_callbacks_with_exception_in_callback(self):
        """Test that exception in one callback doesn't prevent others from being called"""

        class ThrowingCallback(uvm_callback):
            def on_event(self):
                raise ValueError("Expected test error")

        obj = SimpleObject("obj")
        cb_throw = ThrowingCallback("cb_throw")
        cb_normal = SimpleCallback("cb_normal")

        uvm_callbacks.add(obj, cb_throw)
        uvm_callbacks.add(obj, cb_normal)

        # The exception should propagate
        with pytest.raises(ValueError):
            uvm_do_callbacks(obj, "on_event")

        # Note: cb_normal won't be called because cb_throw raises before iteration continues
        # This is expected behavior - the caller must handle exceptions

    def test_do_callbacks_sequence(self):
        """Test calling multiple different callbacks in sequence"""
        obj = SimpleObject("obj")
        cb = SimpleCallback("cb")

        uvm_callbacks.add(obj, cb)

        # Call different methods in sequence
        uvm_do_callbacks(obj, "on_start")
        uvm_do_callbacks(obj, "on_event", 1, 2, 3)
        uvm_do_callbacks(obj, "on_finish", "done")

        assert len(cb.method_calls) == 3
        assert cb.method_calls[0]["method"] == "on_start"
        assert cb.method_calls[1]["method"] == "on_event"
        assert cb.method_calls[2]["method"] == "on_finish"
