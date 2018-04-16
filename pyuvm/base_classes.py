'''
This file defines the UVM base classes
'''
import sys
try:
    import logging
    import inspect
    import copy
    from pyuvm.uvm_pkg import *
    from abc import ABC
except ModuleNotFoundError as mnf:
    print(mnf)
    sys.exit(1)

class uvm_void():
    '''
    5.2
    The abstract base class for all classes.  Not really neaded for
    python in that it defines no methods, and Python uses duck typing.
    It is here for completeness.
    '''

class uvm_object(uvm_void):
    '''
    5.3.1
    '''
    override = None

    @classmethod
    def create(cls, name='unnamed'):
        '''
        5.3.5.1
        This implements the factory with overrides. It is much simpler
        to do this in Python than SystemVerilog
        '''
        if cls.override:
            return cls.override ( name )
        else:
            return cls ( name )


    def __init__(self, name='unnamed'):
        '''
        Implements behavior in new()
        5.3.2
        '''
    # Private
        assert(isinstance(name,str))
        self.__name=None
        self.__logger = logging.getLogger ( name )

    # Publich Properties

        self.name=name

    def get_uvm_seeding(self):
        '''
        5.3.3.1
        '''
        raise UVMNotImplemented('get_uvm_seeding not implemented')

    def set_uvm_seeding(self, enable):
        '''
        5.3.3.2
        '''
        raise UVMNotImplemented('set_uvm_seeding not implemented')

    def reseed(self):
        '''
        5.3.3.3
        '''
        raise  UVMNotImplemented('reseed not implemented')

    @property
    def name(self):
        '''
        5.3.4.2
        '''
        assert(self.__name !=None)
        return self.__name

    @name.setter
    def name(self, name):
        '''
        5.3.4.1
        '''
        assert(isinstance(name, str))
        self.__name=name

    @property
    def full_name(self):
        '''
        5.3.4.3
        '''
        return self.name


    @property
    def inst_id(self):
        '''
        5.3.4.4
        '''
        return id(self)

    def get_type(self):
        '''
        5.3.4.5
        '''
        raise UVMNotImplemented('Python provides better ways to do this so the uvm_object_wrapper is unimplemented')

    def get_object_type(self):
        '''
        5.3.4.6
        '''
        raise UVMNotImplemented ( 'Python provides better ways to do this so the uvm_object_wrapper is unimplemented' )

    @property
    def type_name(self):
        '''
        5.3.4.7
        '''
        return type(self).__name__

    def clone(self):
        '''
        5.3.5.2
        Unlike the clone in the SystemVerilog UVM, this clone does the deep
        copy without the user needing to override do_copy()
        '''
        return copy.deepcopy(self)

    def print(self):
        '''
        5.3.6.1
        '''
        raise UVMNotImplemented ( 'There are probably better ways to do printing in Python')

    def sprint(self):
        raise UVMNotImplemented ( 'There are probably better ways to do printing in Python' )

    def do_print(self):
        raise UVMNotImplemented ( 'There are probably better ways to do printing in Python' )

    def convert2string(self):
        '''
        5.3.6.4
        This interface exists in Python as the __str__() method
        '''
        raise UsePythonMethod ( 'Use Python __str__() method')

    def record(self):
        '''
        5.3.7
        '''
        raise UVMNotImplemented ( 'Python does not run in the simulator, so no recording' )
    def do_record(self):
        '''
        5.3.7.2
        '''
        raise UVMNotImplemented ( 'Python does not run in the simulator, so no recording' )

    def copy(self):
        '''
        5.3.8.1
        '''
        raise UsePythonMethod('Python has the __copy__() method and the copy module')

    def do_copy(self):
        '''
        5.3.8.2
        '''
        raise UsePythonMethod('Use the __deepcopy__() method to implement this to support the copy module')

    def compare(self):
        '''
        5.3.9.1
        '''
        raise UsePythonMethod('Use the __eq__() __lt__() and other comparison methods to implement this')

    def do_compare(self):
        '''
        5.3.9.2
        '''
        raise UsePythonMethod('Use the __eq__(), __lt__() and other comparison methods to implement this.')

    def pack(self):
        '''
        5.3.10.1
        Delivers data in object as a dynamic array of bits
        :return:
        '''

        raise UVMNotImplemented ( 'Need to implement this before being finished' )

    def pack_bytes(self):
        '''
        5.3.10.1
        :return:
        '''
        raise UVMNotImplemented('Need to implement this before being finished')

    def pack_ints(self):
        '''
        5.3.10.1
        :return:
        '''
        raise UVMNotImplemented('Need to implement this before being finished')

    def pack_longints(self):
        '''
        5.3.10.1
        :return:
        '''
        raise UVMNotImplemented('Need to implement this before being finished')

    def do_pack(self):
        '''
        5.3.10.2
        :return:
        '''
        raise UVMNotImplemented('Need to implement this before being finished')

    def unpack(self):
        '''
        5.3.11.1
        Delivers data in object as a dynamic array of bits
        :return:
        '''

        raise UVMNotImplemented ( 'Need to implement this before being finished' )

    def unpack_bytes(self):
        '''
        5.3.11.1
        :return:
        '''
        raise UVMNotImplemented ( 'Need to implement this before being finished' )

    def unpack_ints(self):
        '''
        5.3.11.1
        :return:
        '''
        raise UVMNotImplemented ( 'Need to implement this before being finished' )

    def unpack_longints(self):
        '''
        5.3.11.1
        :return:
        '''
        raise UVMNotImplemented ( 'Need to implement this before being finished' )

    def do_unpack(self):
        '''
        5.3.11.2
        :return:
        '''
        raise UVMNotImplemented ( 'Need to implement this before being finished' )

    def set_local(self):
        '''
        5.3.12
        '''
        raise UsePythonMethod('The getattr and setattr functions handle this')

    def do_execute_op(self):
        '''
        5.3.13.1
        :return:
        '''
        raise UsePythonMethod('The getattr and setattr functions handle all 5.3.13 issues')


class uvm_field_op:
    '''
    5.3.13
    We do not implement the UVM field op as this is a UVM way of providing field-based
    functionality that can better be implemented using Python functionality.
    '''
    def __new__(cls, *args, **kwargs):
        raise UsePythonMethod('Python has simpler ways of handling field function.')


class uvm_policy:
    '''
    5.3.14
    The uvm_policy is used to add functionality to SystemVerilog that already exists
    in Python. It is not needed in pyuvm.
    '''
    def __new__(cls, *args, **kwargs):
        raise UsePythonMethod('Python has simpler ways of handling functionality provided by policies.')


class uvm_transaction(uvm_object):
    '''
    5.4
    The pyuvm uvm_transaction does not include a uvm_initiator.  This object supports printing and recording
    and these things are either irrelevant (recording only happens in a simulator) or supplanted (Python
    provides better ways to handle printing.

    As a result we do not implement any of the transaction methods in the UVM transaction.  It serves
    only as a placeholder class to be consistent with the fact that uvm_sequence_item extends uvm_transaction.
    '''

class uvm_time:
    '''
    5.6
    Not implemented in pyuvm since we are not running in a simulator.
    '''
