

class Singleton(type):
    _instances={}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls]=super(Singleton,cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    @classmethod
    def clear_singletons(cls):
        cls._instances.clear()
        pass

class FactoryDicts(metaclass=Singleton):
    classes = {}
    class_overrides = {}
    instance_overrides = {}


class FactoryMeta(type):
    """
    This is the metaclass that causes all uvm_void classes to register themselves
    """
    def __init__(cls, name, bases, clsdict):
        FactoryDicts.classes[cls.__name__] = cls
        super().__init__(name, bases, clsdict)


