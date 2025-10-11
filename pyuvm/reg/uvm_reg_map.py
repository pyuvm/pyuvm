from __future__ import annotations

from typing import TYPE_CHECKING

from pyuvm import uvm_object, uvm_sequence_base
from pyuvm.reg.uvm_reg_model import (
    uvm_hier_e,
)

if TYPE_CHECKING:
    from pyuvm import (
        uvm_sequencer,
        uvm_sequencer_base,
    )
    from pyuvm.reg.uvm_mem import uvm_mem
    from pyuvm.reg.uvm_reg import uvm_reg
    from pyuvm.reg.uvm_reg_adapter import uvm_reg_adapter
    from pyuvm.reg.uvm_reg_backdoor import uvm_reg_backdoor
    from pyuvm.reg.uvm_reg_block import uvm_reg_block
    from pyuvm.reg.uvm_reg_field import uvm_reg_field
    from pyuvm.reg.uvm_reg_item import uvm_reg_bus_op, uvm_reg_item
    from pyuvm.reg.uvm_reg_model import (
        uvm_endianness_e,
        uvm_hier_e,
        uvm_reg_addr_t,
        uvm_reg_map_addr_range,
    )
    from pyuvm.reg.uvm_reg_sequence import uvm_reg_frontdoor
    from pyuvm.reg.uvm_vreg import uvm_vreg
    from pyuvm.reg.uvm_vreg_field import uvm_vreg_field

__all__ = [
    "uvm_reg_map_info",
    "uvm_reg_transaction_order_policy",
    "uvm_reg_seq_base",
    "uvm_reg_map"
]


class uvm_reg_map_info:
    offset: uvm_reg_addr_t
    rights: str
    unmapped: bool
    addr: list[uvm_reg_addr_t]
    frontdoor: uvm_reg_frontdoor
    mem_range: uvm_reg_map_addr_range
    is_initialized: bool


class uvm_reg_transaction_order_policy(uvm_object):
    def __init__(self, name: str = "policy"):
        super().__init__(name)
        raise NotImplementedError

    def order(self, q: list[uvm_reg_bus_op]) -> None:
        raise NotImplementedError


class uvm_reg_seq_base(uvm_sequence_base):
    def __init__(self, name: str = "uvm_reg_seq_base"):
        super().__init__(name)


