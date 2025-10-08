from pyuvm.reg.uvm_reg import uvm_reg
from pyuvm.reg.uvm_reg_item import uvm_reg_item
from pyuvm.reg.uvm_reg_map import uvm_reg_map
from pyuvm.reg.uvm_reg_model import (
    uvm_check_e,
    uvm_door_e,
    uvm_predict_e,
    uvm_reg_byte_en_t,
    uvm_reg_data_t,
    uvm_status_e,
)
from pyuvm.s05_base_classes import uvm_object
from pyuvm.s14_15_python_sequences import uvm_sequence_base

__all__ = ["uvm_reg_fifo"]


class uvm_reg_fifo(uvm_reg):
    def __init__(
        self,
        name: str = "uvm_reg_fifo",
        size: int = 0,
        n_bits: int = 0,
        has_coverage: int = 0,
    ):
        super().__init__(name, n_bits, has_coverage)
        self._size = size
        raise NotImplementedError

    def build(self) -> None:
        raise NotImplementedError

    def set_compare(self, check: uvm_check_e = uvm_check_e.UVM_CHECK) -> None:
        raise NotImplementedError

    def size(self) -> int:
        raise NotImplementedError

    def capacity(self) -> int:
        raise NotImplementedError

    def set(self, value: uvm_reg_data_t, fname: str = "", lineno: int = 0) -> None:
        raise NotImplementedError

    async def update(
        self,
        path: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR,
        map: uvm_reg_map = None,
        parent: uvm_sequence_base = None,
        prior: int = -1,
        extension: uvm_object = None,
        fname: str = "",
        lineno: int = 0,
    ) -> uvm_status_e:
        raise NotImplementedError

    def get(self, fname: str = "", lineno: int = 0) -> uvm_reg_data_t:
        raise NotImplementedError

    def do_predict(
        self,
        rw: uvm_reg_item,
        kind: uvm_predict_e = uvm_predict_e.UVM_PREDICT_DIRECT,
        be: uvm_reg_byte_en_t = -1,
    ) -> bool:
        raise NotImplementedError

    async def pre_write(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    async def pre_read(self, rw: uvm_reg_item) -> None:
        raise NotImplementedError

    def post_randomize(self) -> None:
        raise NotImplementedError
