from pyuvm.s06_reporting_classes import uvm_report_object
from pyuvm.s08_factory_classes import uvm_factory
from pyuvm.s09_phasing import uvm_common_phases, uvm_run_phase
from pyuvm import error_classes
from pyuvm import utility_classes
import time


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

    @classmethod
    def clear_components(cls):
        cls.component_dict = {}

    def __init__(self, name, parent=None):
        """
        13.1.2.1---This is new() in the IEEE-UVM, but we mean
        the same thing with __init__()
        """

        super().__init__(name)
        self.__parent = None
        self.__children = {}
        if parent == None and name != 'uvm_root':
            parent = uvm_root()
        self.parent = parent
        if parent != None:
            parent.add_child(name, self)
        self.print_enabled = True  # 13.1.2.2

        # Cache the hierarchy for easy access
        if name != 'uvm_root':
            uvm_component.component_dict[self.get_full_name()] = self

    def clear_children(self):
        self.__children = {}

    def clear_hierarchy(self):
        self.__parent = None
        self.clear_children()

    def do_execute_op(self, op):
        raise error_classes.UVMNotImplemented("Policies not implemented")

    def create_component(self, type_name, name):
        new_comp = uvm_factory().create_component_by_name(type_name, self.get_full_name(), name, self)
        return new_comp

    def get_parent(self):
        """
        :return: parent object
        13.1.3.1--- No 'get_' prefix
        """
        return self.__parent

    def raise_objection(self):
        utility_classes.ObjectionHandler().raise_objection(self)

    def drop_objection(self):
        utility_classes.ObjectionHandler().drop_objection(self)

    def config_db_set(self, item, label, inst_path=None):
        """
        Store an object in the config_db.

        :param item: The object to store
        :param label: The label to use to retrieve it
        :param inst_path: A path with globs or if left blank the get_full_name() path
        """
        if inst_path is None:
            inst_path = self.get_full_name()

        utility_classes.ConfigDB().set(item, label, inst_path)

    def config_db_get(self, label):
        """
        Retrieve an object from the config_db using this compnents
        get_full_name() path. Can find objects stored with wildcards

        :param label: The label to use to retrieve the object
        :return: The object at this path stored at the label
        """
        datum = utility_classes.ConfigDB().get(label, self.get_full_name())
        return datum

    @property
    def parent(self):
        return self.get_parent()

    @parent.setter
    def parent(self, parent):
        if parent != None:
            assert (isinstance(parent, uvm_component)), f" {parent} is of type {type(parent)}"
        assert (parent != self), f'Cannot make a {self.get_name()} its own parent.  That is incest.'
        self.__parent = parent

    def get_full_name(self):
        """
        :return: Name concatenated to parent name.
        13.1.3.2
        """
        if self.get_name() == 'uvm_root':
            return ''
        fullname = self.__parent.get_full_name()
        if len(fullname) == 0:
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
        assert (name not in self.__children), f"{self.get_full_name()} already has a child named {name}"
        self.__children[name] = child
        pass

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
                assert isinstance(grandchild, uvm_component, )
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
        assert (isinstance(name, str))
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
        assert (isinstance(name, str))
        return name in self.__children

    def lookup(self, name):
        """
        13.1.3.7
        Return a component base on the path. If . then
        use full name from root otherwise relative
        :param name: The search name
        :return: either the component or None
        """
        assert (isinstance(name, str))
        if name[0] == '.':
            lookup_name = name[1:]
        else:
            lookup_name = f'{self.get_full_name()}.{name}'
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

    def build_phase(self):
        ...

    def connect_phase(self):
        ...

    def end_of_elaboration_phase(self):
        ...

    def start_of_simulation_phase(self):
        ...

    def run_phase(self):
        ...

    def extract_phase(self):
        ...

    def check_phase(self):
        ...

    def report_phase(self):
        ...

    def final_phase(self):
        ...

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

    @classmethod
    def clear_singletons(cls):
        cls.singleton = None

    def __init__(self):
        super().__init__("uvm_root", None)
        self.uvm_test_top = None

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

        factory = uvm_factory()
        self.uvm_test_top = factory.create_component_by_name(test_name, "", "uvm_test_top", self)
        for phase in uvm_common_phases:
            phase.traverse(self.uvm_test_top)
            if phase == uvm_run_phase:
                time.sleep(.1)
                run_cond = utility_classes.ObjectionHandler().run_condition
                run_over = utility_classes.ObjectionHandler().run_phase_complete
                with run_cond:
                    run_cond.wait_for(run_over)
        time.sleep(1)
        pass









