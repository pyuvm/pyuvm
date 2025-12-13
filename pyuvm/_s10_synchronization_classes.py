from __future__ import annotations

from pyuvm._s05_base_classes import uvm_object

__all__ = ["uvm_callback", "uvm_callbacks", "uvm_callback_iter"]


class uvm_callback(uvm_object):
    def __init__(self, name: str = "uvm_callback") -> None:
        super().__init__(name)
        raise NotImplementedError


class uvm_callbacks(uvm_object):
    def __init__(self, name: str = "uvm_callbacks") -> None:
        super().__init__(name)
        raise NotImplementedError


class uvm_callback_iter:
    def __init__(self, obj):
        raise NotImplementedError
