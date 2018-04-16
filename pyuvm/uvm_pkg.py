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

class Singleton(type):
    _instances={}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls]=super(Singleton,cls).__call__(*args, **kwargs)
        return cls._instances[cls]
    @classmethod
    def clear_singletons(cls):
        cls._instances.clear()
        pass
