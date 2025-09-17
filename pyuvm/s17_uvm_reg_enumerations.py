# Global register enumerations
from pyuvm.s05_base_classes import uvm_object
from pyuvm.error_classes import UVMFatalError
from enum import Enum


UVM_REG_DATA_WIDTH = 64
UVM_REG_ADDR_WIDTH = 64

# 17.2.1.1 uvm_reg_data_t
uvm_reg_data_t = int

# 17.2.1.3 uvm_reg_addr_t
uvm_reg_addr_t = int

uvm_reg_policy_t = [
    "RO",       # no effect, R: no effect.
    "RW",       # as is, R: no effect.
    "RC",       # no effect, R: clears all bits.
    "RS",       # no effect, R: sets all bits.
    "WRC",      # as is, R: clears all bits.
    "WRS",      # as is, R: sets all bits.
    "WC",       # clears all bits, R: no effect.
    "WS",       # sets all bits, R: no effect.
    "WSRC",     # sets all bits, R: clears all bits.
    "WCRS",     # clears all bits, R: sets all bits.
    "W1C",      # 1/0 clears/no effect on matching bit, R: no effect.
    "W1S",      # 1/0 sets/no effect on matching bit, R: no effect.
    "W1T",      # 1/0 toggles/no effect on matching bit, R: no effect.
    "W0C",      # 1/0 no effect on/clears matching bit, R: no effect.
    "W0S",      # 1/0 no effect on/sets matching bit, R: no effect.
    "W0T",      # 1/0 no effect on/toggles matching bit, R: no effect.
    "W1SRC",    # 1/0sets/no effect on matching bit, R: clears all bits.
    "W1CRS",    # 1/0clears/no effect on matching bit, R: sets all bits.
    "W0SRC",    # 1/0no effect on/sets matching bit, R: clears all bits.
    "W0CRS",    # 1/0no effect on/clears matching bit, R: sets all bits.
    "WO",       # as is, R: error.
    "WOC",      # clears all bits, R: error.
    "WOS",      # sets all bits, R: error.
    # first one after HARD reset is as is,
    # other W have no effects, R: no effect.
    "W1",
    # first one after HARD reset is as is,
    # other W have no effects, R: error.
    "WO1",
    "NOACCESS"  # no effect, R: no effect.
]

# 17.2.1.5 uvm_reg_byte_en_t
uvm_reg_byte_en_t = int

uvm_reg_field_ignore_rand_mode = ["RW", "WRC", "WRS", "WO", "W1", "WO1"]


# 17.2.1.7 uvm_hdl_path_slice
class uvm_hdl_path_slice():
    def __init__(self, path: str, offset: int, size: int):
        self.path: str = path
        self.offset: int = offset
        self.size: int = size


# 17.2.2.1 uvm_status_e
class uvm_status_e(Enum):
    UVM_IS_OK = 0  # Operation completed successfully.
    UVM_NOT_OK = 1  # Operation completed with error.
    # Operation completed successfully, but had unknown bits.
    UVM_HAS_X = 2


# 17.2.2.2 uvm_door_e
class uvm_door_e(Enum):
    # Use the front door.
    UVM_FRONTDOOR = 0
    # Use the back door.
    UVM_BACKDOOR = 1
    # Operation derived from observations by a bus
    # monitor via the uvm_reg_predictor
    UVM_PREDICT = 2
    # Operation specified by the context.
    UVM_DEFAULT_DOOR = 3


# 17.2.2.3 uvm_check_e
class uvm_check_e(Enum):
    UVM_NO_CHECK = 0  # Read only.
    UVM_CHECK = 1  # Read and check.


# 17.2.2.4 uvm_endianness_e
class uvm_endianness_e(Enum):
    # Byte ordering not applicable.
    UVM_NO_ENDIAN = 0
    # Least-significant bytes first in consecutive addresses.
    UVM_LITTLE_ENDIAN = 1
    # Most-significant bytes first in consecutive addresses.
    UVM_BIG_ENDIAN = 2
    # Least-significant bytes first at the same address.
    UVM_LITTLE_FIFO = 3
    # Most-significant bytes first at the same address.
    UVM_BIG_FIFO = 4


# 17.2.2.5 uvm_elem_kind_e
class uvm_elem_kind_e(Enum):
    UVM_REG = 0  # Register.
    UVM_FIELD = 1  # Field.
    UVM_MEM = 2  # Memory location.


# 17.2.2.6 uvm_access_e
class uvm_access_e(Enum):
    UVM_READ = 0  # Read operation.
    UVM_WRITE = 1  # Write operation.


