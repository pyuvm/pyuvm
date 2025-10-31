from pyuvm.s10_synchronization_classes import (
    uvm_callback,
    uvm_callback_iter,
    uvm_callbacks,
)

__all__ = [
    "uvm_reg_cbs",
    "uvm_reg_cb",
    "uvm_reg_cb_iter",
    "uvm_reg_bd_cb",
    "uvm_reg_bd_cb_iter",
    "uvm_mem_cb",
    "uvm_mem_cb_iter",
    "uvm_reg_field_cb",
    "uvm_reg_field_cb_iter",
    "uvm_reg_read_only_cbs",
    "uvm_reg_write_only_cbs",
]


class uvm_reg_cbs(uvm_callback):
    def __init__(self, name: str = "uvm_reg_cbs"):
        super().__init__()
        raise NotImplementedError


class uvm_reg_cb(uvm_callbacks):
    pass


class uvm_reg_cb_iter(uvm_callback_iter):
    pass


class uvm_reg_bd_cb(uvm_callbacks):
    pass


class uvm_reg_bd_cb_iter(uvm_callback_iter):
    pass


class uvm_mem_cb(uvm_callbacks):
    pass


class uvm_mem_cb_iter(uvm_callback_iter):
    pass


class uvm_reg_field_cb(uvm_callbacks):
    pass


class uvm_reg_field_cb_iter(uvm_callback_iter):
    pass


class uvm_reg_read_only_cbs(uvm_reg_cbs):
    def __init__(self, name: str = "uvm_reg_read_only_cbs"):
        super().__init__(name)
        raise NotImplementedError


class uvm_reg_write_only_cbs(uvm_reg_cbs):
    def __init__(self, name: str = "uvm_reg_write_only_cbs"):
        super().__init__(name)
        raise NotImplementedError