class uvm_reg_map(uvm_object):
    def __init__(self, name: str = "uvm_reg_map"):
        super().__init__(name)
        raise NotImplementedError

    def _init_addr_map(self) -> None:
        raise NotImplementedError

    @staticmethod
    def backdoor() -> uvm_reg_backdoor:
        raise NotImplementedError

    def configure(self,
                  parent: uvm_reg_block,
                  base_addr: uvm_reg_addr_t,
                  n_bytes: int,
                  endian: uvm_endianness_e,
                  byte_addressing: bool = True) -> None:
        raise NotImplementedError

    def add_reg(self,
                rg: uvm_reg,
                offset: uvm_reg_addr_t,
                rights: str = "RW",
                unmapped: bool = False,
                frondoor: uvm_reg_frontdoor = None) -> None:
        raise NotImplementedError

    def add_mem(self,
                mem: uvm_mem,
                offset: uvm_reg_addr_t,
                rights: str = "RW",
                unmapped: bool = False,
                frontdoor: uvm_reg_frontdoor = None):
        raise NotImplementedError

    def add_submap(self,
                   child_map: uvm_reg_map,
                   offset: uvm_reg_addr_t) -> None:
        raise NotImplementedError

    def set_sequencer(self,
                      sequencer: uvm_sequencer,
                      adapter: uvm_reg_adapter = None) -> None:
        raise NotImplementedError

    def set_submap_offset(self,
                          submap: uvm_reg_map,
                          offset: uvm_reg_addr_t) -> None:
        raise NotImplementedError

    def get_submap_offset(self, submap: uvm_reg_map) -> uvm_reg_addr_t:
        raise NotImplementedError

    def set_base_addr(self, offset: uvm_reg_addr_t) -> None:
        raise NotImplementedError

    def reset(self, kind: str = "SOFT") -> None:
        raise NotImplementedError

    def _add_parent_map(self,
                        parent_map: uvm_reg_map,
                        offset: uvm_reg_addr_t) -> None:
        raise NotImplementedError

    def _verify_map_config(self) -> None:
        raise NotImplementedError

    def _set_reg_offset(self,
                        reg: uvm_reg,
                        offset: uvm_reg_addr_t,
                        unmapped: bool) -> None:
        raise NotImplementedError

    def _set_mem_offset(self,
                        mem: uvm_mem,
                        offset: uvm_reg_addr_t,
                        unmapped: bool) -> None:
        raise NotImplementedError

    def get_full_name(self) -> str:
        raise NotImplementedError

    def get_root_map(self) -> uvm_reg_map:
        raise NotImplementedError

    def get_parent(self) -> uvm_reg_block:
        raise NotImplementedError

    def get_parent_map(self) -> uvm_reg_map:
        raise NotImplementedError

    def get_base_addr(
            self,
            hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> uvm_reg_addr_t:
        raise NotImplementedError

    def get_n_bytes(self,
                    hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> int:
        raise NotImplementedError

    def get_addr_unit_bytes(self) -> int:
        raise NotImplementedError

    def get_endian(
            self,
            hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> uvm_endianness_e:
        raise NotImplementedError

    def get_sequencer(
            self,
            hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> uvm_sequencer_base:
        raise NotImplementedError

    def get_adapter(
            self,
            hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> uvm_reg_adapter:
        raise NotImplementedError

    def get_submaps(self,
                    submaps: list[uvm_reg_map],  # ref
                    hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> None:
        raise NotImplementedError

    def get_registers(self,
                      regs: list[uvm_reg],  # ref
                      hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> None:
        raise NotImplementedError

    def get_fields(self,
                   fields: list[uvm_reg_field],  # ref
                   hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> None:
        raise NotImplementedError

    def get_memories(self,
                     mems: list[uvm_mem],  # ref
                     hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> None:
        raise NotImplementedError

    def get_virtual_registers(
            self,
            regs: list[uvm_vreg],  # ref
            hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> None:
        raise NotImplementedError

    def get_virtual_fields(self,
                           fields: list[uvm_vreg_field],  # ref
                           hier: uvm_hier_e = uvm_hier_e.UVM_HIER) -> None:
        raise NotImplementedError

    def get_reg_map_info(self, rg: uvm_reg, error: bool) -> uvm_reg_map_info:
        raise NotImplementedError

    def get_mem_map_info(self, mem: uvm_mem, error: bool) -> uvm_reg_map_info:
        raise NotImplementedError

    def get_size(self) -> int:
        raise NotImplementedError

    def get_physical_address(self,
                             base_addr: uvm_reg_addr_t,
                             mem_offset: uvm_reg_addr_t,
                             n_bytes: int,
                             addr: list[uvm_reg_addr_t]) -> int:
        raise NotImplementedError

    def get_reg_by_offset(self,
                          offset: uvm_reg_addr_t,
                          read: bool = True) -> uvm_reg:
        raise NotImplementedError

    def get_mem_by_offset(self, offset: uvm_reg_addr_t) -> uvm_mem:
        raise NotImplementedError

    def set_auto_predict(self, on: bool = True) -> None:
        raise NotImplementedError

    def get_auto_predict(self) -> bool:
        raise NotImplementedError

    def set_check_on_read(self, on: bool = True) -> None:
        raise NotImplementedError

    def get_check_on_read(self) -> bool:
        raise NotImplementedError

    async def do_bus_write(self,
                           rw: uvm_reg_item,
                           sequencer: uvm_sequencer_base,
                           adapter: uvm_reg_adapter) -> None:
        raise NotImplementedError

    async def do_bus_read(self,
                          rw: uvm_reg_item,
                          sequencer: uvm_sequencer_base,
                          adapter: uvm_reg_adapter) -> None:
        raise NotImplementedError

    async def do_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def do_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    def _get_bus_info(
            self,
            rw: uvm_reg_item) -> tuple[uvm_reg_map_info, int, int, int]:
        raise NotImplementedError

    def set_transaction_order_policy(
            self,
            pol: uvm_reg_transaction_order_policy) -> None:
        raise NotImplementedError

    def get_transaction_order_policy(
            self) -> uvm_reg_transaction_order_policy:
        raise NotImplementedError

    def get_physical_address_to_map(self,
                                    base_addr: uvm_reg_addr_t,
                                    mem_offset: uvm_reg_addr_t,
                                    n_bytes: int,
                                    addr: list[uvm_reg_addr_t],
                                    parent_map: uvm_reg_map,
                                    byte_offset: int,
                                    mem: uvm_mem = None) -> int:
        raise NotImplementedError

    async def perform_accesses(self,
                               accesses: list[uvm_reg_bus_op],
                               rw: uvm_reg_item,
                               adapter: uvm_reg_adapter,
                               sequencer: uvm_sequencer_base) -> None:
        raise NotImplementedError

    async def do_bus_access(self,
                            rw: uvm_reg_item,
                            sequencer: uvm_sequencer_base,
                            adapter: uvm_reg_adapter) -> None:
        raise NotImplementedError

    def unregister(self) -> None:
        raise NotImplementedError

    def clone_and_update(self, rights: str) -> uvm_reg_map:
        raise NotImplementedError

    # TODO: Should this be dunder methods?
    # extern virtual function string      convert2string();
    # extern virtual function uvm_object  clone();
    # extern virtual function void        do_print (uvm_printer printer);
    # extern virtual function void        do_copy   (uvm_object rhs);
