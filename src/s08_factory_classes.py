import utility_classes
import error_classes
# from predefined_component_classes import uvm_object
from s13_predefined_component_classes import uvm_component


# Implementing section 8 in the IEEE Specification
# The IEEE spec assumes that UVM is being written in SystemVerilog,
# a language that does not allow you to control how classes get defined.
# Python has more control in this area. With Python we can set things up
# so that any class that extends uvm_void automatically gets registered
# into the factory.

# Therefore there is no need for 8.2.2 the type_id, that is a SystemVerilog artifact as is 8.2.3
# There is also no need for 8.2.4, the uvm_object_registry.  The FactoryMeta class causes
# all classes from uvm_void down to automatically register themselves with the factory
# by copying themselves into a dict.

# However there is a need to provide the methods in 8.



class uvm_factory(metaclass=utility_classes.Singleton):
    """
    8.3.1.1
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
        pass

    def set_inst_override_by_type(self, original_type, override_type, full_inst_path):
        """
        8.3.1.3 Implementation
        :param original_type: The original type being overridden
        :param override_type: The overriding type
        :param full_inst_path: The inst where this happens.

        The intention here is to only override when a type of original_type is at the
        full_inst_path provided. If someone stores a different class at full_inst_path
        then the override will not happen.

        We capture this by storing the original and override types as a tuple at the full
        inst path.  Later we'll retrieve the tuple and check the type of the object at
        the full_inst_path.

        instance_overrides is an OrderedDict, so we will check the paths in the order they
        are registered later.
        """
        assert issubclass(original_type, utility_classes.uvm_void), "You tried to override a non-uvm_void class"
        assert issubclass(override_type, utility_classes.uvm_void), "You tried to use a non-uvm_void class as an override"
        self.fd.overrides[original_type] = utility_classes.Override(override_type, full_inst_path)


    def set_inst_override_by_name(self, original_name, override_name, full_inst_path):
        """
        8.3.1.4.1
        Here we use the names of classes instead of the classes.  The original_name
        doesn't need to be the name of a class, it can be an arbitrary string. The
        override_name must be the name of a class.

        Later we will retrieve this by searching through the keys for a match to
        a path and then checking that the name given in the search matches the
        original_name
        :param original:
        :param override:
        :return:
        """
        assert isinstance(full_inst_path, str), "The inst_path must be a string"
        assert isinstance(original_name, str), "Original_name must be a string"
        assert isinstance(override_name, str), "Override_name must be a string"
        try:
            override_type = self.fd.classes[override_name]
            original_type = self.fd.classes[original_name]
        except KeyError:
            raise error_classes.UVMFactoryError(f"{override_name} or {original_name}" + " has not been defined.")
        self.fd.overrides[original_type] = utility_classes.Override(override_type, full_inst_path)



    def set_type_override_by_type(self, original_type, override_type, replace=True):
        """
        8.3.1.4.2
        :param original_type: The original type to be overridden
        :param override_type: The new type that will override it
        :param replace: If the override exists, only replace it if this is True
        """
        assert issubclass(original_type, utility_classes.uvm_void), "You tried to override a non-uvm_void class"
        assert issubclass(override_type, utility_classes.uvm_void), "You tried to use a non-uvm_void class as an override"
        if (original_type not in self.fd.overrides) or replace:
            self.fd.overrides[original_type] = utility_classes.Override(override_type)

    def set_type_override_by_name(self, original_type_name, override_type_name, replace=True):
        """
        8.3.1.4.2
        :param original_type_name: The name of the type to be overridden or an arbitrary string.
        :param override_type_name: The name of the overriding type. It must have been declared.
        :param replace: If the override already exists only replace if this is True
        :return:
        """
        assert isinstance(original_type_name, str), "Original_name must be a string"
        assert isinstance(override_type_name, str), "Override_name must be a string"
        try:
            override_type = self.fd.classes[override_type_name]
            original_type = self.fd.classes[original_type_name]
        except KeyError:
            raise error_classes.UVMFactoryError(f"{override_type_name} or {original_type_name}" + " has not been defined.")

        if (original_type not in self.fd.overrides) or replace:
            self.fd.overrides[original_type] = utility_classes.Override(override_type)



    def create_object_by_type(self, requested_type, parent_inst_path="", name=""):
        """
        :param requeested_type: The type that we request but that can be overridden
        :param parent_inst_path: The get_full_name path of the parrent
        :param name: The name of the instance requested_type("name")
        :return: Type that is child of uvm_object.
        """

