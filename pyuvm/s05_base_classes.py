"""
This file defines the UVM base classes
"""
import sys

try:
    import logging
    import inspect
    import copy
    import pyuvm.error_classes as error_classes
    import pyuvm.utility_classes as utility_classes
except ModuleNotFoundError as mnf:
    print(mnf)
    sys.exit(1)


class uvm_object(utility_classes.uvm_void):
    """
    5.3.1
    """

    def __init__(self, name=''):
        """
        Implements behavior in new()
        5.3.2
        """
        # Private
        assert (isinstance(name, str)), f"{name} is not a string it is a {type(name)}"
        self.set_name(name)
        self.logger = logging.getLogger(name)

    def get_uvm_seeding(self):
        """
        5.3.3.1
        """
        raise error_classes.UVMNotImplemented('get_uvm_seeding not implemented')

    def set_uvm_seeding(self, enable):
        """
        5.3.3.2
        """
        raise error_classes.UVMNotImplemented('set_uvm_seeding not implemented')

    def reseed(self):
        """
        5.3.3.3
        """
        raise error_classes.UVMNotImplemented('reseed not implemented')

    # 5.3.3.4
    def get_name(self):
        """
        Return the name of this object as passed by the constructor
        """
        assert (self.obj_name != None), f"Internal error. {str(self)} has no name"
        return self.obj_name

    def set_name(self, name):
        """
        5.3.4.1
        """
        assert (isinstance(name, str)), f"Must set the name to a string"
        self.obj_name = name

    def get_full_name(self):
        """
        5.3.4.3
        """
        return self.get_name()


    def get_inst_id(self):
        """
        5.3.4.4
        Returns the python ID which fits the bill for what the ID is supposed to be.
        """
        return id(self)

    def get_type(self):
        """
        5.3.4.5
        Not implemented because Python can implement the factory without
        these shenanigans.
        """
        raise error_classes.UVMNotImplemented('Python provides better ways to do this so the uvm_object_wrapper is unimplemented')

    def get_object_type(self):
        """
        5.3.4.6
        Not implemented because Python can implement the factory without
        these shenanigans.
        """
        raise error_classes.UVMNotImplemented('Python provides better ways to do this so the uvm_object_wrapper is unimplemented')

    def get_type_name(self):
        """
        5.3.4.7
        """
        return type(self).__name__

    def create(self, name):
        """
        5.3.5.1
        :return:
        """
        return self.__class__(name)




    def clone(self):
        """
        5.3.5.2
        Unlike the clone in the SystemVerilog UVM, this clone does the deep
        copy without the user needing to override do_copy()
        """
        return copy.deepcopy(self)

    def print(self):
        """
        5.3.6.1
        """
        raise error_classes.UVMNotImplemented('There are probably better ways to do printing in Python')

    def sprint(self):
        raise error_classes.UVMNotImplemented('There are probably better ways to do printing in Python')

    def do_print(self):
        raise error_classes.UVMNotImplemented('There are probably better ways to do printing in Python')

    def convert2string(self):
        """
        5.3.6.4
        This interface exists in Python as the __str__() method
        """
        raise error_classes.UsePythonMethod('Use Python __str__() method')

    def record(self):
        """
        5.3.7
        """
        raise error_classes.UVMNotImplemented('Python does not run in the simulator, so no recording')

    def do_record(self):
        """
        5.3.7.2
        """
        raise error_classes.UVMNotImplemented('Python does not run in the simulator, so no recording')

    def copy(self):
        """
        5.3.8.1
        """
        raise error_classes.UsePythonMethod('Python has the __copy__() method and the copy module')

    def do_copy(self):
        """
        5.3.8.2
        """
        raise error_classes.UsePythonMethod('Use the __deepcopy__() method to implement this to support the copy module')

    def compare(self):
        """
        5.3.9.1
        """
        raise error_classes.UsePythonMethod('Use the __eq__() __lt__() and other comparison methods to implement this')

    def do_compare(self):
        """
        5.3.9.2
        """
        raise error_classes.UsePythonMethod('Use the __eq__(), __lt__() and other comparison methods to implement this.')

    def pack(self):
        """
        5.3.10.1
        Delivers data in object as a dynamic array of bits
        :return:
        """

        raise error_classes.UsePythonMethod("use pickle, json, or yaml.")

    def pack_bytes(self):
        """
        5.3.10.1
        :return:
        """
        raise error_classes.UsePythonMethod("use pickle, json, or yaml.")


    def pack_ints(self):
        """
        5.3.10.1
        :return:
        """
        raise error_classes.UsePythonMethod("use pickle, json, or yaml.")

    def pack_longints(self):
        """
        5.3.10.1
        :return:
        """
        raise error_classes.UsePythonMethod("use pickle, json, or yaml.")

    def do_pack(self):
        """
        5.3.10.2
        :return:
        """
        raise error_classes.UsePythonMethod("use pickle, json, or yaml.")


    def unpack(self):
        """
        5.3.11.1
        Delivers data in object as a dynamic array of bits
        :return:
        """
        raise error_classes.UsePythonMethod("use pickle, json, or yaml.")

    def push_active_policy(self):
        """
        5.3.14.1
        :return:
        """
        raise error_classes.UsePythonMethod("use pickle, json, or yaml.")

    def pop_active_policy(self):
        """
        5.3.14.2
        :return:
        """
        raise error_classes.UsePythonMethod("use pickle, json, or yaml.")

    def get_active_policy(self):
        """
        5.3.14.3
        :return:
        """
        raise error_classes.UsePythonMethod("use pickle, json, or yaml.")

    def unpack_bytes(self):
        """
        5.3.11.1
        :return:
        """
        raise error_classes.UsePythonMethod("use pickle, json, or yaml.")

    def unpack_ints(self):
        """
        5.3.11.1
        :return:
        """
        raise error_classes.UsePythonMethod("use pickle, json, or yaml.")


    def unpack_longints(self):
        """
        5.3.11.1
        :return:
        """
        raise error_classes.UsePythonMethod("use pickle, json, or yaml.")

    def do_unpack(self):
        """
        5.3.11.2
        :return:
        """
        raise error_classes.UsePythonMethod("use pickle, json, or yaml.")


    def set_local(self):
        """
        5.3.12
        """
        raise error_classes.UsePythonMethod('The getattr and setattr functions handle this')

    def do_execute_op(self, op):
        """
        5.3.13.1
        :return:
        """
        raise error_classes.UsePythonMethod('The getattr and setattr functions handle all 5.3.13 issues')

