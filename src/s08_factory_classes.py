import meta_classes
import error_classes
# from predefined_component_classes import uvm_object
from s13_predefined_component_classes import uvm_component


# Implementing section 8 in the IEEE Specification
# The IEEE spec assumes that UVM is being written in SystemVerilog,
# a language that does not allow you to control how classes get defined.
# Python has more control in this area. With Python we can set things up
# so that any class that extends uvm_void automatically gets registered
# into the factory.


# Our implementation starts at section 8.3.2 uvm_factory


class uvm_factory(metaclass=meta_classes.Singleton):
    """
    8.3.1.1
    The uvm_factory is a singleton that delivers all factory functions.
    """

    # 8.3.1.2.1 get
    # There is no get() method in Python singletons.  Instead you instantiate
    # the singleton as normal and you automatically get the singleton.

    # 8.3.1.3 register
    # There is no register in pyuvm.  Instead the factory builds its class
    # database through introspection.

    def __init__(self):
        self.fd = meta_classes.FactoryDicts()
        pass

    def register(self, name, cls):
        self.fd.classes[name] = cls

    def set_inst_override_by_type(self, original, override, full_inst_path):
        self.fd.instance_overrides[full_inst_path] = override

    def set_inst_override_by_name(self, original_name, override_name, full_inst_path):
        self.fd.instance_overrides[full_inst_path] = self.fd.classes[override_name]

    def set_type_override_by_type(self, original, override, replace=True):
        '''
        8.3.1.4.2
        '''
        if replace or original not in self.fd.class_overrides:
            self.fd.class_overrides[original] = override

    def set_type_override_by_name(self, original_name, override_name, replace=True):
        self.set_type_override_by_type(self.fd.classes[original_name], self.fd.classes[override_name], replace)

    # 8.3.1.5 Creation!  Let there be objects

    def create_object_by_type(self, requested_type, parent_inst_path="", name=""):
        assert (isinstance(name, str)), "name must be a string"
        assert (isinstance(parent_inst_path, str)), "parent_inst_path must be a string"
        if not issubclass(type(requested_type), object):
            raise TypeError(f'{requested_type} should be a uvm_object. Yours is a {type(requested_type)}')

        instance = f'{parent_inst_path}.{name}'
        if instance in self.fd.instance_overrides:
            return self.fd.instance_overrides[instance](name)
        if requested_type in self.fd.class_overrides:
            return self.fd.class_overrides[requested_type](name)
        return requested_type(name)

    def create_component_by_type(self, requested_type, name, parent):
        if not issubclass(type(parent), uvm_component):
            raise TypeError(f'{parent} should be a uvm_component. Yours is a {type(parent)}')
        if not issubclass(requested_type, uvm_component):
            raise TypeError(f'{requested_type} should be a uvm_component. Yours is a {requested_type}')
        instance = f'{parent.full_name}.{name}'

        if instance in self.fd.instance_overrides:
            return self.fd.instance_overrides[instance](name, parent)
        if requested_type in self.fd.class_overrides:
            return self.fd.class_overrides[requested_type](name, parent)
        return requested_type(name, parent)

    def create_object_by_name(self, requested_type_name, parent_inst_path="", name=""):
        if len(parent_inst_path) > 0 and len(name) > 0:
            full_path = f'{parent_inst_path}.{name}'
            try:
                requested_type = self.fd.classes[requested_type_name]
            except KeyError:
                raise error_classes.UVMFactoryError(f'{requested_type_name} is not registered with the factory')

            if full_path in self.fd.instance_overrides:
                return self.fd.instance_overrides[full_path](name)

            if requested_type in self.fd.class_overrides:
                return self.fd.class_overrides[requested_type](name)

            return requested_type(name)

    def create_component_by_name(self, requested_type_name, parent_inst_path="", name="", parent=None):
        try:
            requested_type = self.fd.classes[requested_type_name]
        except KeyError:
            raise UVMFactoryError(f'{requested_type_name} is not registered with the factory')

        if len(name) == 0 or parent is None:
            raise RuntimeError(f'create_component_by_name requires a name and parent')

        if not issubclass(type(parent), uvm_component):
            raise TypeError(f'{parent} should be a uvm_component. Yours is a {type(parent)}')
        if not issubclass(requested_type, uvm_component):
            raise TypeError(f'{requested_type} should be a subclass of uvm_component. Yours is a {requested_type}')

        if len(parent_inst_path) > 0:
            full_path = f'{parent_inst_path}.{name}'
            if full_path in self.fd.instance_overrides:
                return self.fd.instance_overrides[full_path](name, parent)

        if requested_type in self.fd.class_overrides:
            return self.fd.class_overrides[requested_type](name, parent)

        return requested_type(name, parent)


