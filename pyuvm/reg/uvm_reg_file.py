from __future__ import annotations

from typing import TYPE_CHECKING

from pyuvm.s05_base_classes import uvm_object

if TYPE_CHECKING:
    from pyuvm.reg.uvm_reg_block import uvm_reg_block

__all__ = ["uvm_reg_file"]


class uvm_reg_file(uvm_object):
    def __init__(self, name: str = ""):
        super().__init__(name)
        raise NotImplementedError

    def configure(
        self,
        blk_parent: uvm_reg_block,
        regfile_parent: uvm_reg_file,
        hdl_path: str = "",
    ) -> None:
        raise NotImplementedError

    def get_full_name(self) -> str:
        raise NotImplementedError

    def get_parent(self) -> uvm_reg_block:
        raise NotImplementedError

    def get_block(self) -> uvm_reg_block:
        raise NotImplementedError

    def get_regfile(self) -> uvm_reg_file:
        raise NotImplementedError

    def clear_hdl_path(self, kind: str = "RTL") -> None:
        raise NotImplementedError

    def add_hdl_path(self, path: str, kind: str = "RTL") -> None:
        raise NotImplementedError

    def has_hdl_path(self, kind: str = "") -> bool:
        raise NotImplementedError

    def get_hdl_path(self, paths: list[str], kind: str = "") -> None:
        raise NotImplementedError

    def get_full_hdl_path(
        self, paths: list[str], kind: str = "", separator: str = "."
    ) -> None:
        raise NotImplementedError

    def set_default_hdl_path(self, kind: str) -> None:
        raise NotImplementedError

    def get_default_hdl_path(self) -> str:
        raise NotImplementedError

    # TODO: Should this be dunder methods?
    # extern virtual function void         do_print (uvm_printer printer);
    # extern virtual function string       convert2string();
    # extern virtual function uvm_object   clone      ();
    # extern virtual function void         do_copy    (uvm_object rhs);
    # extern virtual function bit          do_compare (uvm_object  rhs,
    #                                                  uvm_comparer comparer);
    # extern virtual function void         do_pack    (uvm_packer packer);
    # extern virtual function void         do_unpack  (uvm_packer packer);
