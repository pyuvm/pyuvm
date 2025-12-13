from dataclasses import dataclass
from enum import Enum, IntEnum

from pyuvm._s05_base_classes import uvm_object

__all__ = [
    "UVM_DEFAULT_PATH",
    "UVM_REG_DATA_WIDTH",
    "uvm_reg_data_t",
    "uvm_reg_data_logic_t",
    "uvm_reg_addr_t",
    "uvm_reg_addr_logic_t",
    "uvm_reg_byte_en_t",
    "uvm_reg_cvr_t",
    "uvm_hdl_path_slice",
    "uvm_status_e",
    "uvm_door_e",
    "uvm_path_e",
    "uvm_check_e",
    "uvm_endianness_e",
    "uvm_elem_kind_e",
    "uvm_access_e",
    "uvm_hier_e",
    "uvm_predict_e",
    "uvm_coverage_model_e",
    "uvm_reg_mem_test_e",
    "uvm_hdl_path_concat",
    "uvm_reg_backdoor",
    "uvm_reg_frontdoor",
    "uvm_reg_map_addr_range",
    "uvm_object_string_pool",
]


class uvm_reg_data_t(int): ...


class uvm_reg_data_logic_t(int): ...


class uvm_reg_addr_t(int): ...


class uvm_reg_addr_logic_t(int): ...


class uvm_reg_byte_en_t(int): ...


class uvm_reg_cvr_t(int): ...


@dataclass
class uvm_hdl_path_slice(uvm_object):
    path: str
    offset: int
    size: int


class uvm_status_e(Enum):
    UVM_IS_OK = 0
    UVM_NOT_OK = 1
    UVM_HAS_X = 2


class uvm_door_e(Enum):
    UVM_FRONTDOOR = 0
    UVM_BACKDOOR = 1
    UVM_PREDICT = 2
    UVM_DEFAULT_DOOR = 3


class uvm_path_e(Enum):
    pass


class uvm_check_e(Enum):
    UVM_NO_CHECK = 0
    UVM_CHECK = 1


class uvm_endianness_e(Enum):
    UVM_NO_ENDIAN = 0
    UVM_LITTLE_ENDIAN = 1
    UVM_BIG_ENDIAN = 2
    UVM_LITTLE_FIFO = 3
    UVM_BIG_FIFO = 4


class uvm_elem_kind_e(Enum):
    UVM_REG = 0
    UVM_FIELD = 1
    UVM_MEM = 2


class uvm_access_e(Enum):
    UVM_READ = 0
    UVM_WRITE = 1
    UVM_BURST_READ = 2
    UVM_BURST_WRITE = 3


class uvm_hier_e(Enum):
    UVM_NO_HIER = 0
    UVM_HIER = 1


class uvm_predict_e(Enum):
    UVM_PREDICT_DIRECT = 0
    UVM_PREDICT_READ = 1
    UVM_PREDICT_WRITE = 2


class uvm_coverage_model_e(Enum):
    UVM_NO_COVERAGE = 0
    UVM_CVR_REG_BITS = 1
    UVM_CVR_ADDR_MAP = 2
    UVM_CVR_FIELD_VALS = 4
    UVM_CVR_ALL = -1


class uvm_reg_mem_test_e(IntEnum):
    UVM_DO_REG_HW_RESET = 0x0000_0000_0000_0001
    UVM_DO_REG_BIT_BASH = 0x0000_0000_0000_0002
    UVM_DO_REG_ACCESS = 0x0000_0000_0000_0004
    UVM_DO_MEM_ACCESS = 0x0000_0000_0000_0008
    UVM_DO_SHARED_ACCESS = 0x0000_0000_0000_0010
    UVM_DO_MEM_WALK = 0x0000_0000_0000_0020
    UVM_DO_ALL_REG_MEM_TESTS = 0xFFFF_FFFF_FFFF_FFFF


class uvm_hdl_path_concat(uvm_object):
    def __init__(self, name: str = ""):
        super().__init__(name)
        raise NotImplementedError


class uvm_reg_backdoor(uvm_object):
    def __init__(self, name: str = ""):
        super().__init__(name)
        raise NotImplementedError


class uvm_reg_frontdoor:
    def __init__(self):
        raise NotImplementedError


class uvm_reg_map_addr_range:
    def __init__(self):
        raise NotImplementedError


class uvm_object_string_pool(uvm_object):
    def __init__(self, name: str = ""):
        super().__init__(name)
        raise NotImplementedError


UVM_DEFAULT_PATH: uvm_door_e = uvm_door_e.UVM_DEFAULT_DOOR
UVM_REG_DATA_WIDTH: int = 64
