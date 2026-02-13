import pytest

from pyuvm import (
    uvm_callback,
    uvm_callback_iter,
    uvm_callbacks,
    uvm_object,
)
from pyuvm._s10_synchronization_classes import uvm_apprepend

pytestmark = pytest.mark.usefixtures("initialize_pyuvm")


class test_callback(uvm_callback):
    """Test callback class for testing uvm_callback_iter"""

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
    yield
    uvm_callbacks._callbacks.clear()


class TestCallbackIterInit:
    """Test uvm_callback_iter initialization"""

    def test_iter_with_empty_callbacks(self):
        """Test iterator initialization with no callbacks"""
        obj = test_object("empty_obj")
        iterator = uvm_callback_iter(obj)
        assert iterator._index == -1
        assert iterator._iter == []

    def test_iter_with_single_callback(self):
        """Test iterator initialization with single callback"""
        obj = test_object("single_obj")
        cb = test_callback("cb1")
        uvm_callbacks.add(obj, cb)

        iterator = uvm_callback_iter(obj)
        assert len(iterator._iter) == 1
        assert iterator._iter[0] is cb

    def test_iter_with_multiple_callbacks(self):
        """Test iterator initialization with multiple callbacks"""
        obj = test_object("multi_obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")
        cb3 = test_callback("cb3")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)
        uvm_callbacks.add(obj, cb3)

        iterator = uvm_callback_iter(obj)
        assert len(iterator._iter) == 3
        assert iterator._iter[0] is cb1
        assert iterator._iter[1] is cb2
        assert iterator._iter[2] is cb3

    def test_iter_filters_disabled_callbacks(self):
        """Test that iterator filters out disabled callbacks"""
        obj = test_object("filter_obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")
        cb3 = test_callback("cb3")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)
        uvm_callbacks.add(obj, cb3)

        # Disable cb2
        cb2.callback_mode(False)

        iterator = uvm_callback_iter(obj)
        assert len(iterator._iter) == 2
        assert iterator._iter[0] is cb1
        assert iterator._iter[1] is cb3


class TestCallbackIterFirst:
    """Test uvm_callback_iter.first() method"""

    def test_first_with_no_callbacks(self):
        """Test first() returns None when no callbacks"""
        obj = test_object("empty_obj")
        iterator = uvm_callback_iter(obj)
        assert iterator.first() is None

    def test_first_with_callbacks(self):
        """Test first() returns first callback and sets index"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)

        iterator = uvm_callback_iter(obj)
        first_cb = iterator.first()
        assert first_cb is cb1
        assert iterator._index == 0

    def test_first_resets_index(self):
        """Test first() resets index when called multiple times"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")
        cb3 = test_callback("cb3")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)
        uvm_callbacks.add(obj, cb3)

        iterator = uvm_callback_iter(obj)
        iterator.last()  # Move to last
        assert iterator._index == 2

        first_cb = iterator.first()  # Reset to first
        assert first_cb is cb1
        assert iterator._index == 0


class TestCallbackIterLast:
    """Test uvm_callback_iter.last() method"""

    def test_last_with_no_callbacks(self):
        """Test last() returns None when no callbacks"""
        obj = test_object("empty_obj")
        iterator = uvm_callback_iter(obj)
        assert iterator.last() is None

    def test_last_with_callbacks(self):
        """Test last() returns last callback and sets index"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")
        cb3 = test_callback("cb3")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)
        uvm_callbacks.add(obj, cb3)

        iterator = uvm_callback_iter(obj)
        last_cb = iterator.last()
        assert last_cb is cb3
        assert iterator._index == 2

    def test_last_resets_index(self):
        """Test last() resets index when called multiple times"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")
        cb3 = test_callback("cb3")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)
        uvm_callbacks.add(obj, cb3)

        iterator = uvm_callback_iter(obj)
        iterator.first()  # Move to first
        assert iterator._index == 0

        last_cb = iterator.last()  # Move to last
        assert last_cb is cb3
        assert iterator._index == 2


