from enum import Enum, auto

class UVMNotImplemented(NotImplementedError):
    '''
    For methods that we haven't yet implemented.
    '''

class UsePythonMethod(NotImplementedError):
    '''
    For cases where the user should use a Python
    method rather than a UVM method.  For example
    use __str__() instead of convert2string()
    '''

