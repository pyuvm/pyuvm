# from base_classes import *
from pyuvm.s14_15_python_sequences import uvm_seq_item_port
from pyuvm.s12_uvm_tlm_interfaces import uvm_analysis_export
from pyuvm.s13_uvm_component import *
from pyuvm import error_classes
from enum import IntEnum


# This section and sequences are the crux of pyuvm.
# The classes here allow us to build classic UVM
# testbenches in Python.
#
# Section 13 of the IEEE-UVM Reference Manual (1800.2-2017)
# lists five pieces of uvm_component functionality.
# pyuvm implements much of this functionality using Python:
#
# a: Hierarchy---This is implemented in pyuvm
# b: Phasing---This is also implemented in pyuvm, but is hardcoded
#              to the standard UVM phases.
# c: Hierarchical Reporting---We manage this with the logging module. It is
#              orthogonal to the components.
# d: Transaction Recording---We do not record transactions since pyuvm does
#              not run in the simulator. This
# could be added later if we see a need or way to do it.
# e: Factory---pyuvm manages the factory through the create() method without
#              all the SystemVerilog typing overhead.
#


class uvm_active_passive_enum(IntEnum):
    UVM_PASSIVE = 0
    UVM_ACTIVE = 1


# Class Declarations


# 13.2
class uvm_test(uvm_component):
    """
    The base class for all tests
    """


# 13.3
class uvm_env(uvm_component):
    """
    The base class for hierarchical containers of other components that
    together comprise a complete environment. The environment may
    initially consist of the entire testbench. Later, it can be reused as
    a sub-environment in even larger system-level environments.
    """


# 13.4
class uvm_agent(uvm_component):
    """
    Contains controls for individual agents
    """

    def build_phase(self):
        """
        This ``build_phase()`` implements agent-specific behavior.
            * It sets the agent's ``is_active`` property to ``UVM_ACTIVE``
            * It allows the user to override the ``is_active`` property using
              the ``cdb_get()`` method.
            * It logs a warning if the user sets an illegal value for
              ``is_active`` and sets the value to ``UVM_ACTIVE``.
        """
        super().build_phase()
        self.is_active = uvm_active_passive_enum.UVM_ACTIVE
        try:
            self.is_active = self.cdb_get("is_active")
        except error_classes.UVMConfigItemNotFound:
            self.is_active = uvm_active_passive_enum.UVM_ACTIVE

        if self.is_active not in list(uvm_active_passive_enum):
            self.logger.warning(f"{self.get_full_name()}"
                                "has illegal is_active"
                                f" value: {self.is_active}."
                                "Setting to UVM_ACTIVE")
            self.is_active = uvm_active_passive_enum.UVM_ACTIVE

    def get_is_active(self):
        return self.is_active

    def active(self):
        return self.get_is_active() == uvm_active_passive_enum.UVM_ACTIVE


# 13.5
class uvm_monitor(uvm_component):
    ...


# 13.6
class uvm_scoreboard(uvm_component):
    ...


# 13.7
class uvm_driver(uvm_component):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.seq_item_port = uvm_seq_item_port("seq_item_port", self)


# 13.8 uvm_push_driver

# Never seen one used. Not implemented.


# 13.9
class uvm_subscriber(uvm_component):
    class uvm_AnalysisImp(uvm_analysis_export):
        def __init__(self, name, parent, write_fn):
            super().__init__(name, parent)
            self.write_fn = write_fn

        def write(self, tt):
            """
            Write a transaction to all the connected subscribers.

            :param tt: The transaction to write
            :return: None

            """
            self.write_fn(tt)

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.analysis_export = self.uvm_AnalysisImp("analysis_export",
                                                    self,
                                                    self.write)

    def write(self, tt):
        """
        Force the user to implement the write method.
        """
        raise error_classes.UVMFatalError(
            "You must override the write() method in"
            f"uvm_subscriber {self.get_full_name()}")
