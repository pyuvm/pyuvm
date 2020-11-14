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

class UVMFactoryError(TypeError):
    '''
    For cases where a type is not registered with the factory
    '''

class UVMTLMConnectionError(RuntimeError):
    """
    For problems connecting TLM
    """

class UVMBadPhase(RuntimeError):
    """
    Errors in phasing
    """