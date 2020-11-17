from collections import OrderedDict
import logging
import fnmatch
from queue import *
from time import monotonic as time

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

class RunningThreads(metaclass=Singleton):
    def __init__(self):
        self.__threads = []

    def add_thread(self, thread):
        self.__threads.append(thread)

    def join_all(self):
        for thread in self.__threads:
            thread.join()

class Override():
    """
    This class stores an override and an optional path.
    It is intended to be stored in a dict with the original class
    as the key.
    """
    def __init__(self):

        self.type_override = None
        self.inst_overrides = None

    def add(self, override, path = None):
        if path is None:
            self.type_override = override
        else:
            if self.inst_overrides is None:
                self.inst_overrides = OrderedDict()
            self.inst_overrides[path] = override

    def find_inst_override(self, path):
        for inst in self.inst_overrides:
            if fnmatch.fnmatch(path, inst):
                return self.inst_overrides[inst]
        return None

    def __str__(self):
        """
        For printing out the overrides
        :return: str
        """
        if self.type_override is not None:
            to = "Type Override: "+ f"{self.type_override.__name__}"
        else:
            to = "Type Override: None"
        ss = f"{to:25}" + " || "
        if self.inst_overrides is not None:
            ss += "Instance Overrides: "
            first = True
            for inst in self.inst_overrides:
                if not first:
                    ss += " | "
                first = False
                if len(inst)>29:
                    inst = inst[:29]
                ss+=inst +  f" => {self.inst_overrides[inst].__name__}"


        return ss



class FactoryData(metaclass=Singleton):

    def __init__(self):
        self.classes = {}
        self.clear_overrides()
        self.logger = logging.getLogger("Factory")

    def clear_overrides(self):
        self.overrides = {}

    def clear_classes(self):
        self.classes = {}

    def find_override(self, requested_type, inst_path=None, overridden_list=None):
        """
        :param requested_type: The type we're overriding
        :param inst_path: The inst_path we're using to override if any
        :param override_list: A list of previously found overrides
        :return: overriding_type
        From 8.3.1.5
        Override searches are recursively applied, with instance overrides taking precedence
        over type overrides.  If foo overrides bar, and xyz overrides foo, then a request for bar
        returns xyx.
        """

        # xyz -> foo -> bar
        #
        # So if find_override is fo:
        #     fo(xyz) -> fo(foo) -> fo(bar) <-- no override returns bar.
        # Recursive loops result ina n error in which case the type returned is the one that
        # formed the loop.
        #     xyz -> foo -> bar -> xyz
        #
        # fo(xyz) -> fo(foo) -> fo(bar) -> fo(xyz) -- xyz is in list of overrides so return bar
        # bar is returned with a printed error.
        #
        # We use the Override class which contains both the type override if there is one or
        # a list of instance overrides in the order the were added.
        # If inst_path is None we return the type_override or its override
        # If inst_path is given, but we don't find a match we return type_override if it exists

        # Keep track of what classes have been overridden
        #

        # Is there an override loop?
        def check_override(override, overridden_list):
            if overridden_list is None:
                overridden_list = []
            if override in overridden_list:
                self.logger.error(f"{requested_type} already overridden: {overridden_list}")
                return requested_type
            else:
                overridden_list.append(requested_type)
                rec_override = self.find_override(override, inst_path, overridden_list)
                return rec_override

        # Save the type for a later check
        # Is this requested type even in the list of overrides?
        try:
            override = self.overrides[requested_type]
        except KeyError:
            return requested_type

        if inst_path is not None:
            for path in override.inst_overrides:
                if fnmatch.fnmatch(inst_path, path):
                    found_type = override.inst_overrides[path]
                    return check_override(found_type, overridden_list)

        # No inst requested or found, do we have a type override?
        if override.type_override is not None:
            return check_override(override.type_override, overridden_list)
        else:
            return requested_type

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

class PeekQueue(Queue):
    def peek(self, block=True, timeout=None):
        '''Return first item from queue without removing it

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until an item is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the Empty exception if no item was available within that time.
        Otherwise ('block' is false), return an item if one is immediately
        available, else raise the Empty exception ('timeout' is ignored
        in that case).
        '''
        with self.not_empty:
            if not block:
                if not self._qsize():
                    raise Empty
            elif timeout is None:
                while not self._qsize():
                    self.not_empty.wait()
            elif timeout < 0:
                raise ValueError("'timeout' must be a non-negative number")
            else:
                endtime = time() + timeout
                while not self._qsize():
                    remaining = endtime - time()
                    if remaining <= 0.0:
                        raise Empty
                    self.not_empty.wait(remaining)
            item = self.queue[0]
            self.not_full.notify()
            return item

