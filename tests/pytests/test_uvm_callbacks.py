import pytest

from pyuvm import (
    uvm_callback,
    uvm_callbacks,
    uvm_object,
    uvm_root,
)
from pyuvm._s10_synchronization_classes import uvm_apprepend

pytestmark = pytest.mark.usefixtures("initialize_pyuvm")


class test_callback(uvm_callback):
    """Test callback class"""

    def __init__(self, name: str = "test_callback"):
        super().__init__(name)
        self.called = False
        self.call_count = 0

    def callback_method(self):
        self.called = True
        self.call_count += 1


class test_object(uvm_object):
    """Test object for attaching callbacks"""

    def __init__(self, name: str = "test_object"):
        super().__init__(name)


@pytest.fixture(autouse=True)
def cleanup_callbacks():
    """Clean up callbacks before and after each test"""
    uvm_callbacks._callbacks.clear()
    uvm_callbacks._instance = None
    yield
    uvm_callbacks._callbacks.clear()
    uvm_callbacks._instance = None


class TestCallbacksSingleton:
    """Test uvm_callbacks singleton pattern"""

    def test_get_returns_singleton(self):
        """Test that get() returns same instance"""
        instance1 = uvm_callbacks.get()
        instance2 = uvm_callbacks.get()
        assert instance1 is instance2

    def test_multiple_creations_return_same_instance(self):
        """Test that multiple creations return same instance"""
        cb1 = uvm_callbacks()
        cb2 = uvm_callbacks()
        assert cb1 is cb2


class TestCallbacksAdd:
    """Test uvm_callbacks.add() method"""

    def test_add_single_callback(self):
        """Test adding a single callback"""
        obj = test_object("obj")
        cb = test_callback("cb")

        uvm_callbacks.add(obj, cb)
        assert obj in uvm_callbacks._callbacks
        assert cb in uvm_callbacks._callbacks[obj]

    def test_add_multiple_callbacks_to_same_object(self):
        """Test adding multiple callbacks to same object"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")
        cb3 = test_callback("cb3")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)
        uvm_callbacks.add(obj, cb3)

        assert len(uvm_callbacks._callbacks[obj]) == 3
        assert cb1 in uvm_callbacks._callbacks[obj]
        assert cb2 in uvm_callbacks._callbacks[obj]
        assert cb3 in uvm_callbacks._callbacks[obj]

    def test_add_same_callback_not_duplicated(self):
        """Test that same callback is not added twice"""
        obj = test_object("obj")
        cb = test_callback("cb")

        uvm_callbacks.add(obj, cb)
        uvm_callbacks.add(obj, cb)

        assert len(uvm_callbacks._callbacks[obj]) == 1
        assert uvm_callbacks._callbacks[obj][0] is cb

    def test_add_with_append_ordering(self):
        """Test UVM_APPEND ordering appends to end"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")
        cb3 = test_callback("cb3")

        uvm_callbacks.add(obj, cb1, uvm_apprepend.UVM_APPEND)
        uvm_callbacks.add(obj, cb2, uvm_apprepend.UVM_APPEND)
        uvm_callbacks.add(obj, cb3, uvm_apprepend.UVM_APPEND)

        cbs = uvm_callbacks._callbacks[obj]
        assert cbs[0] is cb1
        assert cbs[1] is cb2
        assert cbs[2] is cb3

    def test_add_with_prepend_ordering(self):
        """Test UVM_PREPEND ordering prepends to beginning"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")
        cb3 = test_callback("cb3")

        uvm_callbacks.add(obj, cb1, uvm_apprepend.UVM_APPEND)
        uvm_callbacks.add(obj, cb2, uvm_apprepend.UVM_PREPEND)
        uvm_callbacks.add(obj, cb3, uvm_apprepend.UVM_PREPEND)

        cbs = uvm_callbacks._callbacks[obj]
        # cb3 prepended last, so it's first
        assert cbs[0] is cb3
        assert cbs[1] is cb2
        assert cbs[2] is cb1

    def test_add_callbacks_to_different_objects(self):
        """Test adding callbacks to different objects"""
        obj1 = test_object("obj1")
        obj2 = test_object("obj2")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")

        uvm_callbacks.add(obj1, cb1)
        uvm_callbacks.add(obj2, cb2)

        assert cb1 in uvm_callbacks._callbacks[obj1]
        assert cb2 in uvm_callbacks._callbacks[obj2]
        assert cb2 not in uvm_callbacks._callbacks[obj1]
        assert cb1 not in uvm_callbacks._callbacks[obj2]

    def test_add_callbacks_to_type(self):
        """Test adding callbacks to a type instead of instance"""
        cb = test_callback("cb")
        uvm_callbacks.add(test_object, cb)

        assert test_object in uvm_callbacks._callbacks
        assert cb in uvm_callbacks._callbacks[test_object]


class TestCallbacksDelete:
    """Test uvm_callbacks.delete() method"""

    def test_delete_single_callback(self):
        """Test deleting a callback"""
        obj = test_object("obj")
        cb = test_callback("cb")

        uvm_callbacks.add(obj, cb)
        assert cb in uvm_callbacks._callbacks[obj]

        uvm_callbacks.delete(obj, cb)
        assert cb not in uvm_callbacks._callbacks[obj]

    def test_delete_one_of_multiple_callbacks(self):
        """Test deleting one callback leaves others"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")
        cb3 = test_callback("cb3")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)
        uvm_callbacks.add(obj, cb3)

        uvm_callbacks.delete(obj, cb2)

        cbs = uvm_callbacks._callbacks[obj]
        assert len(cbs) == 2
        assert cb1 in cbs
        assert cb2 not in cbs
        assert cb3 in cbs

    def test_delete_non_existent_callback(self):
        """Test deleting non-existent callback does nothing"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")

        uvm_callbacks.add(obj, cb1)
        # Try to delete cb2 which doesn't exist
        uvm_callbacks.delete(obj, cb2)

        # cb1 should still be there
        assert cb1 in uvm_callbacks._callbacks[obj]

    def test_delete_from_object_with_no_callbacks(self):
        """Test deleting from object with no callbacks"""
        obj = test_object("obj")
        cb = test_callback("cb")

        # Try to delete from obj that has no callbacks registered
        uvm_callbacks.delete(obj, cb)

        # Should not raise error, object key might not exist
        assert (
            obj not in uvm_callbacks._callbacks
            or len(uvm_callbacks._callbacks[obj]) == 0
        )

    def test_delete_all_callbacks_for_object(self):
        """Test deleting all callbacks for an object"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)

        uvm_callbacks.delete(obj, cb1)
        uvm_callbacks.delete(obj, cb2)

        assert len(uvm_callbacks._callbacks[obj]) == 0


