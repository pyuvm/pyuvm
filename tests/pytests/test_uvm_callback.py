import pytest

from pyuvm import uvm_callback, uvm_object

pytestmark = pytest.mark.usefixtures("initialize_pyuvm")


class test_callback(uvm_callback):
    """Test callback class extending uvm_callback"""

    def __init__(self, name: str = "test_callback"):
        super().__init__(name)
        self.call_count = 0
        self.last_args = None
        self.last_kwargs = None

    def on_event(self, *args, **kwargs):
        """Test callback method"""
        self.call_count += 1
        self.last_args = args
        self.last_kwargs = kwargs


class TestCallbackInitialization:
    """Test uvm_callback initialization"""

    def test_callback_creation_with_default_name(self):
        """Test creating callback with default name"""
        cb = uvm_callback()
        assert cb.get_name() == "uvm_callback"

    def test_callback_creation_with_custom_name(self):
        """Test creating callback with custom name"""
        cb = uvm_callback("my_callback")
        assert cb.get_name() == "my_callback"

    def test_callback_inherits_from_uvm_object(self):
        """Test that uvm_callback inherits from uvm_object"""
        cb = uvm_callback()
        assert isinstance(cb, uvm_object)

    def test_callback_is_enabled_by_default(self):
        """Test that callbacks are enabled by default"""
        cb = uvm_callback()
        assert cb._enabled is True

    def test_callback_custom_subclass(self):
        """Test creating custom callback subclass"""
        cb = test_callback("custom_cb")
        assert cb.get_name() == "custom_cb"
        assert cb.is_enabled() is True


class TestCallbackMode:
    """Test uvm_callback.callback_mode() method"""

    def test_callback_mode_returns_current_state(self):
        """Test callback_mode() returns current enabled state"""
        cb = uvm_callback()
        assert cb.callback_mode() is True

    def test_callback_mode_disable(self):
        """Test disabling callback with callback_mode()"""
        cb = uvm_callback()
        result = cb.callback_mode(False)
        assert result is True  # Returns previous state
        assert cb._enabled is False

    def test_callback_mode_enable(self):
        """Test enabling callback with callback_mode()"""
        cb = uvm_callback()
        cb.callback_mode(False)
        result = cb.callback_mode(True)
        assert result is False  # Returns previous state
        assert cb._enabled is True

    def test_callback_mode_toggle(self):
        """Test toggling callback mode"""
        cb = uvm_callback()

        # Initially enabled
        assert cb.callback_mode() is True

        # Disable
        cb.callback_mode(False)
        assert cb.callback_mode() is False

        # Enable
        cb.callback_mode(True)
        assert cb.callback_mode() is True

    def test_callback_mode_returns_previous_state(self):
        """Test that callback_mode returns the previous state before change"""
        cb = uvm_callback()

        # First call returns True (was enabled)
        result1 = cb.callback_mode(False)
        assert result1 is True

        # Second call returns False (was disabled)
        result2 = cb.callback_mode(True)
        assert result2 is False

    def test_callback_mode_read_only(self):
        """Test reading callback state without changing it"""
        cb = uvm_callback()
        cb.callback_mode(False)

        # Read state multiple times
        state1 = cb.callback_mode()
        state2 = cb.callback_mode()
        state3 = cb.callback_mode()

        # Should all be False and unchanged
        assert state1 is False
        assert state2 is False
        assert state3 is False
        assert cb._enabled is False


class TestCallbackIsEnabled:
    """Test uvm_callback.is_enabled() method"""

    def test_is_enabled_when_enabled(self):
        """Test is_enabled() returns True when enabled"""
        cb = uvm_callback()
        assert cb.is_enabled() is True

    def test_is_enabled_when_disabled(self):
        """Test is_enabled() returns False when disabled"""
        cb = uvm_callback()
        cb.callback_mode(False)
        assert cb.is_enabled() is False

    def test_is_enabled_after_toggle(self):
        """Test is_enabled() tracks state changes"""
        cb = uvm_callback()

        assert cb.is_enabled() is True
        cb.callback_mode(False)
        assert cb.is_enabled() is False
        cb.callback_mode(True)
        assert cb.is_enabled() is True

    def test_is_enabled_multiple_calls(self):
        """Test is_enabled() can be called multiple times"""
        cb = uvm_callback()

        # Multiple reads should always return same state
        for _ in range(5):
            assert cb.is_enabled() is True


