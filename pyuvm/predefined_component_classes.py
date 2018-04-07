from base_classes import *
from queue import Queue

'''
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

'''

# Class Declarations

class uvm_component(uvm_object):
    '''
The specification calls for uvm_component to extend uvm_report_object. However, pyuvm
uses the logging module orthogonally to class structure. It may be that in future
we find a reason to wrap the basic logging package in the uvm code, but at this point
we are better off leaving logging to itself.

The choice then becomes whether to create a uvm_report_object class as a placeholder
to preserve the UVM reference manual hierarchy or to code what is really going on.
We've opted for the latter.
    '''
    def __init__(self, name, parent):
        '''
        :param name: A string with the name of the object.
        :param parent: The parent in the UVM hierarchy.


        13.1.2.1---This is new() in the IEEE-UVM, but we mean
        the same thing with __init__()
        '''

        component_dict={}

        super().__init__(name)
        self.__parent = None
        self.__children={}
        self.parent = parent
        self.print_enabled=True #13.1.2.2

        # Cache the hierarchy for easy access
        uvm_component.component_dict[self.full_name]=self

        @property
        def parent(self):
            '''
            :return: parent object
            13.1.3.1--- No 'get_' prefix
            '''
            assert(self.__parent != None)
            return self.__parent

        @parent.setter
        def parent(self, parent):
            assert(issubclass(parent,uvm_component))
            self.__parent=parent

        @property
        def full_name(self):
            '''
            :return: Name concatenated to parent name.
            13.1.3.2
            '''
            return f'{self.parent.full_name}.{self.name}'
        '''
        # Children in pyuvm
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
        '''
        @property
        def children(self):
            '''
            13.1.3.3
            :return: dict with children
            '''
            return self.__children

        def __iter__(self):
            '''
            13.1.3.4
            Implements the intention of this requirement
            without the approach taken in the UVM
            '''
            for childname in self.children:
                yield self.__children[childname]

        def get_child(self, name):
            '''
            13.1.3.4
            :param self:
            :param name: child string
            :return: uvm_component of that name
            '''
            assert(isinstance(name, str))
            return self.__children[name]

        def get_num_children(self):
            '''
            13.1.3.5
            :param self:
            :return: Number of children in component
            '''
            return len(self.__children)

        def has_child(self, name):
            '''
            13.1.3.6
            :param self:
            :param name: Name of child object
            :return: True if exists, False otherwise
            '''
            assert(isinstance(name,str))
            return name in self.children

        def lookup(self, name):
            '''
            13.1.3.7
            Return a component base on the path. If . then
            use full name from root otherwise relative
            :param name: The search name
            :return: either the component or None
            '''
            assert(name,str)
            if name[0] == '.':
                lookup_name=name
            else:
                lookup_name=f'{self.full_name}.{name}'
            try:
                return uvm_component.component_dict[lookup_name]
            except KeyError:
                return None


        def get_depth(self):
            '''
            13.1.3.8
            Get the depth that I am from the top component.
            :param self: That's me
            :return: depth
            '''
            # Rather than getting all recursive just count
            # levels in the full name.
            return len(self.full_name.split("."))-1

        '''
        Phasing Interface 13.1.4
        We are only implementing the basic phases.  Fancy user-defined phasing could be added
        at a later time.
        
        One note. The SystemVerilog UVM uses virtual methods for phases.
        This is unnecessary in Python. Duck typing means that the variable has only
        the type of the object in it.
        
        Therefore we do not implement the phases using the virtual method approach.
        
        '''

        def build_phase(self):
            '''
            13.1.4.1.1
            :param self:
            :return: None
            '''
            pass

        def connect_phase(self):
            '''
            13.1.4.1.2
            :param self:
            :return: None
            '''
            pass

        def end_of_elaboration_phase(self):
            '''
            13.1.4.1.3
            :param self:
            :return: None
            '''


        def start_of_simulaiton_phase(self):
            '''
            13.1.4.1.4
            :param self:
            :return: None
            '''
            pass

        def run_phase(self):
            '''
            13.1.4.1.5
            :param self:
            :return: None
            '''
            pass

        def extract_phase(self):
            '''
            13.1.4.1.6
            :param self:
            :return: None
            '''
            pass

        def check_phase(self):
            '''
            13.1.4.1.7
            :param self:
            :return: None
            '''
            pass

        def report_phase(self):
            '''
            13.1.4.1.8
            :param self:
            :return: None
            '''
            pass

        def final_phase(self):
            '''
            13.1.4.1.9
            :param self:
            :return: None
            '''
            pass

        '''
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
        '''

class uvm_test(uvm_component):
    '''
    13.2
    The base class for all user-defined tests

    Python does not require that we override new() for every
    UVM class, so we don't do that (same for __init__).
    '''


class uvm_env(uvm_component):
    '''
    13.3
    The user's containes for agents and what-not
    '''


class uvm_agent(uvm_component):
    '''
    13.4
    Contains controls for individual agents
    '''
    def __init__(self):
        super().__init__()
        self.__is_active=False


    '''
    Have chosen to implement the spirit of 
    the is_active member rather than the 
    enum-based implementation.
    '''
    @property
    def is_active(self):
        return self.__is_active
    @is_active.setter
    def is_active(self, is_active):
        assert(is_active,bool)
        self.__is_active=is_active

class uvm_monitor(uvm_component):
    '''
    13.5
    We'll see if anything is ever added
    to uvm_monitor
    '''

class uvm_scoreboard(uvm_component):
    '''
    13.6
    '''

class uvm_driver(uvm_component):
    '''
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
    '''

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

'''
13.8 uvm_push_driver

Never seen one used. Not implemented.
'''

class uvm_subscriber(uvm_component):
    '''
    13.9
    '''






