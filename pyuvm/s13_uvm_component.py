import fnmatch
import logging
import string

from pyuvm import INFO, error_classes, utility_classes
from pyuvm._utils import cocotb_version_info
from pyuvm.s06_reporting_classes import uvm_report_object
from pyuvm.s08_factory_classes import uvm_factory
from pyuvm.s09_phasing import uvm_build_phase, uvm_common_phases, uvm_run_phase

if cocotb_version_info < (2, 0):
    from cocotb.log import SimColourLogFormatter, SimTimeContextFilter
else:
    from cocotb.logging import SimColourLogFormatter, SimTimeContextFilter


# 13.1.1
class uvm_component(uvm_report_object):
    component_dict = {}

    @classmethod
    def clear_components(cls):
        cls.component_dict = {}

    def __init__(self, name, parent):
        """
        13.1.2.1---This is new() in the IEEE-UVM, but we mean
        the same thing with __init__()

        :param name: The name of the component. Used in the UVM hierarchy
        :param parent: The parent component.  If None, the parent is uvm_root
        """

        self._children = {}
        if parent is None and name != 'uvm_root':
            parent = uvm_root()
        self.parent = parent
        if parent is not None:
            parent.add_child(name, self)
        self.print_enabled = True  # 13.1.2.2
        super().__init__(name)

        # Cache the hierarchy for easy access
        if name != 'uvm_root':
            uvm_component.component_dict[self.get_full_name()] = self

    def clear_children(self):
        """
        Removes the direct children from this component.
        """
        self._children = {}

    def clear_hierarchy(self):
        """
        Removes self from the UVM hierarchy
        """
        self._parent = None
        self.clear_children()

    def do_execute_op(self, op):
        raise error_classes.UVMNotImplemented("Policies not implemented")

    @classmethod
    def create(cls, name="", parent=None):
        if parent is None:
            parent_inst_path = ""
        else:
            parent_inst_path = parent.get_full_name()

        new_comp = uvm_factory().create_component_by_type(
            cls, parent_inst_path=parent_inst_path,
            name=name, parent=parent)
        return new_comp

    def get_parent(self):
        """
        :return: parent object

        13.1.3.1
        """
        return self._parent

    def raise_objection(self):
        """
        Raise an objection, usually at the start of the ``run_phase()``
        """
        utility_classes.ObjectionHandler().raise_objection(self)

    def drop_objection(self):
        """
        Drop an objection, usually at the end of the ``run_phase()``
        """
        utility_classes.ObjectionHandler().drop_objection(self)

    def objection(self):
        class Objection:
            def __init__(self, component):
                self.component = component

            def __enter__(self):
                return self.component.raise_objection()

            def __exit__(self, *args):
                return self.component.drop_objection()

        return Objection(self)

    def cdb_set(self, label, value, inst_path="*"):
        """
        A convenience routing to store an object in the config_db using
        this component's ``get_full_name()`` path.

        :param value: The object to store
        :param label: The label to use to retrieve it
        :param inst_path: A path with globs or if left blank
                          the get_full_name() path
        """

        ConfigDB().set(self, inst_path, label, value)

    def cdb_get(self, label, inst_path=""):
        """
        A convenience routine that retrieves an object from
        the config_db using this component's
        ``get_full_name()`` path. Can find objects stored with wildcards

        :param inst_path: The path below this component
        :param label: The label used to store the value
        :return: The object at this path stored at the label
        """
        datum = ConfigDB().get(self, inst_path, label)
        return datum

    @property
    def parent(self):
        return self.get_parent()

    @parent.setter
    def parent(self, parent):
        if parent is not None:
            assert (isinstance(parent, uvm_component)), \
                f" {parent} is of type {type(parent)}"
        assert (parent != self), \
            f'Cannot make a {self.get_name()} its own parent.  That is incest.'
        self._parent = parent

    def get_full_name(self):
        """
        :return: This component's name concatenated to parent name.

        13.1.3.2
        """
        if self.get_name() is None or self.get_name() == 'uvm_root':
            return ''
        if self._parent is None:
            fullname = ""
        else:
            fullname = self._parent.get_full_name()
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
        :return: A dict containing children objects
        """
        return list(self.children)

    def add_child(self, name, child):
        assert (name not in self._children), \
            f"{self.get_full_name()} already has a child named {name}"
        self._children[name] = child
        pass

    @property
    def hierarchy(self):
        """
        We return a generator to find the children.
        This is more pythonic and saves memory for large hierarchies.

        :return: A generator that returns the children.
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
        without the approach taken in the UVM  We use a
        generator instead.
        """
        for child in self._children:
            yield self._children[child]

    def __repr__(self):
        return self.get_full_name()

    def get_child(self, name):
        """
        13.1.3.4
        :param self:
        :param name: child's name
        :return: child ``uvm_component`` of that name
        """
        assert (isinstance(name, str))
        try:
            return self._children[name]
        except KeyError:
            return None

    def get_num_children(self):
        """
        13.1.3.5
        :param self:
        :return: The number of children in component

        """
        return len(self._children)

    def has_child(self, name):
        """
        13.1.3.6
        :param name: Name of child the object
        :return: True if exists, False otherwise

        """
        assert (isinstance(name, str))
        return name in self._children

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

        :return: The hierarchy depth from me to the bottom.
        """
        # Rather than getting all recursive just count
        # levels in the full name.
        fullname = self.get_full_name()
        if len(fullname) == 0:
            return 0
        else:
            return len(self.get_full_name().split("."))

    # noinspection SpellCheckingInspection
    def set_logging_level_hier(self, logging_level):
        """
        Set the logging level for this component's logger
        and all the way down the hierarchy

        :param logging_level: typically a constant from logging module
        :return: None

        """
        self.set_logging_level(logging_level)
        for child in self.children:
            child.set_logging_level_hier(logging_level)

    def add_logging_handler_hier(self, handler):
        """
        Add an additional handler all the way down the component hierarchy

        :param handler: A logging.Handler object
        :return: None
        """
        assert isinstance(handler, logging.Handler), \
            f"You can only add logging.Handler objects not {type(handler)}"
        self.add_logging_handler(handler)
        for child in self.children:
            child.add_logging_handler_hier(handler)

    def remove_logging_handler_hier(self, handler):
        """
        Remove a handler from all loggers below this component

        :param handler: logging handler
        :return: None
        """
        assert isinstance(handler, logging.Handler), \
            f"You must pass a logging.Handler not {type(handler)}"
        self.logger.removeHandler(handler)
        for child in self.children:
            child.remove_logging_handler_hier(handler)

    def remove_streaming_handler_hier(self):
        """
        Remove this component's streaming handler and all the way down
        the hierarchy
        """
        self.remove_streaming_handler()
        for child in self.children:
            child.remove_streaming_handler_hier()

    def disable_logging_hier(self):
        """
        Disable logging for this component and all the way down the hierarchy
        """
        self.disable_logging()
        for child in self.children:
            child.disable_logging_hier()

    def build_phase(self):
        ...

    def connect_phase(self):
        ...

    def end_of_elaboration_phase(self):
        ...

    def start_of_simulation_phase(self):
        ...

    async def run_phase(self):
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
    13.1.5--Configuration interface
    13.1.6--Recording interface
    13.1.7--Other interfaces
    """


# 13.2 (rest of 13.2 is in s13_predefined_components)
class uvm_test(uvm_component):
    """
    The base class for all tests
    """


class uvm_root(uvm_component, metaclass=utility_classes.UVM_ROOT_Singleton):
    """
    F.7.  We do not use ``uvm_pkg`` to hold ``uvm_root``.  Instead it
    is a class variable of uvm_component.  This avoids
    circular reference issues regarding uvm_pkg.

    Plus, it's cleaner.

    ``uvm_root`` is still a singleton that you access through its
    constructor instead of through a ``get()`` method.

    Much of the functionality in Annex F delivers functionality
    in SystemVerilog that is already built into Python. So we're
    going to skip much of that Annex.
    """

    @classmethod
    def clear_singletons(cls, keep_set={}):
        """
        Clear the singletons in the system.  This is used for testing
        """
        keepers = {uvm_factory, utility_classes.FactoryData}.union(keep_set)
        utility_classes.Singleton.clear_singletons(keep=keepers)

    def __init__(self):
        super().__init__("uvm_root", None)
        self.uvm_test_top = None
        self.running_phase = None

    def _utt(self):
        """Used in testing"""
        return self.get_child("uvm_test_top")

# This implementation skips much of the state-setting and
# what not in the LRM and focuses on building the
# hierarchy and running the test.

# At this time pyuvm has not implemented the phasing
# system described in the LRM.  It's not clear that anyone
# is using it, and in fact it is recommended that people
# stick to the basic phases.  So this implementation loops
# through the hierarchy and runs the phases.
    async def run_test(self, test_name,
                       keep_singletons=False, keep_set=set()):
        """
        :param test_name: The uvm test name or test class
        :param keep_singletons: If True do not clear singletons (default False)
        :param keep_set: Set of singleton classes to keep
            if keep_singletons is False. Pass a list of singletons to `set()`
        :return: none
        """
        factory = uvm_factory()
        if not keep_singletons:
            uvm_report_object.set_default_logging_level(INFO)
            self.clear_singletons(keep_set)
            factory.clear_overrides()
        self.clear_children()
        utility_classes.ObjectionHandler().clear()
        self.uvm_test_top = factory.create_component_by_name(
            test_name, "", "uvm_test_top", self)
        for self.running_phase in uvm_common_phases:
            self.logger.log(utility_classes.PYUVM_DEBUG,
                            str(self.running_phase))
            self.running_phase.traverse(self.uvm_test_top)
            if self.running_phase == uvm_run_phase:
                await utility_classes.ObjectionHandler().run_phase_complete()  # noqa: E501


# In the SystemVerilog UVM the uvm_config_db is a
# convenience layer on top of the much more complicated
# uvm_resource_db class. However, few people
# use the uvm_resource_db and in fact, Mentor recommends
# that people use the uvm_config_db interface.
#
# Therefore pyuvm implements only the behavior of
# the ConfigDB. It also does NOT implement the
# regular expression form of wildcards, which are
# also rarely used. Instead it implements globbing
# as defined by fnmatch().
#
# To avoid confusion with the full uvm_config_db
# our class is named ConfigDB.


class ConfigDB(metaclass=utility_classes.Singleton):
    default_get = object()
    default_precedence = 1000
    legal_chars = set(string.ascii_letters) | set(string.digits) | set("_.")
    """
    A path-based singleton storage system
    """

    # The ConfigDB is a dual-level dict. The outer dict is a
    # GlobPathDict that can store globs in keys that match
    # later retrievals. Each entry contains another dict
    # that stores items by keys.
    #
    # Unlike the UVM config_db, this config_db makes no effort
    # to store multiple items at one location. The last stored
    # wins
    #
    # Also, pyuvm does not support wildcards in the field names
    # at this time.

    def __init__(self):
        self.logger_holder = uvm_report_object("logger_holder")
        self.logger_holder.remove_streaming_handler()
        configdb_handler = logging.StreamHandler()
        configdb_handler.addFilter(SimTimeContextFilter())
        # Don't let the handler interfere with logger level
        configdb_handler.setLevel(logging.NOTSET)
        # Make log messages look like UVM messages
        configdb_formatter = SimColourLogFormatter()
        configdb_handler.setFormatter(configdb_formatter)
        self.logger_holder.add_logging_handler(configdb_handler)
        self.logger_holder.logger.propagate = False
        self._path_dict = {}
        self.is_tracing = False
        self._cond_dict = {}

    def clear(self):
        """Reset the ConfigDB. Used for testing."""
        if self.is_tracing:
            self.logger_holder.logger.info("CFGDB/CLEAR: Clearing ConfigDB()")
        self._path_dict = {}

    @staticmethod
    def _get_context_inst_name(context, inst_name):
        """
        Get the config_key from context and passed inst_name

        :param context: uvm_component or None
        :param inst_name: string that can be a glob
        :return: string that is the key

        """
        assert context is None or isinstance(context, uvm_component), \
            "config_db context must be None or a uvm_component. "
        f"Not {type(context)}"
        if context is None:
            context = uvm_root()

        if inst_name is None or inst_name == "":
            inst_name = context.get_full_name()
        elif context.get_full_name() != "":
            inst_name = context.get_full_name() + "." + inst_name
        return context, inst_name

    def trace(self, method, context, inst_name, field_name, value):
        """
        Output the ConfigDB activity if tracing is on.
        """
        if self.is_tracing:
            # noinspection SpellCheckingInspection
            self.logger_holder.logger.info(f"CFGDB/{method} Context: {context}  --  {inst_name} {field_name}={value}")  # noqa: E501

    def set(self, context, inst_name, field_name, value):
        """
        Stores an object in the db using the context and
        inst_name to create a retrieval path, and the key
        name.

        :param context: A handle to a component
        :param inst_name: The instance name within the component
        :param field_name: The key we're setting
        :param value: The object to be stored
        :return: None

        """

        if not set(field_name).issubset(self.legal_chars):
            raise error_classes.UVMNotImplemented(
                f"pyuvm does not allow wildcards in key names ({field_name})"
            )

        context, inst_name = self._get_context_inst_name(context, inst_name)

        if inst_name not in self._path_dict:
            self._path_dict[inst_name] = {}

        if field_name not in self._path_dict[inst_name]:
            self._path_dict[inst_name][field_name] = {}

        precedence = self.default_precedence
        if uvm_root().running_phase is uvm_build_phase:
            precedence = self.default_precedence - context.get_depth()

        self._path_dict[inst_name][field_name][precedence] = value

        self.trace("SET", context, inst_name, field_name, value)

    def get(self, context, inst_name, field_name, default=default_get):
        """
        The component path matches against the paths in the ConfigDB. The path
        cannot have wildcards, but can match against keys with wildcards.
        Return the value stored at key. If the key is missing, returns default
        or raises ``UVMConfigItemNotFound``.

        :param context: The component making the call
        :param inst_name: component full path with no wildcards
        :param field_name: the field_name being retrieved
        :param default: the value to return if there is no key, defaults to
            default_get
        :raises UVMConfigItemNotFound: if the key is not found and the
        default is not set
        :return: value found at location

        """
        if not set(inst_name).issubset(self.legal_chars):
            raise error_classes.UVMError(
                f'"{inst_name}" is illegal: '
                f'inst_name wildcards only allowed when storing.')

        context, inst_name = self._get_context_inst_name(context, inst_name)

        try:
            key_matches = []  # Make the linter happy by setting this.
            try:
                # key_matches = [dk for dk in self._path_dict.keys()
                #                if fnmatch.fnmatch(inst_name, dk)]
                for dk in self._path_dict.keys():
                    if fnmatch.fnmatch(inst_name, dk):
                        key_matches.append(dk)

            except TypeError:
                raise error_classes.UVMConfigItemNotFound(
                    f'"{inst_name}" is not in ConfigDB().')
            finally:
                if len(key_matches) == 0:
                    raise error_classes.UVMConfigItemNotFound(
                        f'"{inst_name}" is not in ConfigDB().')
            # Here we sort the list of paths by which paths are "in" other
            # paths. That is A comes before '*'  A.B comes before A.*, etc.
            # We use an insertion sort. A path is inserted in front of the
            # first path it is "in"
            sorted_paths = []
            try:
                sorted_paths.append(key_matches.pop())
            except IndexError:
                raise error_classes.UVMConfigItemNotFound(
                    f"{inst_name} not in ConfigDB()")

            # Sort the matching keys from most specific to
            # most greedy. A.B.C before A.B.* before A.* before *
            for path in key_matches:
                inserted = False
                for ii in range(len(sorted_paths)):
                    if fnmatch.fnmatch(path, sorted_paths[ii]):
                        sorted_paths.insert(ii, path)
                        inserted = True
                        break
                if not inserted:
                    sorted_paths.append(path)
            value = None
            for path in sorted_paths:
                try:
                    component_fields = self._path_dict[path]
                    matching_path_fields = component_fields[field_name]
                    max_precedence = max(matching_path_fields.keys())
                    value = matching_path_fields[max_precedence]
                    break
                except KeyError:
                    pass
            if value is not None:
                self.trace("GET", context, inst_name, field_name, value)
                return value
            else:
                raise error_classes.UVMConfigItemNotFound(
                    f'"Component {inst_name} has no key: {field_name}')
        except error_classes.UVMConfigItemNotFound as e:
            if default is self.default_get:
                raise e
            return default

    def exists(self, context, inst_name, field_name):
        """
        Returns true if there is data in the database at this location

        :param context: None or uvm_component
        :param inst_name: instance name string in context
        :param field_name: key name for location
        :return: True if exists

        """
        try:
            _ = self.get(context, inst_name, field_name)
        except error_classes.UVMConfigItemNotFound:
            return False
        return True

    def wait_modified(self):
        """
        :raises UVMNotImplemented: This is not implemented in pyuvm
        """
        raise error_classes.UVMNotImplemented(
            "wait_modified not implemented pending requests for it.")

    def __str__(self):
        str_list = [f"\n{'PATH':20}: {'KEY':10}: {'DATA':30}"]
        for inst_path in self._path_dict:
            for key in self._path_dict[inst_path]:
                str_list.append(f"{inst_path:20}: {key:10}: {self._path_dict[inst_path][key]}")  # noqa: E501
        return "\n".join(str_list)
