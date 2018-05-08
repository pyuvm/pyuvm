from uvm_pkg import UVMFactoryError
from base_classes import Singleton
from predefined_component_classes import uvm_object
from predefined_component_classes import uvm_component

class uvm_factory(metaclass=Singleton):
    classes = {}
    class_overrides={}
    instance_overrides = {}

    def register(self,name,cls):
        self.classes[name]=cls

    def set_inst_override_by_type(self, original, override, full_inst_path):
        self.instance_overrides[full_inst_path] = override

    def set_inst_override_by_name(self, original_name, override_name, full_inst_path):
        self.instance_overrides[full_inst_path] = self.classes[override_name]

    def set_type_override_by_type(self, original, override, replace=True):
        '''
        8.3.1.4.2
        '''
        if replace or original not in self.class_overrides:
            self.class_overrides[original]=override

    def set_type_override_by_name(self, original_name, override_name, replace=True):
        self.set_type_override_by_type(self.classes[original_name], self.classes[override_name], replace)

    # 8.3.1.5 Creation!  Let there be objects

    def create_object_by_type(self, requested_type, parent_inst_path="", name=""):
        assert(isinstance(name,str)), "name must be a string"
        assert(isinstance( parent_inst_path, str )), "parent_inst_path must be a string"
        if not issubclass( type( requested_type ), object ):
            raise TypeError( f'{requested_type} should be a uvm_object. Yours is a {type(requested_type)}' )

        instance= f'{parent_inst_path}.{name}'
        if instance in self.instance_overrides:
            return self.instance_overrides[instance](name)
        if requested_type in self.class_overrides:
            return self.class_overrides[requested_type]( name )
        return requested_type( name )

    def create_component_by_type(self, requested_type, name, parent):
        if not issubclass(type(parent), uvm_component):
            raise TypeError(f'{parent} should be a uvm_component. Yours is a {type(parent)}')
        if not issubclass(  requested_type , uvm_component ):
            raise TypeError( f'{requested_type} should be a uvm_component. Yours is a {requested_type}' )
        instance=f'{parent.full_name}.{name}'

        if instance in self.instance_overrides:
            return self.instance_overrides[instance](name, parent)
        if requested_type in self.class_overrides:
            return self.class_overrides[requested_type]( name, parent )
        return requested_type( name, parent )

    def create_object_by_name(self, requested_type_name, parent_inst_path="", name=""):
        if len(parent_inst_path) > 0 and len(name) > 0:
            full_path=f'{parent_inst_path}.{name}'
            try:
                requested_type = self.classes[requested_type_name]
            except KeyError:
                raise UVMFactoryError(f'{requested_type_name} is not registered with the factory')

            if full_path in self.instance_overrides:
                return self.instance_overrides[full_path] ( name )

        if requested_type in self.class_overrides:
            return self.class_overrides[requested_type] ( name )

        return requested_type(name)

    def create_component_by_name(self, requested_type_name, parent_inst_path="", name="", parent=None):
        try:
            requested_type = self.classes[requested_type_name]
        except KeyError:
            raise UVMFactoryError ( f'{requested_type_name} is not registered with the factory' )

        if len(name) == 0 or parent is None:
            raise RuntimeError(f'create_component_by_name requires a name and parent')

        if not issubclass(type(parent), uvm_component):
            raise TypeError(f'{parent} should be a uvm_component. Yours is a {type(parent)}')
        if not issubclass(  requested_type , uvm_component ):
            raise TypeError( f'{requested_type} should be a subclass of uvm_component. Yours is a {requested_type}' )

        if len(parent_inst_path) > 0:
            full_path=f'{parent_inst_path}.{name}'
            if full_path in self.instance_overrides:
                return self.instance_overrides[full_path] ( name, parent )

        if requested_type in self.class_overrides:
            return self.class_overrides[requested_type] ( name, parent )

        return requested_type(name, parent)

#8.3.1.6











