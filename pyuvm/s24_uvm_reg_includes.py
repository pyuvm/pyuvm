'''
Collection of defines to be sued
'''
from enum import Enum


class path_t(Enum):
    '''
    Access TYPE
    '''
    FRONTDOOR = 1
    BACKDOOR = 2
    USER_FRONTDOOR = 3


class check_t(Enum):
    '''
    Check TYPE
    '''
    CHECK = 1
    NO_CHECK = 2


class elem_kind(Enum):
    '''
    Status TYPE
    '''
    IS_OK = 1
    IS_NOT_OK = 2


# Predict Type
class predict_t(Enum):
    '''
    predict_t main prediction to be used
    PREDICT_WRITE   = 1
    PREDICT_READ    = 2
    PREDICT_DIRECT  = 3
    '''
    PREDICT_WRITE = 1
    PREDICT_READ = 2
    PREDICT_DIRECT = 3


#
class elem_kind_e(Enum):
    pass


#
class access_e(Enum):
    '''
    access_e typoe of access allowed
    PYUVM_READ  = 0
    PYUVM_WRITE = 1
    '''
    PYUVM_READ = 0
    PYUVM_WRITE = 1


class uvm_resp_t(Enum):
    '''
    uvm_resp_t is the main response based on the access issued
    PASS_RESP  = 0
    ERROR_RESP = 1
    '''
    PASS_RESP = 0
    ERROR_RESP = 1


def rand_enable(use_pyvsc: bool):
    '''
    New Decorator class with randomization option
    If the randomization is switched off then the decorator will no more use
    py_vsc but it just disables it allowing user to use local methods if needed
    '''
    class enable_rand:
        # Accept class as argument
        def __init__(self, cls) -> None:
            self.cls = cls

        # operate on CLS init inupt argument
        def __call__(self):
            if (use_pyvsc is True):
                pass
                # return vsc.randobj
            else:
                # Return the function unchanged, not decorated.
                # if use_pyvsc is not enabled
                return self.cls
    return enable_rand


# Global to be set in case we wanna use the VSC package
enable_pyvsc = False
# Global to be set in case we wanna use the auto prediction
enable_auto_predict = True
# Global enable bit for error response in case of
# NO-EFFECT action based on the access type
enable_throw_error_response_on_read = False
# Global enable bit for error response in case of
# NO-EFFECT action based on the access type
enable_throw_error_response_on_write = False
# Global assert disable this is used in order to
# avoid code interruption by just checking for the error list
disable_code_interruption_assert = False


def error_out(header, message):
    '''
    Used to error out based on header and message
    '''
    assert (disable_code_interruption_assert, header + message)


class uvm_reg_bus_op:
    '''
    Standard class for register bus operation to
    be used into the Prediction or Adpater
    '''
    kind: access_e
    addr: int
    data: int
    n_bits: int
    byte_en: bool
    status: uvm_resp_t


class uvm_reg_error_decoder(Enum):
    '''
    List of uvm_reg errors to be collected
    FIELD_CANNOT_BE_NONE        = 1
    FIELD_ALREADY_ADDED         = 2
    FIELD_DOESNT_FIT_INTO_REG   = 3
    FIELD_OVERLAPPING_ERROR     = 4
    REG_SIZE_CANNOT_BE_ZERO     = 5
    '''
    FIELD_CANNOT_BE_NONE = 1
    FIELD_ALREADY_ADDED = 2
    FIELD_DOESNT_FIT_INTO_REG = 3
    FIELD_OVERLAPPING_ERROR = 4
    REG_SIZE_CANNOT_BE_ZERO = 5


class uvm_reg_field_error_decoder(Enum):
    '''
    List of uvm_reg errors to be collected
    CONFIGURE_MUST_BE_CALLED_BEFORE         = 1
    ACCESS_TYPE_NEEDS_TO_BE_A_STRING        = 2
    WRONG_ACCESS_FOR_PREDICT_READ           = 3
    WRONG_COMBINATION_PREDICTION_DIRECTION  = 4
    ACCESS_VALUE_OUT_OF_LIST                = 5
    '''
    CONFIGURE_MUST_BE_CALLED_BEFORE = 1
    ACCESS_TYPE_NEEDS_TO_BE_A_STRING = 2
    WRONG_ACCESS_FOR_PREDICT_READ = 3
    WRONG_COMBINATION_PREDICTION_DIRECTION = 4
    ACCESS_VALUE_OUT_OF_LIST = 5