class TestCallbacksAddByName:
    """Test uvm_callbacks.add_by_name() method"""

    def test_add_by_name_to_single_component(self):
        """Test adding callback to component by name"""
        # Note: find_all() is not implemented, so this test verifies the method exists
        # and can be called, even though it will raise NotImplementedError
        root = uvm_root()
        cb = test_callback("cb")

        with pytest.raises(NotImplementedError):
            uvm_callbacks.add_by_name("my_comp", cb, root)

    def test_add_by_name_with_multiple_matches(self):
        """Test adding callback to multiple components with same name structure"""
        # find_all() is not implemented, so verify it raises NotImplementedError
        root = uvm_root()
        cb = test_callback("cb")

        with pytest.raises(NotImplementedError):
            uvm_callbacks.add_by_name("work", cb, root)

    def test_add_by_name_preserves_ordering(self):
        """Test that add_by_name respects ordering parameter"""
        # find_all() is not implemented, so verify it raises NotImplementedError
        root = uvm_root()
        cb1 = test_callback("cb1")

        with pytest.raises(NotImplementedError):
            uvm_callbacks.add_by_name("test_comp", cb1, root, uvm_apprepend.UVM_APPEND)


class TestCallbacksDeleteByName:
    """Test uvm_callbacks.delete_by_name() method"""

    def test_delete_by_name(self):
        """Test deleting callback from component by name"""
        # find_all() is not implemented, so verify it raises NotImplementedError
        root = uvm_root()
        cb = test_callback("cb")

        with pytest.raises(NotImplementedError):
            uvm_callbacks.delete_by_name("my_comp", cb, root)

    def test_delete_by_name_multiple_callbacks(self):
        """Test deleting one callback leaves others when using delete_by_name"""
        # find_all() is not implemented, so verify it raises NotImplementedError
        root = uvm_root()
        cb = test_callback("cb")

        with pytest.raises(NotImplementedError):
            uvm_callbacks.delete_by_name("test_comp", cb, root)


