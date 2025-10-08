from pyuvm import (
    uvm_object,
    uvm_sequence,
    uvm_sequence_base,
    uvm_sequencer_base,
)
from pyuvm.reg import uvm_mem
from pyuvm.reg.uvm_reg import uvm_reg
from pyuvm.reg.uvm_reg_item import uvm_reg_item
from pyuvm.reg.uvm_reg_map import uvm_reg_map
from pyuvm.reg.uvm_reg_model import (
    uvm_check_e,
    uvm_door_e,
    uvm_reg_addr_t,
    uvm_reg_data_t,
    uvm_status_e,
)

__all__ = ["uvm_reg_sequence", "uvm_reg_frontdoor"]


class uvm_reg_sequence(uvm_sequence):
    def __init__(self, name: str = "uvm_reg_sequence_inst"):
        super().__init__(name)
        raise NotImplementedError

    async def body(self):
        raise NotImplementedError

    async def do_reg_item(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def write_reg(self,
                        rg: uvm_reg,
                        value: uvm_reg_data_t,
                        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
                        map: uvm_reg_map = None,
                        prior: int = -1,
                        extension: uvm_object = None,
                        fname: str = "",
                        lineno: int = 0) -> uvm_status_e:
        raise NotImplementedError

    async def read_reg(
            self,
            rg: uvm_reg,
            path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
            map: uvm_reg_map = None,
            prior: int = -1,
            extension: uvm_object = None,
            fname: str = "",
            lineno: int = 0) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def poke_reg(self,
                       rg: uvm_reg,
                       value: uvm_reg_data_t,
                       kind: str = "",
                       extension: uvm_object = None,
                       fname: str = "",
                       lineno: int = 0) -> uvm_status_e:
        raise NotImplementedError

    async def peek_reg(
            self,
            rg: uvm_reg,
            kind: str = "",
            extension: uvm_object = None,
            fname: str = "",
            lineno: int = 0) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def update_reg(self,
                         rg: uvm_reg,
                         path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
                         map: uvm_reg_map = None,
                         prior: int = -1,
                         extension: uvm_object = None,
                         fname: str = "",
                         lineno: int = 0) -> uvm_status_e:
        raise NotImplementedError

    async def mirror_reg(self,
                         rg: uvm_reg,
                         check: uvm_check_e = uvm_check_e.UVM_NO_CHECK,
                         path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
                         map: uvm_reg_map = None,
                         prior: int = -1,
                         extension: uvm_object = None,
                         fname: str = "",
                         lineno: int = 0) -> uvm_status_e:
        raise NotImplementedError

    async def write_mem(self,
                        mem: uvm_mem,
                        offset: uvm_reg_addr_t,
                        value: uvm_reg_data_t,
                        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
                        map: uvm_reg_map = None,
                        prior: int = -1,
                        extension: uvm_object = None,
                        fname: str = "",
                        lineno: int = 0) -> uvm_status_e:
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
            lineno: int = 0) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def poke_mem(self,
                       mem: uvm_mem,
                       offset: uvm_reg_addr_t,
                       value: uvm_reg_data_t,
                       kind: str = "",
                       extension: uvm_object = None,
                       fname: str = "",
                       lineno: int = 0) -> uvm_status_e:
        raise NotImplementedError

    async def peek_mem(
            self,
            mem: uvm_mem,
            offset: uvm_reg_addr_t,
            kind: str = "",
            extension: uvm_object = None,
            fname: str = "",
            lineno: int = 0) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError


class uvm_reg_frontdoor(uvm_sequence):
    def __init__(self, name: str = ""):
        super().__init__(name)
        raise NotImplementedError

    async def atomic_lock(self):
        raise NotImplementedError

    def atomic_unlock(self):
        raise NotImplementedError

    async def start(self,
                    sequencer: uvm_sequencer_base,
                    parent_sequence: uvm_sequence_base = None,
                    this_priority: int = -1,
                    call_pre_psot: bool = True) -> None:
        raise NotImplementedError
