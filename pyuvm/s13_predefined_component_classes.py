# from base_classes import *
from pyuvm.s14_15_python_sequences import uvm_seq_item_port
from pyuvm.s12_uvm_tlm_interfaces import  uvm_analysis_export
from pyuvm.s13_uvm_component import *

"""
This section and sequences are the crux of pyuvm. The classes here allow us to build classic UVM
testbenches in Python.

Section 13 of the IEEE-UVM Refernce Manual (1800.2-2017) lists five pieces of uvm_component functionality.
pyuvm implements much of this functionality using Python:

a: Hierarchy---This is implemented in pyuvm
b: Phasing---This is also implemented in pyuvm, but is hardcoded to the standard UVM phases.
c: Hierarchical Reporting---We manage this with the logging module. It is orthogonal to the components.
d: Transaction Recording---We do not record transactions since pyuvm does not run in the simulator. This
could be added later if we see a need or way to do it.
e: Factory---pyuvm manages the factory throught the create() method without all the SystemVerilog typing overhead.

"""


# Class Declarations

class uvm_test(uvm_component):
    """
    13.2
    The base class for all user-defined tests

    Python does not require that we override new() for every
    UVM class, so we don't do that (same for __init__).
    """


class uvm_env(uvm_component):
    """
    13.3
    The user's containes for agents and what-not
    """


class uvm_agent(uvm_component):
    """
    13.4
    Contains controls for individual agents
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.__is_active = False

    """
    Have chosen to implement the spirit of 
    the is_active member rather than the 
    enum-based implementation.
    """

    @property
    def is_active(self):
        return self.__is_active

    @is_active.setter
    def is_active(self, is_active):
        assert (isinstance(is_active, bool))
        self.__is_active = is_active


class uvm_monitor(uvm_component):
    """
    13.5
    We'll see if anything is ever added
    to uvm_monitor
    """


class uvm_scoreboard(uvm_component):
    """
    13.6
    """

# 13.7
class uvm_driver(uvm_component):

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.seq_item_port = uvm_seq_item_port("seq_item_port", self)
        pass

"""
13.8 uvm_push_driver

Never seen one used. Not implemented.
"""

# 13.9
class uvm_subscriber(uvm_analysis_export):
    """
    A component that is also a uvm_analysis_export
    """