class uvm_field_op:
    """
    5.3.13
    We do not implement the UVM field op as this is a UVM way of providing field-based
    functionality that can better be implemented using Python functionality.
    """

    def __new__(cls, *args, **kwargs):
        raise error_classes.UsePythonMethod('Python has simpler ways of handling field function.')

class uvm_policy:
    """
    5.3.14
    The uvm_policy is used to add functionality to SystemVerilog that already exists
    in Python. It is not needed in pyuvm.
    """

    def __new__(cls, *args, **kwargs):
        raise error_classes.UsePythonMethod('Python has simpler ways of handling functionality provided by policies.')


class uvm_transaction(uvm_object):
    """
    5.4.1
    """
    def __init__(self, name="", initiator=None):
        """
        5.4.2.1
        :param name: Object name
        :param initiator: componennt that is initiator
        """
        super().__init__(name)
        self.set_initiator(initiator)
        self.transaction_id = None

    def set_initiator(self, initiator):
        """
        5.4.2.14
        :param initiator: initiator to set
        :return: None
        """
        self.initiator = initiator

    def get_initiator(self):
        """
        5.4.2.15
        :return: initiator
        """
        return self.initiator


    def __not_implemented(self):
        raise error_classes.UVMNotImplemented('This method is not implemented at this time.')

    def accept_tr(self, time):
        """
        5.4.2.2
        :param time:
        :return:
        """
        self.__not_implemented()

    def do_accept_tr(self):
        """
        5.4.2.3
        :return:
        """
        self.__not_implemented()

    def begin_tr(self, begin_time=0, parent_handle = None):
        """
        5.4.2.5
        :param begin_time:
        :param parent_handle:
        :return:
        """
        self.__not_implemented()

    def do_begin_tr(self):
        """
        5.4.2.5
        :return:
        """
        self.__not_implemented()

    def end_tr(self, end_time= 0, free_handle = True):
        """
        5.4.2.6
        :param end_time:
        :param free_handle:
        :return:
        """
        self.__not_implemented()

    def do_end_tr(self):
        """
        5.4.2.7
        :return:
        """
        self.__not_implemented()

    def get_tr_handle(self):
        """
        5.4.2.8
        """
        self.__not_implemented()

    def enable_recording(self):
        """
        5.4.2.9
        :return:
        """
        self.__not_implemented()

    def disable_recording(self):
        """
        5.4.2.10
        :return:
        """
        self.__not_implemented()

    def is_recording_enabled(self):
        """
        5.4.2.11
        :return:
        """
        self.__not_implemented()

    def is_active(self):
        """
        5.4.2.12
        :return:
        """
        self.__not_implemented()

    def get_event_pool(self):
        """
        5.4.2.13
        :return:
        """
        self.__not_implemented()


    def get_accept_time(self):
        """
        5.4.2.16
        :return:
        """
        self.__not_implemented()


    def get_begin_time(self):
        """
        5.4.2.16
        :return:
        """
        self.__not_implemented()


    def get_end_time(self):
        """
        5.4.2.16
        :return:
        """
        self.__not_implemented()

    def set_transaction_id(self, txn_id):
        """
        5.4.2.17
        :param self:
        :return:
        """
        assert(isinstance(txn_id,int)), "Transaction ID must be an integer."
        self.transaction_id = txn_id

    def get_transaction_id(self):
        """
        5.4.2.18
        :return:
        """
        if self.transaction_id is None:
            return id(self)
        else:
            return self.transaction_id







class uvm_time:
    """
    5.6
    Not implemented in pyuvm since we are not running in a simulator.
    """