class TestCallbackSubclassing:
    """Test subclassing uvm_callback"""

    def test_custom_callback_with_callback_method(self):
        """Test custom callback with additional methods"""
        cb = test_callback("my_cb")

        assert cb.get_name() == "my_cb"
        assert cb.is_enabled() is True
        assert cb.call_count == 0

    def test_custom_callback_method_invocation(self):
        """Test invoking custom callback method"""
        cb = test_callback()

        cb.on_event(1, 2, 3, key="value")

        assert cb.call_count == 1
        assert cb.last_args == (1, 2, 3)
        assert cb.last_kwargs == {"key": "value"}

    def test_custom_callback_multiple_invocations(self):
        """Test invoking callback method multiple times"""
        cb = test_callback()

        cb.on_event(1)
        cb.on_event(2)
        cb.on_event(3)

        assert cb.call_count == 3

    def test_callback_mode_independent_from_custom_state(self):
        """Test that callback_mode is independent from custom instance state"""
        cb = test_callback()

        # Invoke method
        cb.on_event()
        assert cb.call_count == 1

        # Disable callback
        cb.callback_mode(False)

        # Custom state should persist
        assert cb.call_count == 1
        assert cb.is_enabled() is False


class TestCallbackStateConsistency:
    """Test consistency between _enabled, callback_mode(), and is_enabled()"""

    def test_enabled_flag_consistency_initially(self):
        """Test that all methods return consistent state initially"""
        cb = uvm_callback()

        assert cb._enabled is True
        assert cb.callback_mode() is True
        assert cb.is_enabled() is True

    def test_enabled_flag_consistency_after_disable(self):
        """Test consistency after disabling"""
        cb = uvm_callback()
        cb.callback_mode(False)

        assert cb._enabled is False
        assert cb.callback_mode() is False
        assert cb.is_enabled() is False

    def test_enabled_flag_consistency_after_enable(self):
        """Test consistency after enabling"""
        cb = uvm_callback()
        cb.callback_mode(False)
        cb.callback_mode(True)

        assert cb._enabled is True
        assert cb.callback_mode() is True
        assert cb.is_enabled() is True


class TestCallbackInheritedBehavior:
    """Test inherited behavior from uvm_object"""

    def test_callback_has_get_name(self):
        """Test that callback has get_name from uvm_object"""
        cb = uvm_callback("my_callback")
        assert hasattr(cb, "get_name")
        assert cb.get_name() == "my_callback"

    def test_callback_has_set_name(self):
        """Test that callback has set_name from uvm_object"""
        cb = uvm_callback("original_name")
        cb.set_name("new_name")
        assert cb.get_name() == "new_name"

    def test_callback_object_hierarchy(self):
        """Test callback object hierarchy"""
        cb = test_callback("test")

        # Should be an instance of uvm_callback
        assert isinstance(cb, test_callback)
        assert isinstance(cb, uvm_callback)
        assert isinstance(cb, uvm_object)


class TestCallbackEdgeCases:
    """Test edge cases and corner cases"""

    def test_callback_with_empty_string_name(self):
        """Test creating callback with empty string name"""
        cb = uvm_callback("")
        assert cb.get_name() == ""

    def test_callback_with_special_characters_in_name(self):
        """Test callback with special characters in name"""
        special_names = [
            "callback_with_underscore",
            "callback-with-dash",
            "callback.with.dot",
            "callback@123",
            "callback#1_specialChar!",
        ]

        for name in special_names:
            cb = uvm_callback(name)
            assert cb.get_name() == name

    def test_multiple_callbacks_independent_state(self):
        """Test that multiple callbacks maintain independent state"""
        cb1 = uvm_callback("cb1")
        cb2 = uvm_callback("cb2")
        cb3 = uvm_callback("cb3")

        # Disable cb1 and cb3
        cb1.callback_mode(False)
        cb3.callback_mode(False)

        # Check states are independent
        assert cb1.is_enabled() is False
        assert cb2.is_enabled() is True
        assert cb3.is_enabled() is False

    def test_callback_mode_with_none_parameter(self):
        """Test callback_mode with None returns current state without change"""
        cb = uvm_callback()
        cb.callback_mode(False)

        result = cb.callback_mode(None)
        assert result is False
        assert cb.is_enabled() is False