class TestCallbackIterNext:
    """Test uvm_callback_iter.next() method"""

    def test_next_with_no_callbacks(self):
        """Test next() returns None when no callbacks"""
        obj = test_object("empty_obj")
        iterator = uvm_callback_iter(obj)
        assert iterator.next() is None

    def test_next_on_single_callback(self):
        """Test next() on single callback"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        uvm_callbacks.add(obj, cb1)

        iterator = uvm_callback_iter(obj)
        # Index starts at -1, first next() should return first (and only) callback
        result = iterator.next()
        assert result is cb1
        assert iterator._index == 0

        # Next call should return None (out of bounds)
        result = iterator.next()
        assert result is None

    def test_next_sequence(self):
        """Test next() in sequence"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")
        cb3 = test_callback("cb3")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)
        uvm_callbacks.add(obj, cb3)

        iterator = uvm_callback_iter(obj)
        assert iterator.next() is cb1
        assert iterator.next() is cb2
        assert iterator.next() is cb3
        assert iterator.next() is None  # Past end


class TestCallbackIterPrev:
    """Test uvm_callback_iter.prev() method"""

    def test_prev_with_no_callbacks(self):
        """Test prev() returns None when no callbacks"""
        obj = test_object("empty_obj")
        iterator = uvm_callback_iter(obj)
        assert iterator.prev() is None

    def test_prev_from_last(self):
        """Test prev() from last position"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")
        cb3 = test_callback("cb3")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)
        uvm_callbacks.add(obj, cb3)

        iterator = uvm_callback_iter(obj)
        iterator.last()
        assert iterator._index == 2

        result = iterator.prev()
        # prev() decrements index from 2 to 1
        assert result is cb2
        assert iterator._index == 1

    def test_prev_at_beginning(self):
        """Test prev() returns None when at beginning"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        uvm_callbacks.add(obj, cb1)

        iterator = uvm_callback_iter(obj)
        iterator.first()
        assert iterator._index == 0

        result = iterator.prev()
        assert result is None


class TestCallbackIterGetCb:
    """Test uvm_callback_iter.get_cb() method"""

    def test_get_cb_with_no_callbacks(self):
        """Test get_cb() with no callbacks"""
        obj = test_object("empty_obj")
        iterator = uvm_callback_iter(obj)
        assert iterator.get_cb() is None

    def test_get_cb_at_index(self):
        """Test get_cb() returns callback at current index"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)

        iterator = uvm_callback_iter(obj)
        iterator.first()
        assert iterator.get_cb() is cb1

        iterator.last()
        assert iterator.get_cb() is cb2

    def test_get_cb_before_iteration(self):
        """Test get_cb() returns None before first item is accessed"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        uvm_callbacks.add(obj, cb1)

        iterator = uvm_callback_iter(obj)
        # Index is -1 initially (before first element)
        assert iterator.get_cb() is None


class TestCallbackIterIteration:
    """Test uvm_callback_iter as Python iterator"""

    def test_iterator_protocol_empty(self):
        """Test iterator protocol with no callbacks"""
        obj = test_object("empty_obj")
        iterator = uvm_callback_iter(obj)
        assert iter(iterator) is iterator
        with pytest.raises(StopIteration):
            next(iterator)

    def test_iterator_protocol_with_callbacks(self):
        """Test iterator protocol with callbacks"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)

        iterator = uvm_callback_iter(obj)
        assert iter(iterator) is iterator

        # Get callbacks via next()
        items = []
        try:
            while True:
                items.append(next(iterator))
        except StopIteration:
            pass

        assert len(items) == 2
        assert items[0] is cb1
        assert items[1] is cb2

    def test_for_loop_iteration(self):
        """Test iteration using for loop"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")
        cb3 = test_callback("cb3")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)
        uvm_callbacks.add(obj, cb3)

        iterator = uvm_callback_iter(obj)
        collected = []
        for cb in iterator:
            collected.append(cb)

        assert len(collected) == 3
        assert collected[0] is cb1
        assert collected[1] is cb2
        assert collected[2] is cb3


class TestCallbackIterAppend:
    """Test uvm_callback_iter with UVM_APPEND ordering"""

    def test_append_order_preserved(self):
        """Test that UVM_APPEND preserves callback order"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")
        cb3 = test_callback("cb3")

        uvm_callbacks.add(obj, cb1, uvm_apprepend.UVM_APPEND)
        uvm_callbacks.add(obj, cb2, uvm_apprepend.UVM_APPEND)
        uvm_callbacks.add(obj, cb3, uvm_apprepend.UVM_APPEND)

        iterator = uvm_callback_iter(obj)
        assert iterator._iter[0] is cb1
        assert iterator._iter[1] is cb2
        assert iterator._iter[2] is cb3


class TestCallbackIterPrepend:
    """Test uvm_callback_iter with UVM_PREPEND ordering"""

    def test_prepend_order_reversed(self):
        """Test that UVM_PREPEND reverses callback order"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")
        cb3 = test_callback("cb3")

        uvm_callbacks.add(obj, cb1, uvm_apprepend.UVM_APPEND)
        uvm_callbacks.add(obj, cb2, uvm_apprepend.UVM_PREPEND)
        uvm_callbacks.add(obj, cb3, uvm_apprepend.UVM_PREPEND)

        iterator = uvm_callback_iter(obj)
        # cb3 prepended last, so it should be first
        assert iterator._iter[0] is cb3
        assert iterator._iter[1] is cb2
        assert iterator._iter[2] is cb1


class TestCallbackIterWithType:
    """Test uvm_callback_iter with type instead of instance"""

    def test_iter_with_type(self):
        """Test iterator initialization with type"""
        # Register callbacks with a type
        cb1 = test_callback("cb1")
        uvm_callbacks.add(test_object, cb1)

        iterator = uvm_callback_iter(test_object)
        assert len(iterator._iter) == 1
        assert iterator._iter[0] is cb1

    def test_iter_type_separate_from_instance(self):
        """Test that type callbacks are separate from instance callbacks"""
        obj_instance = test_object("instance")
        cb1 = test_callback("cb1_type")
        cb2 = test_callback("cb2_instance")

        # Add callback to type
        uvm_callbacks.add(test_object, cb1)
        # Add callback to instance
        uvm_callbacks.add(obj_instance, cb2)

        iterator_type = uvm_callback_iter(test_object)
        iterator_instance = uvm_callback_iter(obj_instance)

        assert len(iterator_type._iter) == 1
        assert iterator_type._iter[0] is cb1

        assert len(iterator_instance._iter) == 1
        assert iterator_instance._iter[0] is cb2


class TestCallbackIterEdgeCases:
    """Test edge cases"""

    def test_re_enable_disabled_callback(self):
        """Test that re-enabling callbacks is not reflected in existing iterator"""
        obj = test_object("obj")
        cb = test_callback("cb")
        uvm_callbacks.add(obj, cb)

        # Create iterator while callback is enabled
        iterator1 = uvm_callback_iter(obj)
        assert len(iterator1._iter) == 1

        # Disable callback
        cb.callback_mode(False)

        # New iterator should not include disabled callback
        iterator2 = uvm_callback_iter(obj)
        assert len(iterator2._iter) == 0

        # Re-enable callback
        cb.callback_mode(True)

        # New iterator should include re-enabled callback
        iterator3 = uvm_callback_iter(obj)
        assert len(iterator3._iter) == 1

    def test_multiple_iterators_independent(self):
        """Test that multiple iterators can coexist independently"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)

        iter1 = uvm_callback_iter(obj)
        iter2 = uvm_callback_iter(obj)

        # Both should start at same state (-1)
        assert iter1._index == iter2._index == -1

        # Move first iterator
        iter1.last()

        # Second iterator should be unaffected
        assert iter1._index == 1
        assert iter2._index == -1

    def test_callback_enabled_state_inheritance(self):
        """Test callbacks inherit their enabled state at iteration time"""
        obj = test_object("obj")
        cb1 = test_callback("cb1")
        cb2 = test_callback("cb2")

        uvm_callbacks.add(obj, cb1)
        uvm_callbacks.add(obj, cb2)

        # Disable before iteration
        cb1.callback_mode(False)

        iterator = uvm_callback_iter(obj)
        assert len(iterator._iter) == 1
        assert iterator._iter[0] is cb2

        # The disabled callback is not in iterator
        assert cb1 not in iterator._iter
