from __future__ import annotations

from typing import TYPE_CHECKING

from pyuvm import uvm_object

if TYPE_CHECKING:
    from pyuvm.reg.uvm_reg_field import uvm_reg_field
    from pyuvm.reg.uvm_reg_item import uvm_reg_item

__all__ = ["uvm_reg_backdoor"]


class uvm_reg_backdoor(uvm_object):
    def __init__(self, name: str = ""):
        super().__init__()
        raise NotImplementedError

    async def do_pre_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def do_post_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def do_pre_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def do_post_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    def read_func(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    def is_auto_updated(self, field: uvm_reg_field) -> bool:
        raise NotImplementedError

    async def wait_for_change(element: uvm_object) -> None:
        raise NotImplementedError

    async def pre_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def post_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def pre_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def post_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError
