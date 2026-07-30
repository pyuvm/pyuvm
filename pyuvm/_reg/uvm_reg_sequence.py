from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cocotb.triggers import Lock

from pyuvm._error_classes import UVMSequenceError
from pyuvm._reg.uvm_mem import uvm_mem
from pyuvm._reg.uvm_reg import uvm_reg
from pyuvm._reg.uvm_reg_item import uvm_reg_item
from pyuvm._reg.uvm_reg_model import (
    uvm_access_e,
    uvm_check_e,
    uvm_door_e,
    uvm_status_e,
)
from pyuvm._reg.uvm_reg_reporting import uvm_reg_report_error as _report_error
from pyuvm._s14_15_python_sequences import uvm_sequence
from pyuvm._utility_classes import current_task

if TYPE_CHECKING:
    from pyuvm._reg.uvm_reg_map import uvm_reg_map
    from pyuvm._reg.uvm_reg_model import (
        uvm_reg_addr_t,
        uvm_reg_data_t,
    )
    from pyuvm._s05_base_classes import uvm_object
    from pyuvm._s14_15_python_sequences import uvm_sequencer_base

__all__ = ["uvm_reg_sequence", "uvm_reg_frontdoor"]
logger = logging.getLogger("RegModel")


class uvm_reg_sequence(uvm_sequence):
    def __init__(self, name: str = "uvm_reg_sequence_inst"):
        super().__init__(name)
        self.model = None
        self.adapter = None
        self.reg_seqr = None

    async def body(self):
        if self.reg_seqr is None:
            _report_error(
                self,
                "REG_SEQUENCE",
                f"Translation sequence {self.get_full_name()!r} has no "
                "upstream register sequencer configured",
            )
            return

        while True:
            rw = await self.reg_seqr.get_next_item()
            original_parent = getattr(rw, "parent", None)
            try:
                if not isinstance(rw, uvm_reg_item):
                    raise UVMSequenceError(
                        "Register translation sequence received an item that is "
                        "not a uvm_reg_item"
                    )
                rw.set_parent_sequence(self)
                await self.do_reg_item(rw)
            finally:
                if isinstance(rw, uvm_reg_item):
                    rw.set_parent_sequence(original_parent)
                self.reg_seqr.item_done()

    async def do_reg_item(self, rw: uvm_reg_item) -> None:
        if not isinstance(rw, uvm_reg_item):
            raise UVMSequenceError("do_reg_item() requires a uvm_reg_item")
        if self.sequencer is None:
            raise UVMSequenceError(
                "Register translation sequence has no downstream sequencer"
            )
        if self.adapter is None:
            raise UVMSequenceError("Register translation sequence has no adapter")
        local_map = rw.get_local_map()
        if local_map is None:
            raise UVMSequenceError(
                "Register translation item has no selected local map"
            )
        if rw.get_kind() == uvm_access_e.UVM_WRITE:
            await local_map.do_bus_write(rw, self.sequencer, self.adapter)
        elif rw.get_kind() == uvm_access_e.UVM_READ:
            await local_map.do_bus_read(rw, self.sequencer, self.adapter)
        else:
            raise UVMSequenceError(
                f"Unsupported register translation access kind: {rw.get_kind()!r}"
            )

    def _valid_target(self, target, expected_type: type, kind: str) -> bool:
        if isinstance(target, expected_type):
            return True
        _report_error(
            self,
            "REG_SEQUENCE",
            f"{kind} convenience helper requires a valid {expected_type.__name__}",
        )
        return False

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
        if not self._valid_target(rg, uvm_reg, "Register"):
            return uvm_status_e.UVM_NOT_OK
        return await rg.write(value, path, map, self, prior, extension, fname, lineno)

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
        if not self._valid_target(rg, uvm_reg, "Register"):
            return uvm_status_e.UVM_NOT_OK, 0
        return await rg.read(path, map, self, prior, extension, fname, lineno)

    async def poke_reg(
        self,
        rg: uvm_reg,
        value: uvm_reg_data_t,
        kind: str = "",
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError(
            "poke_reg() requires register backdoor support, which is deferred "
            "to the backdoor milestone"
        )

    async def peek_reg(
        self,
        rg: uvm_reg,
        kind: str = "",
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError(
            "peek_reg() requires register backdoor support, which is deferred "
            "to the backdoor milestone"
        )

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
        if not self._valid_target(rg, uvm_reg, "Register"):
            return uvm_status_e.UVM_NOT_OK
        return await rg.update(path, map, self, prior, extension, fname, lineno)

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
        if not self._valid_target(rg, uvm_reg, "Register"):
            return uvm_status_e.UVM_NOT_OK
        return await rg.mirror(check, path, map, self, prior, extension, fname, lineno)

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
        if not self._valid_target(mem, uvm_mem, "Memory"):
            return uvm_status_e.UVM_NOT_OK
        return await mem.write(
            offset, value, path, map, self, prior, extension, fname, lineno
        )

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
        if not self._valid_target(mem, uvm_mem, "Memory"):
            return uvm_status_e.UVM_NOT_OK, 0
        return await mem.read(offset, path, map, self, prior, extension, fname, lineno)

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
        raise NotImplementedError(
            "poke_mem() requires memory backdoor support, which is deferred "
            "to the backdoor milestone"
        )

    async def peek_mem(
        self,
        mem: uvm_mem,
        offset: uvm_reg_addr_t,
        kind: str = "",
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError(
            "peek_mem() requires memory backdoor support, which is deferred "
            "to the backdoor milestone"
        )


class uvm_reg_frontdoor(uvm_reg_sequence):
    def __init__(self, name: str = ""):
        super().__init__(name)
        self.rw_info = None
        self._atomic = Lock()
        self._atomic_owner = None

    @staticmethod
    def _current_task():
        return current_task()

    async def body(self):
        raise UVMSequenceError(
            "uvm_reg_frontdoor.body() must be overridden by a derived frontdoor"
        )

    async def atomic_lock(self):
        owner = self._current_task()
        if self._atomic_owner is owner and owner is not None:
            return
        await self._atomic.acquire()
        self._atomic_owner = owner

    def atomic_unlock(self):
        owner = self._current_task()
        try:
            locked = self._atomic.locked()
        except TypeError:
            # INFO: For backward compatibility with Cocotb <= 1.8
            locked = self._atomic.locked
        if not locked or self._atomic_owner is not owner:
            logger.warning(
                f"Attempt to unlock frontdoor "
                f"{repr(self.get_full_name())} by a task that does not own it"
            )
            return
        self._atomic_owner = None
        self._atomic.release()

    async def start(
        self,
        seqr: uvm_sequencer_base = None,
        call_pre_post: bool = True,
    ) -> None:
        owner = self._current_task()
        acquired_here = self._atomic_owner is not owner or owner is None
        if acquired_here:
            await self.atomic_lock()
        try:
            await super().start(seqr, call_pre_post)
        finally:
            if acquired_here:
                self.atomic_unlock()
