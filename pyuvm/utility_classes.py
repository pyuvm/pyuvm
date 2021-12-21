from collections import OrderedDict
import logging
import fnmatch
import cocotb.queue
from cocotb.triggers import Event, NullTrigger
from cocotb.queue import QueueEmpty

FIFO_DEBUG = 5
PYUVM_DEBUG = 4
logging.addLevelName(FIFO_DEBUG, "FIFO_DEBUG")
logging.addLevelName(PYUVM_DEBUG, "PYUVM_DEBUG")


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)  # noqa: E501
        return cls._instances[cls]

    @classmethod
    def clear_singletons(cls, keep):
        classes = list(cls._instances.keys())
        for del_cls in classes:
            if del_cls not in keep:
                del(cls._instances[del_cls])


class Override:
    """
    This class stores an override and an optional path.
    It is intended to be stored in a dict with the original class
    as the key.
    """

    def __init__(self):

        self.type_override = None
        self.inst_overrides = OrderedDict()

    def add(self, override, path=None):
        if path is None:
            self.type_override = override
        else:
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
            to = "Type Override: " + f"{self.type_override.__name__}"
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
                if len(inst) > 29:
                    inst = inst[:29]
                ss += inst + f" => {self.inst_overrides[inst].__name__}"

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

    # From 8.3.1.5
    def find_override(self, requested_type,
                      inst_path=None, overridden_list=None):
        """
        :param requested_type: The type we're overriding
        :param inst_path: The inst_path we're using to override if any
        :param overridden_list: A list of previously found overrides
        :return: overriding_type

        Override searches are recursively applied, with instance
        overrides taking precedence over type overrides.
        If foo overrides bar, and xyz overrides foo, then a request for bar
        returns xyx.
        """

        # xyz -> foo -> bar
        #
        # So if find_override is fo:
        #     fo(xyz) -> fo(foo) -> fo(bar) <-- no override returns bar.
        # Recursive loops result ina n error in which case the
        # type returned is the one that formed the loop:
        # xyz -> foo -> bar -> xyz
        #
        # fo(xyz) -> fo(foo) -> fo(bar) -> fo(xyz) -- xyz is in
        # list of overrides so return bar
        # bar is returned with a printed error.
        #
        # We use the Override class which contains both the type override if
        # there is one or
        # a list of instance overrides in the order the were added.
        # If inst_path is None we return the type_override or its override
        # If inst_path is given, but we don't find a match we return
        # type_override if it exists

        # Keep track of what classes have been overridden
        #

        # Is there an override loop?
        # noinspection PyShadowingNames
        def check_override(override, overridden_list):
            if overridden_list is None:
                overridden_list = []
            if override in overridden_list:
                self.logger.error(
                    f"{requested_type} already overridden: {overridden_list}")
                return requested_type
            else:
                overridden_list.append(requested_type)
                rec_override = self.find_override(override,
                                                  inst_path,
                                                  overridden_list)
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
    This is the metaclass that causes all uvm_void classes
    to register themselves
    """

    def __init__(cls, name, bases, cls_dict):
        FactoryData().classes[cls.__name__] = cls
        super().__init__(name, bases, cls_dict)


class uvm_void(metaclass=FactoryMeta):
    """
    5.2
    SystemVerilog Python uses this class to allow all
    uvm objects to be stored in a uvm_void variable through
    polymorphism.

    In pyuvm, we're using uvm_void() as a metaclass so
    that all UVM classes can be stored in a factory.
"""


class UVM_ROOT_Singleton(FactoryMeta):
    singleton = None

    def __call__(cls, *args, **kwargs):
        if cls.singleton is None:
            cls.singleton = super(UVM_ROOT_Singleton, cls).__call__(*args, **kwargs)  # noqa : E501
        return cls.singleton

    @classmethod
    def clear_singletons(cls):
        cls.singleton = None
        pass


class ObjectionHandler(metaclass=Singleton):
    """
    This singleton accepts objections and then allows
    them to be removed. It returns True to run_phase_complete()
    when there are no objections left.
    """

    def __init__(self):
        self.__objections = {}
        self._objection_event = Event("objection changed")
        self.objection_raised = False
        self.run_phase_done_flag = None  # used in test suites
        self.printed_warning = False

    def __str__(self):
        ss = f"run_phase complete: {self.run_phase_complete()}\n"
        ss += "Current Objections:\n"
        for cc in self.__objections:
            ss += f"{self.__objections[cc]}\n"
        return ss

    def clear(self):
        if len(self.__objections) != 0:
            logging.warning("Clearing objections raised by %s",
                            ', '.join(self.__objections.values()))
            self.__objections = {}
        self.objection_raised = False

    def raise_objection(self, raiser):
        self.__objections[raiser] = raiser.get_full_name()
        self.objection_raised = True
        self._objection_event.clear()

    def drop_objection(self, dropper):
        try:
            del self.__objections[dropper]
        except KeyError:
            self.objection_raised = True
            pass
        if len(self.__objections) == 0:
            self._objection_event.set()

    async def run_phase_complete(self):
        # Allow the run_phase coros to get scheduled and raise objections:
        await NullTrigger()
        if self.objection_raised:
            await self._objection_event.wait()
        else:
            logging.warning(
                "You did not call self.raise_objection() in any run_phase")


class UVMQueue(cocotb.queue.Queue):
    """
    The UVMQueue provides a peek function as well as the
    ability to break out of a blocking operation if
    the time_to_die predicate is true.  The time
    to die is set to the dropping of all run_phase objections
    by default.
    """
    def __str__(self):
        return str(self._queue)

    def _peek(self):
        return self._queue[0]

    async def peek(self):
        """Remove and return an item from the queue.
        If the queue is empty, wait until an item is available.
        """
        while self.empty():
            event = Event('{} peek'.format(type(self).__name__))
            self._getters.append((event, cocotb.scheduler._current_task))
            await event.wait()
        return self.peek_nowait()

    def peek_nowait(self):
        """Remove and return an item from the queue.
        Return an item if one is immediately available, else raise
        :exc:`asyncio.QueueEmpty`.
        """
        if self.empty():
            raise QueueEmpty()
        item = self._peek()
        return item
