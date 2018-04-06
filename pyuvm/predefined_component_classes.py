from base_classes import *

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
        super().__init__(name)
        self.__parent = None
        self.__children={}
        self.parent = parent
        self.print_enabled=True #13.1.2.2

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








