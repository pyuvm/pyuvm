from __future__ import annotations

import logging

try:
    from cocotb.triggers import Lock
except ModuleNotFoundError:
    from asyncio import Semaphore as Lock

from typing import TYPE_CHECKING

from pyuvm.reg.uvm_reg_model import (
    uvm_check_e,
    uvm_door_e,
)
from pyuvm.s14_15_python_sequences import uvm_sequence

if TYPE_CHECKING:
    from pyuvm.reg import uvm_mem
    from pyuvm.reg.uvm_reg import uvm_reg
    from pyuvm.reg.uvm_reg_item import uvm_reg_item
    from pyuvm.reg.uvm_reg_map import uvm_reg_map
    from pyuvm.reg.uvm_reg_model import (
        uvm_reg_addr_t,
        uvm_reg_data_t,
        uvm_status_e,
    )
    from pyuvm.s05_base_classes import uvm_object
    from pyuvm.s14_15_python_sequences import (
        uvm_sequence_base,
        uvm_sequencer_base,
    )

__all__ = ["uvm_reg_sequence", "uvm_reg_frontdoor"]
logger = logging.getLogger("RegModel")


class uvm_reg_sequence(uvm_sequence):
    def __init__(self, name: str = "uvm_reg_sequence_inst"):
        super().__init__(name)
        raise NotImplementedError

    async def body(self):
        raise NotImplementedError

    async def do_reg_item(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def write_reg(
        self,
        rg: uvm_reg,
        value: uvm_reg_data_t,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def read_reg(
        self,
        rg: uvm_reg,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def poke_reg(
        self,
        rg: uvm_reg,
        value: uvm_reg_data_t,
        kind: str = "",
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def peek_reg(
        self,
        rg: uvm_reg,
        kind: str = "",
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def update_reg(
        self,
        rg: uvm_reg,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def mirror_reg(
        self,
        rg: uvm_reg,
        check: uvm_check_e = uvm_check_e.UVM_NO_CHECK,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def write_mem(
        self,
        mem: uvm_mem,
        offset: uvm_reg_addr_t,
        value: uvm_reg_data_t,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def read_mem(
        self,
        mem: uvm_mem,
        offset: uvm_reg_addr_t,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def poke_mem(
        self,
        mem: uvm_mem,
        offset: uvm_reg_addr_t,
        value: uvm_reg_data_t,
        kind: str = "",
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def peek_mem(
        self,
        mem: uvm_mem,
        offset: uvm_reg_addr_t,
        kind: str = "",
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError


class uvm_reg_frontdoor(uvm_reg_sequence):
    def __init__(self, name: str = ""):
        super().__init__(name)
        self.rw_info = None
        self._atomic = Lock()

    async def atomic_lock(self):
        await self._atomic.acquire()

    def atomic_unlock(self):
        if not self._atomic.locked():
            logger.warning(
                f"Attempt to unlock frontdoor "
                f"{repr(self.get_full_name())} when it wasn't locked!"
            )
        self._atomic.release()

    async def start(
        self,
        sequencer: uvm_sequencer_base,
        parent_sequence: uvm_sequence_base = None,
        this_priority: int = -1,
        call_pre_post: bool = True,
    ) -> None:
        # TODO: implement guard check. See official UVM implementation
        super().start(sequencer, parent_sequence, this_priority, call_pre_post)
