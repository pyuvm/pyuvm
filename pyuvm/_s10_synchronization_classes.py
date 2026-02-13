from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from pyuvm._s05_base_classes import uvm_object
from pyuvm._s13_uvm_component import uvm_root

if TYPE_CHECKING:
    from pyuvm._s13_predefined_component_classes import uvm_component

__all__ = [
    "uvm_apprepend",
    "uvm_callback",
    "uvm_callbacks",
    "uvm_callback_iter",
    "uvm_do_callbacks",
]


class uvm_apprepend(Enum):
    UVM_APPEND = auto()
    UVM_PREPEND = auto()


class uvm_callback(uvm_object):
    def __init__(self, name: str = "uvm_callback") -> None:
        super().__init__(name)
        self._enabled: bool = True

    def callback_mode(self, on: bool | None = None):
        enabled = self._enabled
        if on is not None:
            self._enabled = on
        return enabled

    def is_enabled(self) -> bool:
        return self._enabled


class uvm_callbacks(uvm_object):
    _instance = None
    _callbacks: dict[uvm_object | type, list[uvm_callback]] = {}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            # Create the instance only if it doesn't exist
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, name: str = "uvm_callbacks"):
        if not hasattr(self, "_initialized"):
            self._initialized = True

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def add(cls, obj, cb, ordering: uvm_apprepend = uvm_apprepend.UVM_APPEND):
        if obj in cls._callbacks and cb not in cls._callbacks[obj]:
            if ordering == uvm_apprepend.UVM_APPEND:
                cls._callbacks[obj].append(cb)
            else:
                cls._callbacks[obj].insert(0, cb)
        else:
            cls._callbacks[obj] = [cb]

    @classmethod
    def add_by_name(
        cls,
        name: str,
        cb: uvm_callback,
        root: uvm_component,
        ordering: uvm_apprepend = uvm_apprepend.UVM_APPEND,
    ) -> None:
        top = uvm_root()
        objs = top.find_all(name, root)
        for obj in objs:
            cls.add(obj, cb, ordering)

    @classmethod
    def delete(cls, obj, cb: uvm_callback) -> None:
        if obj in cls._callbacks:
            cb_list = cls._callbacks[obj].copy()
            cls._callbacks[obj] = [i for i in cb_list if i is not cb]

    @classmethod
    def delete_by_name(cls, name: str, cb: uvm_callback, root: uvm_component):
        top = uvm_root()
        objs = top.find_all(name, root)
        for obj in objs:
            cls.delete(obj, cb)

    @classmethod
    def get_first(cls, itr: int, obj: uvm_object) -> uvm_callback | None:
        raise NotImplementedError("Use uvm_callback_iter")

    @classmethod
    def get_last(cls, itr: int, obj: uvm_object) -> uvm_callback | None:
        raise NotImplementedError("Use uvm_callback_iter")

    @classmethod
    def get_next(cls, itr: int, obj: uvm_object) -> uvm_callback | None:
        raise NotImplementedError("Use uvm_callback_iter")

    @classmethod
    def get_prev(cls, itr: int, obj: uvm_object) -> uvm_callback | None:
        raise NotImplementedError("Use uvm_callback_iter")

    @classmethod
    def get_all(cls, obj: uvm_object) -> list[uvm_callback]:
        raise NotImplementedError("Use uvm_callback_iter")


class uvm_callback_iter:
    def __init__(self, obj: type[uvm_object] | uvm_object):
        self._index = -1
        self._iter: list[uvm_callback] = [
            c for c in uvm_callbacks._callbacks.get(obj, list()) if c.callback_mode()
        ]

    def __iter__(self):
        return self

    def __next__(self) -> uvm_callback:
        self._index += 1
        if self._index < len(self._iter):
            return self._iter[self._index]
        else:
            raise StopIteration

    def next(self) -> uvm_callback | None:
        self._index += 1
        if self._index < len(self._iter):
            return self._iter[self._index]
        else:
            return None

    def prev(self) -> uvm_callback | None:
        if self._index > 0:
            self._index -= 1
            return self._iter[self._index]
        else:
            return None

    def first(self) -> uvm_callback | None:
        if len(self._iter) > 0:
            self._index = 0
            return self._iter[self._index]
        else:
            return None

    def last(self) -> uvm_callback | None:
        if len(self._iter) > 0:
            self._index = len(self._iter) - 1
            return self._iter[self._index]
        else:
            return None

    def get_cb(self) -> uvm_callback | None:
        if 0 <= self._index < len(self._iter):
            return self._iter[self._index]
        else:
            return None


def uvm_do_callbacks(
    T: type[uvm_object] | uvm_object,
    cb: type[uvm_callback],
    method: str,
    *args,
    **kwargs,
) -> None:
    callbacks = uvm_callback_iter(T)
    for callback in callbacks:
        func = getattr(callback, method)
        func(*args, **kwargs)