class TestCallbacksNotImplemented:
    """Test methods that raise NotImplementedError"""

    def test_get_first_not_implemented(self):
        """Test that get_first raises NotImplementedError"""
        obj = test_object("obj")
        with pytest.raises(NotImplementedError, match="Use uvm_callback_iter"):
            uvm_callbacks.get_first(0, obj)

    def test_get_last_not_implemented(self):
        """Test that get_last raises NotImplementedError"""
        obj = test_object("obj")
        with pytest.raises(NotImplementedError, match="Use uvm_callback_iter"):
            uvm_callbacks.get_last(0, obj)

    def test_get_next_not_implemented(self):
        """Test that get_next raises NotImplementedError"""
        obj = test_object("obj")
        with pytest.raises(NotImplementedError, match="Use uvm_callback_iter"):
            uvm_callbacks.get_next(0, obj)

    def test_get_prev_not_implemented(self):
        """Test that get_prev raises NotImplementedError"""
        obj = test_object("obj")
        with pytest.raises(NotImplementedError, match="Use uvm_callback_iter"):
            uvm_callbacks.get_prev(0, obj)

    def test_get_all_not_implemented(self):
        """Test that get_all raises NotImplementedError"""
        obj = test_object("obj")
        with pytest.raises(NotImplementedError, match="Use uvm_callback_iter"):
            uvm_callbacks.get_all(obj)


class TestCallbacksStateManagement:
    """Test state management and persistence"""

    def test_callbacks_persist_across_multiple_adds(self):
        """Test that callbacks persist across multiple add operations"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")

        uvm_callbacks.add(obj, cb1)
        assert cb1 in uvm_callbacks._callbacks[obj]

        uvm_callbacks.add(obj, cb2)
        assert cb1 in uvm_callbacks._callbacks[obj]
        assert cb2 in uvm_callbacks._callbacks[obj]

    def test_callbacks_independent_across_objects(self):
        """Test that callbacks for different objects are independent"""
        obj1 = test_object("obj1")
        obj2 = test_object("obj2")
        cb = test_callback("cb")

        uvm_callbacks.add(obj1, cb)
        uvm_callbacks.delete(obj2, cb)  # Delete from obj2 (shouldn't affect obj1)

        assert cb in uvm_callbacks._callbacks[obj1]

    def test_large_number_of_callbacks(self):
        """Test handling multiple callbacks on same object"""
        obj = test_object("obj")
        callbacks = [test_callback(f"cb{i}") for i in range(100)]

        for cb in callbacks:
            uvm_callbacks.add(obj, cb)

        assert len(uvm_callbacks._callbacks[obj]) == 100
        for cb in callbacks:
            assert cb in uvm_callbacks._callbacks[obj]


class TestCallbacksIntegration:
    """Integration tests with other UVM components"""

    def test_add_multiple_callback_types(self):
        """Test adding different callback types to same object"""
        obj = test_object("obj")

        class callback_type1(uvm_callback):
            pass

        class callback_type2(uvm_callback):
            pass

        cb1 = callback_type1("cb1")
        cb2 = callback_type2("cb2")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)

        assert cb1 in uvm_callbacks._callbacks[obj]
        assert cb2 in uvm_callbacks._callbacks[obj]

    def test_mixed_append_prepend_sequence(self):
        """Test complex sequence of append and prepend operations"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")
        cb3 = test_callback("cb3")
        cb4 = test_callback("cb4")
        cb5 = test_callback("cb5")

        uvm_callbacks.add(obj, cb1, uvm_apprepend.UVM_APPEND)
        uvm_callbacks.add(obj, cb2, uvm_apprepend.UVM_APPEND)
        uvm_callbacks.add(obj, cb3, uvm_apprepend.UVM_PREPEND)
        uvm_callbacks.add(obj, cb4, uvm_apprepend.UVM_PREPEND)
        uvm_callbacks.add(obj, cb5, uvm_apprepend.UVM_APPEND)

        cbs = uvm_callbacks._callbacks[obj]
        # Expected order: cb4, cb3, cb1, cb2, cb5
        assert cbs[0] is cb4
        assert cbs[1] is cb3
        assert cbs[2] is cb1
        assert cbs[3] is cb2
        assert cbs[4] is cb5

    def test_callback_registration_across_types_and_instances(self):
        """Test registering callbacks for both type and instance of same class"""
        obj_instance = test_object("instance")
        cb_type = test_callback("cb_type")
        cb_instance = test_callback("cb_instance")

        # Add to type
        uvm_callbacks.add(test_object, cb_type)
        # Add to instance
        uvm_callbacks.add(obj_instance, cb_instance)

        # Type and instance should have separate registrations
        assert cb_type in uvm_callbacks._callbacks[test_object]
        assert cb_instance in uvm_callbacks._callbacks[obj_instance]
        assert cb_instance not in uvm_callbacks._callbacks[test_object]
        assert cb_type not in uvm_callbacks._callbacks[obj_instance]
