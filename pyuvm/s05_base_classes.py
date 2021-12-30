"""
This file defines the UVM base classes
"""
import sys

try:
    import pyuvm.error_classes as error_classes
    import pyuvm.utility_classes as utility_classes
    from pyuvm.s08_factory_classes import uvm_factory
except ModuleNotFoundError as mnf:
    print(mnf)
    sys.exit(1)


# 5.3.1
class uvm_object(utility_classes.uvm_void):
    """ The most basic UVM object """

    # 5.3.2
    def __init__(self, name=''):
        assert (isinstance(name, str)), \
            f"{name} is not a string it is a {type(name)}"
        self.set_name(name)

    # 5.3.3.1
    def get_uvm_seeding(self):
        """Not implemented"""
        raise error_classes.UVMNotImplemented(
            'get_uvm_seeding not implemented')

    # 5.3.3.2
    def set_uvm_seeding(self, enable):
        """ Not implemented """
        raise error_classes.UVMNotImplemented(
            'set_uvm_seeding not implemented')

    # 5.3.3.3
    def reseed(self):
        """ Not implemented """
        raise error_classes.UVMNotImplemented('reseed not implemented')

    # 5.3.3.4
    def get_name(self):
        """
        Return the name of this object as passed by the constructor
        """
        assert (self._obj_name is not None), \
            f"Internal error. {str(self)} has no name"
        return self._obj_name

    # 5.3.4.1
    def set_name(self, name):
        """
        Set the name
        """
        assert (isinstance(name, str)), "Must set the name to a string"
        self._obj_name = name

    # 5.3.4.3
    def get_full_name(self):
        """
        The full name for a uvm_object is simply the name
        """
        return self.get_name()

    # 5.3.4.4
    def get_inst_id(self):
        """
        Returns the python ID which fits the bill
        for what the ID is supposed to be.
        """
        return id(self)

    # 5.3.4.5
    def get_type(self):
        """
        Not implemented because Python can implement the factory without
        these shenanigans.
        """
        raise error_classes.UVMNotImplemented(
            'Python provides better ways to do this '
            'so the uvm_object_wrapper is unimplemented')

    # 5.3.4.6
    def get_object_type(self):
        """
        Not implemented because Python can implement the factory without
        these shenanigans.
        """
        raise error_classes.UVMNotImplemented(
            'Python provides better ways to do this '
            'so the uvm_object_wrapper is unimplemented')

    # 5.3.4.7
    def get_type_name(self):
        """
        Returns types  __name__ magic variable
        """
        return type(self).__name__

    # 5.3.5.1
    @classmethod
    def create(cls, name):
        """
        :return: new object from factory
        """
        new_obj = uvm_factory().create_object_by_type(cls, name=name)
        return new_obj

    # 5.3.5.2
    def clone(self):
        """
        Unlike the clone in the SystemVerilog UVM, this clone()
        uses copy.deepcopy so the user does not need to override
        do_copy()
        """
        new = self.__class__(self.get_name())
        new.copy(self)
        return new

    # 5.3.6.1
    def print(self):
        """
        Not implemented. Use __str__() and print()
        """
        raise error_classes.UVMNotImplemented(
            'There are better ways to do printing in Python using'
            'print() or str()')

    # 5.3.6.2
    def sprint(self):
        """ Not implemented. use __str__() and print()"""
        raise error_classes.UVMNotImplemented(
            'There are better ways to do printing in Python')

    # 5.3.6.3
    def do_print(self):
        """ not implemented. Use __str__() and print()"""
        raise error_classes.UVMNotImplemented(
            'There are better ways to do printing in Python')

    # 5.3.6.4
    def convert2string(self):
        """
        Returns the result of self.__str__().
        Perhaps better to just use __str__() directly?
        :return __str__()
        """
        return self.__str__()

    # 5.3.7
    def record(self):
        """
        Not implemented as we are not in a simulator.
        """
        raise error_classes.UVMNotImplemented(
            'Python does not run in the simulator, so no recording')

    # 5.3.7.2
    def do_record(self):
        """
        Not implemented as we are not in a simulator
        """
        raise error_classes.UVMNotImplemented(
            'Python does not run in the simulator, so no recording')

    # 5.3.8.1
    def copy(self, rhs):
        """
        Copy fields from rhs to this object
        """
        self.do_copy(rhs)

    # 5.3.8.2
    def do_copy(self, rhs):
        """
        Copies name. Override to copy additional data members
        """
        self.set_name(rhs.get_name())

    # 5.3.9.1
    def compare(self, rhs):
        """

        """
        return self.do_compare(rhs)

    # 5.3.9.2
    def do_compare(self, rhs):
        """
        Recommend overriding __eq__() rather than this method.
        """
        return self.__eq__(rhs)

    # 5.3.10.1
    def pack(self):
        """
        Not implemented yet. There are Pythonic solutions to this.
        """
        raise error_classes.UsePythonMethod(
            "use struct, pickle, json, or yaml.")

    # 5.3.10.1
    def pack_bytes(self):
        """
        Not implemented yet. There are Pythonic solutions to this.
        """
        raise error_classes.UsePythonMethod(
            "use struct, pickle, json, or yaml.")

    # 5.3.10.1
    def pack_ints(self):
        """
        Not implemented yet. There are Pythonic solutions to this.
        """
        raise error_classes.UsePythonMethod(
            "use struct, pickle, json, or yaml.")

    # 5.3.10.1
    def pack_longints(self):
        """
        Not implemented yet. There are Pythonic solutions to this.
        """
        raise error_classes.UsePythonMethod(
            "use struct, pickle, json, or yaml.")

    # 5.3.10.2
    def do_pack(self):
        """
        Not implemented yet. There are Pythonic solutions to this.
        """
        raise error_classes.UsePythonMethod(
            "use struct, pickle, json, or yaml.")

    # 5.3.11.1
    def unpack(self):
        """
        Not implemented yet. There are Pythonic solutions to this.
        """
        raise error_classes.UsePythonMethod(
            "use pickle, json, or yaml.")

    # 5.3.14.1
    def push_active_policy(self):
        """
        Not implemented yet.
        """
        raise error_classes.UVMNotImplemented(
            "policies not implemented yet")

    # 5.3.14.2
    def pop_active_policy(self):
        """
        Not implemented yet.
        """
        raise error_classes.UVMNotImplemented("policies not implemented yet")

    # 5.3.14.3
    def get_active_policy(self):
        """
        Not implemented yet.
        """
        raise error_classes.UVMNotImplemented("policies not implemented yet")

    # 5.3.11.1
    def unpack_bytes(self):
        """
        Not implemented yet. There are Pythonic solutions to this.
        """
        raise error_classes.UsePythonMethod(
            "use struct, pickle, json, or yaml.")

    # 5.3.11.1
    def unpack_ints(self):
        """
        Not implemented yet. There are Pythonic solutions to this.
        """
        raise error_classes.UsePythonMethod(
            "use struct, pickle, json, or yaml.")

    # 5.3.11.1
    def unpack_longints(self):
        """
        Not implemented yet. There are Pythonic solutions to this.
        """
        raise error_classes.UsePythonMethod(
            "use struct, pickle, json, or yaml.")

    # 5.3.11.2
    def do_unpack(self):
        """
        Not implemented yet. There are Pythonic solutions to this.
        """
        raise error_classes.UsePythonMethod(
            "use struct, pickle, json, or yaml.")

    # 5.3.12
    def set_local(self):
        """
        Not implemented use Python getattr and setattr.
        """
        raise error_classes.UsePythonMethod(
            'The getattr and setattr functions handle this')

    # 5.3.13.1
    def do_execute_op(self, op):
        """
        Not implemented.
        """
        raise error_classes.UsePythonMethod(
            'Not needed in Python')


