import pyuvm.utility_classes as utility_classes
import pyuvm.error_classes as error_classes
import logging
import fnmatch


# pyuvm refactors the factory, taking advantage Python's
# superiority in terms of OOP features and lack of types.

# Implementing section 8 in the IEEE Specification
# The IEEE spec assumes that UVM is being written in SystemVerilog,
# a language that does not allow you to control how classes get defined.
# Python has more control in this area. With Python we can set things up
# so that any class that extends uvm_void automatically gets registered
# into the factory.

# Therefore there is no need for 8.2.2 the type_id, that
# is a SystemVerilog artifact as is 8.2.3
# There is also no need for 8.2.4, the uvm_object_registry.
# The FactoryMeta class causes all classes from uvm_void
# down to automatically register themselves with the factory
# by copying themselves into a dict.

# However there is a need to provide the methods in 8.


# 8.3.1.1
class uvm_factory(metaclass=utility_classes.Singleton):
    """
    The uvm_factory is a singleton that delivers all factory functions.
    """

    # 8.3.1.2.1 get
    # There is no get() method in Python singletons.  Instead you instantiate
    # the singleton as normal and you automatically get the singleton.

    # 8.3.1.3 register
    # Not implemented
    # There is no register in pyuvm.  Instead the factory builds its class
    # database through introspection.

    def __init__(self):
        self.fd = utility_classes.FactoryData()
        self.logger = logging.getLogger("Factory")
        self.debug_level = 1

    def clear_all(self):
        self.fd.clear_classes()
        self.clear_overrides()

    def clear_overrides(self):
        self.fd.clear_overrides()

    def __set_override(self, original, override, path=None):
        if original not in self.fd.overrides:
            self.fd.overrides[original] = utility_classes.Override()
        self.fd.overrides[original].add(override, path)

    # 8.3.1.3
    def set_inst_override_by_type(self, original_type, override_type,
                                  full_inst_path):
        """
        Override an instance with a new type if original type is at that path
        :param original_type: The original type being overridden
        :param override_type: The overriding type
        :param full_inst_path: The inst where this happens.
        """

        # The intention here is to only override when a type of original_type
        # is at the full_inst_path provided. If someone stores a different
        # class at full_inst_path then the override will not happen.
        #
        #
        # We capture this by storing the original and override types as a
        # tuple at the full inst path.  Later we'll retrieve the tuple
        # and check the type of the object at the full_inst_path.
        #
        # instance_overrides is an OrderedDict, so we will check
        # the paths in the order they are registered later.

        assert issubclass(original_type, utility_classes.uvm_void),\
            "You tried to override a non-uvm_void class"
        assert issubclass(override_type,
                          utility_classes.uvm_void),\
            "You tried to use a non-uvm_void class as an override"
        self.__set_override(original_type, override_type, full_inst_path)

    # 8.3.1.4.1
    def set_inst_override_by_name(self, original_type_name,
                                  override_type_name, full_inst_path):
        """
        Override a specific instance  using strings that contain
        the names of the types.
        :param original_type_name: the name of type being replaced
        :param override_type_name: the name of the substitute type
        :param full_inst_path: The path to the instance
        :return:
        """

        # Here we use the names of classes instead of the classes.
        # The original_name doesn't need to be the name of a class,
        # it can be an arbitrary string. The override_name must
        # be the name of a class.
        #
        # Later we will retrieve this by searching through the
        # keys for a match to a path and then checking that
        # the name given in the search matches the original_name

        assert isinstance(full_inst_path, str), \
            "The inst_path must be a string"
        assert isinstance(original_type_name, str), \
            "Original_name must be a string"
        assert isinstance(override_type_name, str), \
            "Override_name must be a string"
        try:
            override_type = self.fd.classes[override_type_name]
        except KeyError:
            raise error_classes.UVMFactoryError(
                f"{override_type_name}" + " has not been defined.")

        # Set type override by name can use an arbitrary string as a key
        # instead of a type. Fortunately Python dicts don't care about
        # the type of the key.
        try:
            original_type = self.fd.classes[original_type_name]
        except KeyError:
            original_type = original_type_name

        self.__set_override(original_type, override_type, full_inst_path)

    # 8.3.1.4.2
    def set_type_override_by_type(self, original_type, override_type,
                                  replace=True):
        """
        Override one type with another type globally
        :param original_type: The original type to be overridden
        :param override_type: The new type that will override it
        :param replace: If the override exists, only replace it if this is True
        """
        assert issubclass(original_type, utility_classes.uvm_void),\
            "You tried to override a non-uvm_void class"
        assert issubclass(override_type,
                          utility_classes.uvm_void),\
            "You tried to use a non-uvm_void class as an override"
        if (original_type not in self.fd.overrides) or replace:
            self.__set_override(original_type, override_type)

    # 8.3.1.4.2
    def set_type_override_by_name(self, original_type_name,
                                  override_type_name, replace=True):
        """
        Override one type with another type globally using strings
        containing the type names.

        :param original_type_name: The name of the type to be
        overridden or an arbitrary string.
        :param override_type_name: The name of the overriding type.
        It must have been declared.
        :param replace: If the override already exists only
        replace if this is True
        :return:
        """
        assert isinstance(original_type_name, str),\
            "Original_name must be a string"
        assert isinstance(override_type_name, str),\
            "Override_name must be a string"
        try:
            override_type = self.fd.classes[override_type_name]
        except KeyError:
            raise error_classes.UVMFactoryError(
                f"{override_type_name}" + " has not been defined.")

        # Set type override by name can use an arbitrary string as a key
        # instead of a type

        # Fortunately Python dicts don't care about the type of the key.
        try:
            original_type = self.fd.classes[original_type_name]
        except KeyError:
            original_type = original_type_name

        if (original_type not in self.fd.overrides) or replace:
            self.__set_override(original_type, override_type)

    def __find_override(self, requested_type, parent_inst_path="", name=""):
        """
        An internal function that finds overrides

        :param requested_type: The type that could be overridden
        :param parent_inst_path: The parent inst path for an override
        :param name: The name of the object, concatenated with parent
        inst path for override
        :return: either the requested_type or its override
        """
        if not isinstance(requested_type, str):
            assert (issubclass(requested_type, utility_classes.uvm_void)), \
                f"You must create uvm_void descendants not {requested_type}"

        if parent_inst_path == "":
            inst_path = name
        elif name != "":
            inst_path = parent_inst_path + "." + name
        else:
            inst_path = parent_inst_path

        new_cls = self.fd.find_override(requested_type, inst_path)
        if isinstance(new_cls, str):
            self.logger.error(
                f'"{new_cls}" is not declared and is not an override string')
            return None
        else:
            return new_cls

    def create_object_by_type(self, requested_type, parent_inst_path="",
                              name=""):
        """
        8.3.1.5 Creation
        :param requested_type: The type that we request but that can be
        overridden
        :param parent_inst_path: The get_full_name path of the parent
        :param name: The name of the instance requested_type("name")
        :return: Type that is child of uvm_object.
        If the type is is not in the factory we raise UVMFactoryError
        """
        new_type = self.__find_override(requested_type, parent_inst_path, name)
        if new_type is None:
            raise error_classes.UVMFactoryError(
                f"{requested_type} not in uvm_factory()")
        return new_type(name)

    # 8.3.1.5
    def create_object_by_name(self, requested_type_name,
                              parent_inst_path="", name=""):
        """
        Create an object using a string to define its uvm_object type.

        :param requested_type_name: the type that could be overridden
        :param parent_inst_path: A path if we are checking for inst overrides
        :param name: The name of the new object.
        :return: A uvm_object with the name given
        """
        try:
            requested_type = utility_classes.FactoryData().classes[requested_type_name] # noqa
        except KeyError:
            requested_type = requested_type_name

        new_obj = self.create_object_by_type(requested_type, parent_inst_path,
                                             name)
        return new_obj

    # 8.3.1.5
    def create_component_by_type(self, requested_type, parent_inst_path="",
                                 name="", parent=None):
        """
        Create a component of the requested uvm_component type.

        :param requested_type: Type type to be overridden
        :param parent_inst_path: The inst path if we are looking
        for inst overrides
        :param name: Concatenated with parent_inst_path if it
        exists for inst overrides
        :param parent: The parent component
        :return: a uvm_component with the name an parent given.

        If the type is is not in the factory we raise UVMFactoryError
        """

        if name is None:
            raise error_classes.UVMFactoryError(
                "Parameter name must be specified in function call.")

        new_type = self.__find_override(requested_type, parent_inst_path, name)

        if new_type is None:
            raise error_classes.UVMFactoryError(
                f"{requested_type} not in uvm_factory()")

        new_comp = new_type(name, parent)
        return new_comp

    # 8.3.1.5
    def create_component_by_name(self, requested_type_name,
                                 parent_inst_path="", name="", parent=None):
        """
        Create a components using the name of the requested uvm_component type

        :param requested_type_name: the type that could be overridden
        :param parent_inst_path: A path if we are checking for inst overrides
        :param name: The name of the new object.
        :param parent: The component's parent component
        :return: A uvm_object with the name given
        """
        if name is None:
            raise error_classes.UVMFactoryError(
                "Parameter name must be specified in create_component_by_name")

        try:
            requested_type = utility_classes.FactoryData().classes[requested_type_name]  # noqa
        except KeyError:
            requested_type = requested_type_name

        new_obj = self.create_component_by_type(requested_type,
                                                parent_inst_path,
                                                name, parent)
        return new_obj

    # 8.3.1.6.1
    def set_type_alias(self, alias_type_name, original_type):
        """
        Not implemented as it does not seem to exist in SystemVerilog UVM

        :param alias_type_name:A string that will reference the original type
        :param original_type:The original type toe be referenced
        :return:None
        """
        # This method does not seem to be implemented in SystemVerilog
        # so I'm skipping it now.
        raise error_classes.UVMNotImplemented(
            "set_type_alias is not implemented in SystemVerilog")

    # 8.3.1.6.2
    def set_inst_alias(self, alias_type_name, original_type, full_inst_path):
        """
        Not implemented as it does not seem to exist in SystemVerilog UVM

        :param alias_type_name:A string that will reference the original type
        :param original_type:The original type toe be referenced
        :param full_inst_path: The instance path where this alias is active
        :return:None
        """
        # This method does not seem to be implemented in SystemVerilog
        # so I'm skipping it now.
        raise error_classes.UVMNotImplemented(
            "set_type_inst is not implemented in SystemVerilog")

    # 8.3.1.7 Introspection

    # 8.3.1.7.1
    def find_override_by_type(self, requested_type, full_inst_path):
        """
        Given a type and instance path, return the override class object.

        :param requested_type: The type whose override you want
        :param full_inst_path: The inst path where one looks
        :return: class object
        """
        override = self.__find_override(requested_type, full_inst_path)
        return override

    # 8.3.1.7.1
    def find_override_by_name(self, requested_type_name, full_inst_path):
        """
        Given a path and the name of a class return its overriding class object

        :param requested_type_name:
        :param full_inst_path:
        :return: class object
        """
        assert (isinstance(requested_type_name, str)), \
            f"requested_type_name must be a string not a {type(requested_type_name)}"  # noqa
        requested_type = None  # Appeasing the linter
        try:
            requested_type = self.fd.classes[requested_type_name]
        except KeyError:
            error_classes.UVMFactoryError(
                f"{requested_type_name} is not a defined class name")
        return self.find_override_by_type(requested_type, full_inst_path)

    # 8.3.1.7.2
    def find_wrapper_by_name(self):
        """
        There are no wrappers in pyuvm so this is not implemented.
        """
        raise error_classes.UVMNotImplemented(
            "There are no wrappers in pyuvm. "
            "So find_wrapper_by_name is not implemented")

    # 8.3.1.7.3
    def is_type_name_registered(self, type_name):
        """
        Checks that a type of this name is registered with the factory.

        :param type_name: string that is name of a type
        :return: boolean
        """
        assert (isinstance(type_name, str)), \
            ("is_type_name_registered() takes a"
             " string as its argument not {type(type_name)}")
        return type_name in self.fd.classes

    # 8.3.1.7.4
    def is_type_registered(self, uvm_type):
        """
        Checks that a type is registered. The argument is named "obj" in
        the spec, but that name is ridiculous and confusing.

        :param uvm_type: The type to be checked
        :return: boolean
        """
        assert (issubclass(uvm_type, utility_classes.uvm_void)), \
            ("is_type_registered() takes a subclass of uvm_void "
             "as its argument not {type(uvm_type)}")
        return uvm_type in self.fd.classes.values()

    @property
    def debug_level(self):
        """
        uvm_factory().debug_level = 0 : overrides
        uvm_factory().debug_level = 1 : user defined types + above
        uvm_factory().debug_level = 2 : uvm_* types + above
        """
        return self.__debug_level

    @debug_level.setter
    def debug_level(self, debug_level):
        """
        uvm_factory().debug_level = 0 : overrides
        uvm_factory().debug_level = 1 : user defined types + above
        uvm_factory().debug_level = 2 : uvm_* types + above
        """
        assert (0 <= debug_level <= 2), \
            "uvm_factory().all_type must be 0, 1, or 2"
        self.__debug_level = debug_level

    def __str__(self):
        """
        Returns the Pythonic string
        Set uvm_factory().debug_level to a value to control the string.
        The default is 1

        uvm_factory().debug_level = 0 : overrides
        uvm_factory().debug_level = 1 : user defined types + above
        uvm_factory().debug_level = 2 : uvm_* types + above

        :return: String containing factory data
        """
        factory_str = "--- overrides "
        if self.debug_level != 0:
            factory_str += "+ user defined types "
        if self.debug_level == 2:
            factory_str += "+ uvm_* types "
        factory_str += "---\n\n"

        if len(self.fd.overrides) > 0:
            factory_str += "Overrides:\n"
            for inst in self.fd.overrides:
                factory_str += f"{inst.__name__:25}" + ": " + str(self.fd.overrides[inst])  # noqa
                factory_str += "\n"
        # Need to add 1 and 2
        user_list = [self.fd.classes[cls].__name__
                     for cls in self.fd.classes
                     if not fnmatch.fnmatch(self.fd.classes[cls].__name__, "uvm_*")]  # noqa
        uvm_list = [self.fd.classes[cls].__name__
                    for cls in self.fd.classes
                    if fnmatch.fnmatch(self.fd.classes[cls].__name__, "uvm_*")]
        if self.debug_level > 0:
            factory_str += "\n" + "-" * 25 + "\nUser Defined Types:\n"
            factory_str += "\n".join(user_list)

        if self.debug_level == 2:
            factory_str += "\n" + "-" * 25 + "\nUVM Types:\n"
            factory_str += "\n".join(uvm_list)

        return factory_str

    # 8.3.1.7.5
    def print(self, debug_level=1):
        """
        Prints the factory data using debug_level to
        control the amount of output. The uvm_factory().debug_level
        variable can control this for __str__()

        debug_level = 0 : overrides
        debug_level = 1 : user defined types + above
        debug_level = 2 : uvm_* types + above

        :return: None
        """
        saved_debug_level = self.debug_level  # Avoiding a side effect
        self.debug_level = debug_level
        print(self)
        self.debug_level = saved_debug_level

# 8.3.1.8 Usage
# All the elements of usage have been implemented in pyuvm
# The biggest difference is that all uvm_void classes get registered
# with the factory automatically.

# 8.3.2
# Not implemented.  There is no need for a uvm_object_wrapper
# in Python. The user will never notice
# the difference
