# from base_classes import *
import error_classes
from queue import Queue
from s09_phasing import PyuvmPhases, PhaseType
import utility_classes
from s06_reporting_classes import uvm_report_object
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

class uvm_component(uvm_report_object):
    """
    13.1.1 Class Declaration

The specification calls for uvm_component to extend uvm_report_object. However, pyuvm
uses the logging module orthogonally to class structure. It may be that in future
we find a reason to wrap the basic logging package in the uvm code, but at this point
we are better off leaving logging to itself.

The choice then becomes whether to create a uvm_report_object class as a placeholder
to preserve the UVM reference manual hierarchy or to code what is really going on.
We've opted for the latter.
    """
    component_dict = {}

    def __init__(self, name, parent=None):
        """
        13.1.2.1---This is new() in the IEEE-UVM, but we mean
        the same thing with __init__()
        """

        super ().__init__ ( name )
        self.__parent = None
        self.__children={}
        if parent==None and name != 'uvm_root':
            parent=uvm_root()
        self.parent = parent
        if parent != None:
            parent.add_child(name, self)
        self.print_enabled=True #13.1.2.2

        # Cache the hierarchy for easy access
        if name != 'uvm_root':
            uvm_component.component_dict[self.get_full_name()]=self

    def do_execute_op(self, op):
        raise error_classes.UVMNotImplemented("Policies not implemented")

    def create(self, name, parent):
        return self.__class__(name, parent)


    def get_parent(self):
        """
        :return: parent object
        13.1.3.1--- No 'get_' prefix
        """
        return self.__parent
    @property
    def parent(self):
        return self.get_parent()

    @parent.setter
    def parent(self, parent):
        if parent != None:
            assert(isinstance(parent,uvm_component)), f" {parent} is of type {type(parent)}"
        assert(parent != self), f'Cannot make a {self.get_name()} its own parent.  That is incest.'
        self.__parent=parent

    def get_full_name(self):
        """
        :return: Name concatenated to parent name.
        13.1.3.2
        """
        if self.get_name() == 'uvm_root':
            return ''
        fullname = self.__parent.get_full_name()
        if len(fullname)==0:
            fullname = self.get_name()
        else:
            fullname = fullname + "." + self.get_name()
        return fullname

    # Children in pyuvm
    # 13.1.3.4 modified to be pythonic
    """
    UVM components contain a list of child components as
    the basis for creating the UVM hierarchy.  However
    the UVM accesses those children in an unPythonic
    way.  Instead of asking for an iterator of children,
    which is what Python does and what we'll do here, the
    UVM uses `get_child()`, `get_first_child()`, and 
    `get_next_child()` to create iterative-like behavior,
    but there is no sense in recreating this if we're
    in a language like Python with powerful iterative
    functionality.
    
    We will store children in a Python dict so as to
    implement get_child(), but we will not implement
    get_first_child() or get_next_child().  We will
    implement __iter__ so that the user can use
    the component as an iterator.
    """
    def get_children(self):
        """
        13.1.3.3
        :return: dict with children
        """
        return list(self.children)

    def add_child(self, name, child):
        assert(name not in self.__children), f"{self.get_full_name()} already has a child named {name}"
        self.__children[name]=child

    @property
    def hierarchy(self):
        """
        We return a generator to find the children. This is more pythonic and saves memory
        for large hierarchies.
        :return: An ordered list of components top to bottom.
        """
        yield self
        for child in self.children:
            assert isinstance(child, uvm_component)
            yield child
            for grandchild in child.children:
                assert isinstance ( grandchild,uvm_component, )
                yield grandchild

        # The UVM relies upon a hokey iteration system to get the children
        # out of a component class. You get the name of the first child and
        # then pass it to get_next_child to get the name of the next
        # child. This continues until get_next_child returns zero.
        #
        # Python has a rich iteration system and it would be foolish to
        # eschew it. So we are not going to implement the above.  Instead
        # the children() method is a generator that allows you to loop
        # through the children.
    @property
    def children(self):
        """
        13.1.3.4
        Implements the intention of this requirement
        without the approach taken in the UVM
        """
        for childname in self.__children:
            yield self.__children[childname]

    def __repr__(self):
        return self.get_full_name()

    def get_child(self, name):
        """
        13.1.3.4
        :param self:
        :param name: child string
        :return: uvm_component of that name
        """
        assert(isinstance(name, str))
        try:
            return self.__children[name]
        except KeyError:
            return None


    def get_num_children(self):
        """
        13.1.3.5
        :param self:
        :return: Number of children in component
        """
        return len(self.__children)

    def has_child(self, name):
        """
        13.1.3.6
        :param self:
        :param name: Name of child object
        :return: True if exists, False otherwise
        """
        assert(isinstance(name,str))
        return name in self.__children

    def lookup(self, name):
        """
        13.1.3.7
        Return a component base on the path. If . then
        use full name from root otherwise relative
        :param name: The search name
        :return: either the component or None
        """
        assert(isinstance(name,str))
        if name[0] == '.':
            lookup_name=name[1:]
        else:
            lookup_name=f'{self.get_full_name()}.{name}'
        try:
            return uvm_component.component_dict[lookup_name]
        except KeyError:
            return None

    def get_depth(self):
        """
        13.1.3.8
        Get the depth that I am from the top component. uvm_root is 0.
        :param self: That's me
        :return: depth
        """
        # Rather than getting all recursive just count
        # levels in the full name.
        fullname = self.get_full_name()
        if len(fullname) == 0:
            return 0
        else:
            return len(self.get_full_name().split("."))

    def build_phase(self,phase=None):...

    def connect_phase(self, phase=None):...

    def end_of_elaboration_phase(self, phase=None):...

    def start_of_simulation_phase(self, phase=None):...

    def run_phase(self,phase=None):...

    def extract_phase(self,phase=None):...

    def check_phase(self,phase=None):...

    def report_phase(self,phase=None):...

    def final_phase(self,phase=None):...



    """
    The following sections have been skipped and could
    be implemented at a later time if necessary.
    13.1.4.2--Run time phases
    13.1.4.3--phase_* methods
    13.1.4.4--*_domain methods
    13.1.5.5--suspend
    13.1.4.6--pre_abort
    13.1.5--Configurtion interface
    13.1.6--Recording interface
    13.1.7--Other interfaces
    """

