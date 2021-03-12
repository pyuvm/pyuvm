
class UVMError(Exception):
    """
    All UVM Errors
    """


class UVMNotImplemented(UVMError):
    """For methods that we haven't yet implemented."""


class UsePythonMethod(UVMError):
    """
    For cases where the user should use a Python
    method rather than a UVM method.  For example
    use __str__() instead of convert2string()
    """


class UVMFactoryError(UVMError):
    """ For cases where a type is not registered with the factory"""


class UVMTLMConnectionError(UVMError):
    """For problems connecting TLM"""


class UVMBadPhase(UVMError):
    """Errors in phasing"""


class UVMSequenceError(UVMError):
    """Errors using sequences"""


class UVMConfigError(UVMError):
    """Errors using the config_db"""


class UVMConfigItemNotFound(UVMError):
    """Couldn't find something in config_db"""


class UVMFatalError(UVMError):
    """ Used to dump out of the testbench"""
