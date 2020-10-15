from collections import OrderedDict
import logging
import error_classes
import fnmatch


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    @classmethod
    def clear_singletons(cls):
        cls._instances.clear()
        pass

class Override():
    """
    This class stores an override and an optional path.
    It is intended to be stored in a dict with the original class
    as the key.
    """
    def __init__(self, override, path=None):
        self.override = override
        self.inst_pattern = path

    def path_match(self, path):
        if self.inst_pattern is None:
            return True
        else:
            return fnmatch.fnmatch(path, self.inst_pattern)

class FactoryData(metaclass=Singleton):

    def __init__(self):
        self.classes = {}
        self.clear_overrides()
        self.logger = logging.Logger("Factory")

    def clear_overrides(self):
        self.overrides = {}

    def find_inst_override(self, requested_type, inst_path="", overridden_list=[]):
        """
        :param requested_type: The type we're overriding
        :param inst_path: The inst_path we're using to override
        :param override_list: A list of previously found overrides
        :return: overriding_type
        From 8.3.1.5
        Override searches are recursively applied, with instnace overrides taking precedence
        over type overrides.  If foo overrides bar, and xyz overrides foo, then a request for bar
        returns xyx.
            xyz -> foo -> bar
        Recursive loops result ina n error in which case the type returned is the one that
        formed the loop.
            bar -> xyz -> foo -> bar
        bar is returned with a printed error.
        """
        if len(inst_path) == 0:
            return requested_type
        # Since the instance overrides contain wildcards, we search the ordered list
        # of overrides for a match.  If we find a match we search for an override of that
        # type appending our requested type to the overridden_list. If we find an override
        # that is already in the list we print an error and return the requested type.
        return_type = requested_type
        for path_key in self.type_instance_overrides:
            if (fnmatch.fnmatch(inst_path, path_key)):
                (original_type, overriding_type) = self.type_instance_overrides[path_key]
                if original_type != requested_type:
                    continue
                if overriding_type in overridden_list:
                    self.logger.error(f"Type override loop found at {overriding_type}: {overridden_list}")
                    return overriding_type
                else:
                    overridden_list.append(overriding_type)
                return_type =  self.find_inst_override(overriding_type, inst_path, overridden_list)
        return return_type








class FactoryMeta(type):
    """
    This is the metaclass that causes all uvm_void classes to register themselves
    """

    def __init__(cls, name, bases, clsdict):
        FactoryData().classes[cls.__name__] = cls
        super().__init__(name, bases, clsdict)


class uvm_void(metaclass=FactoryMeta):
    """
    5.2
    SystemVerilog Python uses this class to allow all
    uvm objects to be stored in a uvm_void variable through
    polymorphism.

    In pyuvm, we're using uvm_void() as a meteaclass so
    that all UVM classes can be stored in a factory.
"""


class UVM_ROOT_Singleton(FactoryMeta):
    singleton = None

    def __call__(cls, *args, **kwargs):
        if cls.singleton is None:
            cls.singleton = super(UVM_ROOT_Singleton, cls).__call__(*args, **kwargs)
        return cls.singleton

    @classmethod
    def clear_singletons(cls):
        cls.singleton = None
        pass