class uvm_root(uvm_component, metaclass=utility_classes.UVM_ROOT_Singleton):
    """
    F.7.  We do not use uvm_pkg to hold uvm_root.  Instead it
    is a class variable of uvm_commponent.  This avoids
    circular reference issues regarding uvm_pkg.

    Plus, it's cleaner.

    uvm_root is still a singleton that you access through its
    constructor instead of through a get() method.

    Much of the functionality in Annex F delivers functionality
    in SystemVerilog that is already built into Python. So we're
    going to skip much of that Annex.
    """
    singleton = None

    def __call__(cls, *args, **kwargs):
        if cls.singleton is None:
            cls.singleton = super().__call__(*args, **kwargs)
        return cls.singleton

    @classmethod
    def clear_singletons(cls):
        cls.singleton = None

    def __init__(self):
        super().__init__("uvm_root", None)


    def run_test(self, test_name=""):
        """
        This implementation skips much of the state-setting and
        what not in the LRM and focuses on building the
        hierarchy and running the test.

        At this time pyuvm has not implemented the phasing
        system described in the LRM.  It's not clear that anyone
        is using it, and in fact it is recommended that people
        stick to the basic phases.  So this implementation loops
        through the hierarchy and runs the phases.

        :param test_name: The uvm testname
        :return: none
        """
        self.uvm_test_top=uvm_object.create_by_name(test_name,'uvm_test_top',self)
        top_down = self.uvm_test_top.hierarchy
        bottom_up = list(self.uvm_test_top.hierarchy)
        bottom_up.reverse()

        for phase, phase_data in PyuvmPhases.__members__.items():
            method,phase_type=phase_data.value
            if phase_type == PhaseType.TOPDOWN:
                comp_list=top_down
            else:
                comp_list=bottom_up

            for comp in comp_list:
                getattr(uvm_component.component_dict[comp],method)()

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
    def __init__(self):
        super().__init__()
        self.__is_active=False


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
        assert(isinstance(is_active,bool))
        self.__is_active=is_active

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

class uvm_driver(uvm_component):
    """
    13.7
    
    The pyuvm driver implementation differs from the SystemVerilog
    UVM implementation is several respects.
    
    First, there is no need to paramterize the sequence items
    going through the driver.  Python uses dynamic duck-typing,
    so there is no need to ensure that all elements of the driver
    correctly declare their variables.
    
    Second, Python provides the Queue class that does everything
    that UVM TLM does.  So rather than reinvent, or wrap, the wheel
    we will just use Python Queue objects to control our
    sequence item flow.
    
    We will have a property named sequence_item_port but
    it will be a Queue.
    
    Our sequence_item_port will NOT return a response back. Generally
    we want to encourge using the object handles as the method of 
    transfer.  But there is a rsp_port for those who insist.
    """

    def __init__(self):
        super().__init__()
        self.__sequence_item_port=None
        self.__rsp_port=None

    @property
    def sequence_item_port(self):
        return self.__sequence_item_port

    @sequence_item_port.setter
    def sequence_item_port(self,port):
        assert(isinstance(port, Queue))
        self.__sequence_item_port=port

    @property
    def rsp_port(self):
        return self.__rsp_port

    @rsp_port.setter
    def rsp_port(self, port):
        assert(isinstance(port,Queue))
        self.__rsp_port=port

"""
13.8 uvm_push_driver

Never seen one used. Not implemented.
"""

class uvm_subscriber(uvm_component):
    """
    13.9
    """






