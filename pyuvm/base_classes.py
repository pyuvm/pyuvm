'''
This file defines the UVM base classes
'''
import sys
import logging
import
try:
    from pyuvm.uvm_common import *
    from abc import ABC
except ModuleNotFoundError as mnf:
    print(mnf)
    sys.exit(1)

class uvm_void(ABC):
    '''
    The abstract base class for all classes.  Not really neaded for
    python in that it defines no methods, and Python uses duck typing.
    It is here for completeness.
    '''

class uvm_object(uvm_void):

    def __init__(self, name='unnamed'):
    # Private
        self.__name=None
        self.__logger = logging.getLogger ( name )

    # Publich Properties

        self.name=name

    def get_uvm_seeding(self):
        raise UVMNotImplemented('get_uvm_seeding not implemented')

    def set_uvm_seeding(self, enable):
        raise UVMNotImplemented('set_uvm_seeding not implemented')

    def reseed(self):
        raise  UVMNotImplemented('reseed not implemented')

    @property
    def name(self):
        assert(self.__name !=None)
        return self.__name

    @name.setter
    def name(self, name):
        assert(isinstance(name, str))
        self.__name=name

    @property
    def full_name(self):
        return self.name



