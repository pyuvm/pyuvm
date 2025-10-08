from __future__ import annotations

from pyuvm.reg.uvm_reg_map import uvm_reg_map
from pyuvm.reg.uvm_reg_model import uvm_door_e, uvm_reg_data_t, uvm_status_e
from pyuvm.reg.uvm_vreg import uvm_vreg
from pyuvm.s05_base_classes import uvm_object
from pyuvm.s10_synchronization_classes import (
    uvm_callback,
    uvm_callback_iter,
    uvm_callbacks,
)
from pyuvm.s14_15_python_sequences import uvm_sequence_base

__all__ = [
    "uvm_vreg_field",
    "uvm_vreg_field_cbs",
    "uvm_vreg_field_cb",
    "uvm_vreg_field_cb_iter",
]


class uvm_vreg_field(uvm_object):
    def __init__(self, name: str = "uvm_vreg_field"):
        super().__init__(name)
        raise NotImplementedError

    def configure(self, parent: uvm_vreg, size: int, lsb_pos: int) -> None:
        raise NotImplementedError

    def get_full_name(self) -> str:
        raise NotImplementedError

    def get_parent(self) -> uvm_vreg:
        raise NotImplementedError

    def get_register(self) -> uvm_vreg:
        raise NotImplementedError

    def get_lsb_pos_in_register(self) -> int:
        raise NotImplementedError

    def get_n_bits(self) -> int:
        raise NotImplementedError

    def get_access(self, map: uvm_reg_map = None) -> str:
        raise NotImplementedError

    async def write(
        self,
        idx: int,
        value: uvm_reg_data_t,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def read(
        self,
        idx: int,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def poke(
        self,
        idx: int,
        value: uvm_reg_data_t,
        parent: uvm_sequence_base = None,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    async def peek(
        self,
        idx: int,
        parent: uvm_sequence_base = None,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> tuple[uvm_status_e, uvm_reg_data_t]:
        raise NotImplementedError

    async def pre_write(
        self, idx: int, wdat: uvm_reg_data_t, path: uvm_door_e, map: uvm_reg_map
    ) -> None:
        raise NotImplementedError

    async def post_write(
        self,
        idx: int,
        wdat: uvm_reg_data_t,
        path: uvm_door_e,
        map: uvm_reg_map,
        status: uvm_status_e,
    ) -> None:
        raise NotImplementedError

    async def pre_read(self, idx: int, path: uvm_door_e, map: uvm_reg_map) -> None:
        raise NotImplementedError

    async def post_read(
        self,
        idx: int,
        rdat: uvm_reg_data_t,
        path: uvm_door_e,
        map: uvm_reg_map,
        status: uvm_status_e,
    ) -> None:
        raise NotImplementedError

    # TODO: Should this be dunder methods?
    # extern virtual function void do_print (uvm_printer printer);
    # extern virtual function string convert2string;
    # extern virtual function uvm_object clone();
    # extern virtual function void do_copy   (uvm_object rhs);
    # extern virtual function bit do_compare (uvm_object  rhs,
    #                                        uvm_comparer comparer);
    # extern virtual function void do_pack (uvm_packer packer);
    # extern virtual function void do_unpack (uvm_packer packer);


class uvm_vreg_field_cbs(uvm_callback):
    def __init__(self, name: str = "uvm_vreg_field_cbs"):
        super().__init__(name)
        raise NotImplementedError

    async def pre_write(
        self,
        field: uvm_vreg_field,
        idx: int,
        wdat: uvm_reg_data_t,
        path: uvm_door_e,
        map: uvm_reg_map,
    ) -> None:
        raise NotImplementedError

    async def post_write(
        self,
        field: uvm_vreg_field,
        idx: int,
        wdat: uvm_reg_data_t,
        path: uvm_door_e,
        map: uvm_reg_map,
        status: uvm_status_e,
    ) -> None:
        raise NotImplementedError

    async def pre_read(
        self, field: uvm_vreg_field, idx: int, path: uvm_door_e, map: uvm_reg_map
    ) -> None:
        raise NotImplementedError

    async def post_read(
        self,
        field: uvm_vreg_field,
        idx: int,
        rdat: uvm_reg_data_t,
        path: uvm_door_e,
        map: uvm_reg_map,
        status: uvm_status_e,
    ) -> None:
        raise NotImplementedError


class uvm_vreg_field_cb(uvm_callbacks):
    pass


class uvm_vreg_field_cb_iter(uvm_callback_iter):
    pass
