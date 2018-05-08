from enum import Enum, auto
import base_classes
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



class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
            cls.x = 5
        return cls._instances[cls]

def run_test(test_name):
    test = base_classes.uvm_object.create_by_name ( globals ()[test_name], 'uvm_test_top' )