# 17.2.2.7 uvm_hier_e
class uvm_hier_e(Enum):
    # Provide info from the local context.
    UVM_NO_HIER = 0
    # Provide info based on the hierarchical context.
    UVM_HIER = 1


# 17.2.2.8 uvm_predict_e
class uvm_predict_e(Enum):
    # Predicted value is as is.
    UVM_PREDICT_DIRECT = 0
    # Predict based on the specified value having been read.
    UVM_PREDICT_READ = 1
    # Predict based on the specified value having been written.
    UVM_PREDICT_WRITE = 2


# 17.2.2.9 uvm_coverage_model_e
class uvm_coverage_model_e(Enum):
    # None.
    UVM_NO_COVERAGE = 0
    # Individual register bits.
    UVM_CVR_REG_BITS = 1
    # Individual register and memory addresses.
    UVM_CVR_ADDR_MAP = 2
    # Field values.
    UVM_CVR_FIELD_VALS = 3
    # All coverage models.
    UVM_CVR_ALL = 4


# 17.2.2.10 uvm_reg_mem_tests_e
class uvm_reg_mem_tests_e(Enum):
    # Run uvm_reg_hw_reset_seq (see E.1).
    UVM_DO_REG_HW_RESET = 0
    # Run uvm_reg_bit_bash_seq (see E.2.2).
    UVM_DO_REG_BIT_BASH = 1
    # Run uvm_reg_access_seq (see E.3.2).
    UVM_DO_REG_ACCESS = 2
    # Run uvm_mem_access_seq (see E.5.2).
    UVM_DO_MEM_ACCESS = 3
    # Run uvm_reg_mem_shared_access_seq (see E.4.3).
    UVM_DO_SHARED_ACCESS = 4
    # Run uvm_mem_walk_seq (see E.6.2).
    UVM_DO_MEM_WALK = 5
    # Run all of the above.
    UVM_DO_ALL_REG_MEM_TESTS = 6


# 17.2.3 uvm_hdl_path_concat
class uvm_hdl_path_concat(uvm_object):
    # 17.2.3.3.1
    def __init__(self, name='unnamed'):
        super().__init__(name)
        self._slices = []

    def __is_overlapping_slice(self, slice: uvm_hdl_path_slice) -> bool:
        """
        Checks if a slice proivided overlaps with any of the slices
        :param slice:uvm_hdl_path_slice: slice object to compare
        :return: bool
        """
        for slice_i in self._slices:
            # check if provided slice is overlapping with any of the slices
            if slice.offset > slice_i.offset:
                slice_0 = slice_i
            else:
                slice_0 = slice
            if slice_i.offset > slice.offset:
                slice_1 = slice
            else:
                slice_1 = slice_i
            is_invalid = slice_1.offset >= slice_0.offset + slice_0.size
            is_invalid = is_invalid or slice_1.offset < slice_0.offset
            if is_invalid:
                return False
            else:
                pass
        return True

    # 17.2.3.3.2
    def set_slices(self, slices: list):
        # Check for validity of slices
        # check if provided list is not empty
        assert len(slices) >= 1, "Empty slice object provided"
        # - if only one slices implements entire register,
        #   both offset and size must be -1
        # - Slices must not overlap but gap is allowed
        if len(self._slices) == 1:
            if self._slices[0].offset != -1:
                raise UVMFatalError(
                    f"""slice offset: {self._slices[0].offset}
                    must be -1 for single slice. See  17.2.3.3.1""")
            if self._slices[1].size != -1:
                raise UVMFatalError(
                    f"""slice size: {self._slices[0].size}
                    must be -1 for single slice. See  17.2.3.3.1""")
        else:
            # Check for slice overlap
            for count, slice in enumerate(self._slices):
                if self.__is_overlapping_slice(slice):
                    raise UVMFatalError(
                        f" Overlapping slice found:: {slice.path}")
            # Check for slice offset order :::
            # The slices shall be specified in most-to-least
            # significant order.
            if len(slices) > 1:
                for count, slice in enumerate(slices):
                    if count == 0:
                        continue
                    if slice.offset >= slices[count - 1].offset:
                        raise UVMFatalError(
                            "Slice order doesnt follow MSB to LSB")
        self._slices = slices

    # 17.2.3.3.3
    def get_slices(self) -> list:
        return self._slices

    # 17.2.3.3.4
    def add_slice(self, slice_i: uvm_hdl_path_slice) -> None:
        for count, slice in enumerate(self._slices):
            if slice.offset >= slice_i.offset:
                raise UVMFatalError("""The slices
                    shall be specified in most-to-least
                    significant order.""")
            if self.__is_overlapping_slice(slice_i):
                raise UVMFatalError(
                    f"Found overlapping slice :: {slice.path}")
        self._slices.append(slice_i)