# 5.3.13
class uvm_field_op:
    """
    We do not implement the UVM field op as this is a
    UVM way of providing field-based functionality
    that can better be implemented using Python functionality.
    """

    def __new__(cls, *args, **kwargs):
        raise error_classes.UsePythonMethod(
            'Python has simpler ways of handling field function.')


# 5.3.14
class uvm_policy:
    """
    The uvm_policy is used to add functionality to
    SystemVerilog that already exists
    in Python. It is not needed in pyuvm.
    """

    def __new__(cls, *args, **kwargs):
        raise error_classes.UsePythonMethod(
            'Python has simpler ways of handling '
            'functionality provided by policies.')


# 5.4.1
class uvm_transaction(uvm_object):
    """
    Transactions without interface to logging or waveforms.
    """

    # 5.4.2.1
    def __init__(self, name="", initiator=None):
        """
        :param name: Object name
        :param initiator: component that is initiator
        """
        super().__init__(name)
        self.set_initiator(initiator)
        self.transaction_id = id(self)

    def set_id_info(self, other):
        """
        Set transaction_id from other
        :param other: uvm_transaction
        :return: None
        """
        self.transaction_id = other.transaction_id

    def set_initiator(self, initiator):
        """
        5.4.2.14
        :param initiator: initiator to set
        :return: None
        """
        self._initiator = initiator

    def get_initiator(self):
        """
        5.4.2.15
        :return: initiator
        """
        return self._initiator

    def __not_implemented(self):
        raise error_classes.UVMNotImplemented(
            'This method is not implemented at this time.')

    # 5.4.2.2
    def accept_tr(self, time):
        """
        Not implemented
        """
        self.__not_implemented()

    # 5.4.2.3
    def do_accept_tr(self):
        """
        Not implemented
        """
        self.__not_implemented()

    # 5.4.2.5
    def begin_tr(self, begin_time=0, parent_handle=None):
        """
        Not implemented
        """
        self.__not_implemented()

    # 5.4.2.5
    def do_begin_tr(self):
        """
        Not implemented
        """
        self.__not_implemented()

    # 5.4.2.6
    def end_tr(self, end_time=0, free_handle=True):
        """
        Not implemented
        """
        self.__not_implemented()

    # 5.4.2.7
    def do_end_tr(self):
        """
        Not implemented
        """
        self.__not_implemented()

    # 5.4.2.8
    def get_tr_handle(self):
        """
        Not implemented
        """
        self.__not_implemented()

    # 5.4.2.9
    def enable_recording(self):
        """
        Not implemented
        """
        self.__not_implemented()

    # 5.4.2.10
    def disable_recording(self):
        """
        Not implemented
        """
        self.__not_implemented()

    # 5.4.2.11
    def is_recording_enabled(self):
        """
        Not implemented
        """
        self.__not_implemented()

    # 5.4.2.12
    def is_active(self):
        """
        Not implemented
        """
        self.__not_implemented()

    # 5.4.2.13
    def get_event_pool(self):
        """
        Not implemented
        """
        self.__not_implemented()

    # 5.4.2.16
    def get_accept_time(self):
        """
        Not implemented
        """
        self.__not_implemented()

    # 5.4.2.16
    def get_begin_time(self):
        """
        Not implemented
        """
        self.__not_implemented()

    # 5.4.2.16
    def get_end_time(self):
        """
        Not implemented
        """
        self.__not_implemented()

    # 5.4.2.17
    def set_transaction_id(self, txn_id):
        """
        Sets  variable transaction_id
        """
        assert (isinstance(txn_id, int)), "Transaction ID must be an integer."
        self.transaction_id = txn_id

    # 5.4.2.18
    def get_transaction_id(self):
        """
        Returns  variable transaction_id
        """
        if self.transaction_id is None:
            return id(self)
        else:
            return self.transaction_id