class TestCallbackIntegration:
    """Integration tests with other components"""

    def test_callback_can_be_stored_in_collection(self):
        """Test that callbacks can be stored in collections"""
        callbacks = []

        for i in range(5):
            cb = uvm_callback(f"callback_{i}")
            callbacks.append(cb)

        assert len(callbacks) == 5

        # Verify all callbacks are independent
        for i, cb in enumerate(callbacks):
            assert cb.get_name() == f"callback_{i}"

    def test_callbacks_in_dictionary(self):
        """Test storing callbacks in dictionary"""
        cb_dict = {
            "enabled": uvm_callback("enabled_cb"),
            "disabled": uvm_callback("disabled_cb"),
        }

        cb_dict["disabled"].callback_mode(False)

        assert cb_dict["enabled"].is_enabled() is True
        assert cb_dict["disabled"].is_enabled() is False

    def test_callback_enabled_filtering(self):
        """Test filtering callbacks based on enabled state"""
        callbacks = [uvm_callback(f"cb_{i}") for i in range(10)]

        # Disable every other callback
        for i, cb in enumerate(callbacks):
            if i % 2 == 0:
                cb.callback_mode(False)

        enabled_cbs = [cb for cb in callbacks if cb.is_enabled()]
        disabled_cbs = [cb for cb in callbacks if not cb.is_enabled()]

        assert len(enabled_cbs) == 5
        assert len(disabled_cbs) == 5

    def test_custom_callback_inheritance_chain(self):
        """Test deep inheritance hierarchy"""

        class callback_level1(uvm_callback):
            pass

        class callback_level2(callback_level1):
            pass

        class callback_level3(callback_level2):
            pass

        cb = callback_level3("deep_callback")

        assert isinstance(cb, callback_level3)
        assert isinstance(cb, callback_level2)
        assert isinstance(cb, callback_level1)
        assert isinstance(cb, uvm_callback)
        assert isinstance(cb, uvm_object)
        assert cb.get_name() == "deep_callback"
        assert cb.is_enabled() is True


class TestCallbackDefaultBehavior:
    """Test default callback behavior and assumptions"""

    def test_callback_mode_default_parameter_behavior(self):
        """Test callback_mode with default (no) parameter"""
        cb = uvm_callback()

        # Call with no parameter should return current state
        state1 = cb.callback_mode()
        assert state1 is True

        # Should not change state
        state2 = cb.callback_mode()
        assert state2 is True

    def test_callback_creation_always_enabled(self):
        """Test that all callbacks start enabled"""
        for i in range(10):
            cb = uvm_callback(f"cb_{i}")
            assert cb.is_enabled() is True
            assert cb._enabled is True

    def test_callback_mode_as_getter_and_setter(self):
        """Test callback_mode as both getter and setter"""
        cb = uvm_callback()

        # Use as getter
        initial_state = cb.callback_mode()
        assert initial_state is True

        # Use as setter
        old_state = cb.callback_mode(False)
        assert old_state is initial_state

        # Use as getter again
        new_state = cb.callback_mode()
        assert new_state is False


class TestCallbackNameManagement:
    """Test callback name/identity management"""

    def test_callback_name_persistence(self):
        """Test that callback name persists through enable/disable"""
        cb = uvm_callback("persistent_name")

        assert cb.get_name() == "persistent_name"
        cb.callback_mode(False)
        assert cb.get_name() == "persistent_name"
        cb.callback_mode(True)
        assert cb.get_name() == "persistent_name"

    def test_callback_rename_after_creation(self):
        """Test renaming callback after creation"""
        cb = uvm_callback("original")
        assert cb.get_name() == "original"

        cb.set_name("renamed")
        assert cb.get_name() == "renamed"

    def test_callback_rename_does_not_affect_enabled_state(self):
        """Test that renaming doesn't affect enabled state"""
        cb = uvm_callback("original")
        cb.callback_mode(False)

        cb.set_name("renamed")

        assert cb.get_name() == "renamed"
        assert cb.is_enabled() is False


class TestCallbackTypeChecking:
    """Test type information and isinstance checks"""

    def test_callback_type_information(self):
        """Test type information is correct"""
        cb = uvm_callback("cb")

        assert type(cb).__name__ == "uvm_callback"
        assert uvm_callback in type(cb).__mro__

    def test_custom_callback_type_information(self):
        """Test custom callback type information"""
        cb = test_callback("cb")

        assert type(cb).__name__ == "test_callback"
        assert test_callback in type(cb).__mro__
        assert uvm_callback in type(cb).__mro__
