"""
This file defines the UVM base classes
"""

import logging
from typing import Optional

from cocotb.utils import get_sim_time

from pyuvm._error_classes import (
    UsePythonMethod,
    UVMError,
    UVMFatalError,
    UVMNotImplemented,
)
from pyuvm._s08_factory_classes import uvm_factory
from pyuvm._utility_classes import uvm_void
from pyuvm.uvm_reporting import get_sv_uvm_style_reporting_enabled
from pyuvm.uvm_reporting.uvm_base_core_report import uvm_base_core_report
from pyuvm.uvm_reporting.uvm_report_server import uvm_report_server
from pyuvm.uvm_reporting.uvm_verbosity import UVM_LOW


# 5.3.1
class uvm_object(uvm_void):
    """The most basic UVM object"""

    __default_logging_level = logging.INFO

    # 5.3.2
    def __init__(self, name=""):
        """
        :param name: Name of the object. Default is empty string.
        """
        assert isinstance(name, str), f"{name} is not a string it is a {type(name)}"
        self._logger = None
        self._uvm_report_core = None
        parent = getattr(self, "parent", None)
        self._uvm_verbosity = int(getattr(parent, "uvm_verbosity", UVM_LOW))
        self.set_name(name)

    def get_initial_logger_name(self):
        """
        :returns: The name of the initial logger

        Override this method if you want to change the way the logger name is
        generated.

        The default looks like this:

        .. code-block:: python
            return self.get_full_name() + str(id(self))

        """
        return self.get_full_name() + str(id(self))

    @staticmethod
    def set_default_logging_level(default_logging_level):
        """
        :param default_logging_level: The default logging level
        :returns: None

        """
        uvm_object.__default_logging_level = default_logging_level

    @staticmethod
    def get_default_logging_level():
        """
        :returns: The default logging level

        """
        return uvm_object.__default_logging_level

    @property
    def logger(self):
        if self._logger is None:
            uvm_root_logger = logging.getLogger("uvm")
            logger_name = self.get_initial_logger_name()
            self._logger = (
                uvm_root_logger.getChild(logger_name)
                if logger_name
                else uvm_root_logger
            )
            self._logger.setLevel(level=uvm_object.get_default_logging_level())
            self._logger.propagate = get_sv_uvm_style_reporting_enabled()
            manager = uvm_report_server.get_or_none()
            if manager is not None:
                manager.register_logger(self._logger)
        return self._logger

    @logger.setter
    def logger(self, logger):
        assert isinstance(logger, logging.Logger), (
            f"You must pass a logging.Logger not {type(logger)}"
        )
        self._logger = logger
        manager = uvm_report_server.get_or_none()
        if manager is not None:
            manager.register_logger(logger)
        if self._uvm_report_core is not None:
            self._uvm_report_core.set_logger(logger)

    @property
    def uvm_verbosity(self):
        return self._uvm_verbosity

    @uvm_verbosity.setter
    def uvm_verbosity(self, verbosity):
        self.set_report_verbosity(verbosity)

    def get_report_verbosity(self):
        return self._uvm_verbosity

    def set_report_verbosity(self, verbosity):
        self._uvm_verbosity = int(verbosity)
        if self._uvm_report_core is None:
            _ = self.uvm_report
        self._uvm_report_core.set_verbosity(self._uvm_verbosity)
        return self._uvm_verbosity

    def set_report_logger(self, logger):
        self.logger = logger

    @property
    def uvm_report(self):
        if self._uvm_report_core is None:
            self._uvm_report_core = uvm_base_core_report(
                owner=self,
                parent=None,
                default_verbosity=self._uvm_verbosity,
            )
        return self._uvm_report_core.uvm_report

    # 5.3.3.1
    def get_uvm_seeding(self):
        """Not implemented"""
        raise UVMNotImplemented("get_uvm_seeding not implemented")

    # 5.3.3.2
    def set_uvm_seeding(self, enable):
        """
        Not implemented
        """
        raise UVMNotImplemented("set_uvm_seeding not implemented")

    # 5.3.3.3
    def reseed(self):
        """Not implemented"""
        raise UVMNotImplemented("reseed not implemented")

    # 5.3.3.4
    def get_name(self):
        """
        :return: String with name of uvm_object.

        Return the name of this object as passed by the constructor
        """
        assert self._obj_name is not None, f"Internal error. {str(self)} has no name"
        return self._obj_name

    # 5.3.4.1
    def set_name(self, name):
        """
        :param name: Name of the object

        Set the name
        """
        assert isinstance(name, str), "Must set the name to a string"
        self._obj_name = name

    # 5.3.4.3
    def get_full_name(self):
        """
        :return: The full path and name of the object

        The full name for a uvm_object is simply the name
        """
        return self.get_name()

    # 5.3.4.4
    def get_inst_id(self):
        """
        :return: The python ID which fits the bill for what the ID
            is supposed to be.

        """
        return id(self)

    # 5.3.4.5
    def get_type(self):
        """
        Not implemented because Python can implement the factory without
        these shenanigans.
        """
        raise UsePythonMethod(
            "Python provides better ways to do this "
            "so the uvm_object_wrapper is unimplemented"
        )

    # 5.3.4.6
    def get_object_type(self):
        """
        Not implemented because Python can implement the factory without
        these shenanigans.
        """
        raise UsePythonMethod(
            "Python provides better ways to do this "
            "so the uvm_object_wrapper is unimplemented"
        )

    # 5.3.4.7
    def get_type_name(self):
        """
        :return: Returns the type's ``__name__`` magic variable

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
        :return: A new object with the same name and data as this object.

        """
        new = self.__class__(self.get_name())
        new.copy(self)
        return new

    # 5.3.6.1
    def print(self):
        """
        Not implemented. Use __str__() and print()
        """
        raise UsePythonMethod(
            "There are better ways to do printing in Python usingprint() or str()"
        )

    # 5.3.6.2
    def sprint(self):
        """Not implemented. use __str__() and print()"""
        raise UsePythonMethod("There are better ways to do printing in Python")

    # 5.3.6.3
    def do_print(self):
        """not implemented. Use __str__() and print()"""
        raise UsePythonMethod("There are better ways to do printing in Python")

    # 5.3.6.4
    def convert2string(self):
        """
        :return: The result of ``__str__()``

        Override if you want something different than ``__str__()``
        """

        return self.__str__()

    # 5.3.7
    def record(self):
        """
        Not implemented.
        """
        raise UVMNotImplemented("Perhaps a future project?")

    # 5.3.7.2
    def do_record(self):
        """
        Not implemented as we are not in a simulator
        """
        raise UVMNotImplemented("No recording")

    # 5.3.8.1
    def copy(self, rhs):
        """
        :param rhs: The object to copy from
        :return: None

        Copy fields from rhs to this object using ``self.do_copy()``

        """
        self.do_copy(rhs)

    # 5.3.8.2
    def do_copy(self, rhs):
        """
        :param rhs: The object to copy from
        :return: None

        By default we copy the name. Override this function
        to copy the rest of the object members.
        """
        self.set_name(rhs.get_name())

    # 5.3.9.1
    def compare(self, rhs):
        """
        :param rhs: The object being compared.
        :returns: True if do_compare() believes the objects
            are the same.

        Compares one uvm_object to another uvm_object using
        the user-overridden ``do_compare()`` function.
        """
        return self.do_compare(rhs)

    # 5.3.9.2
    def do_compare(self, rhs):
        """
        :param rhs: The object being compared.
        :returns: True if the objects are the same.

        Uses ``__eq__()`` to compare the objects.  Override this
        to change the compare behavior.
        """
        return self == rhs

    # 5.3.10.1
    def pack(self):
        """
        Not implemented. There are Pythonic solutions to this.
        """
        raise UsePythonMethod("use struct, pickle, json, or yaml.")

    # 5.3.10.1
    def pack_bytes(self):
        """
        Not implemented. There are Pythonic solutions to this.
        """
        raise UsePythonMethod("use struct, pickle, json, or yaml.")

    # 5.3.10.1
    def pack_ints(self):
        """
        Not implemented. There are Pythonic solutions to this.
        """
        raise UsePythonMethod("use struct, pickle, json, or yaml.")

    # 5.3.10.1
    def pack_longints(self):
        """
        Not implemented. There are Pythonic solutions to this.
        """
        raise UsePythonMethod("use struct, pickle, json, or yaml.")

    # 5.3.10.2
    def do_pack(self):
        """
        Not implemented. There are Pythonic solutions to this.
        """
        raise UsePythonMethod("use struct, pickle, json, or yaml.")

    # 5.3.11.1
    def unpack(self):
        """
        Not implemented. There are Pythonic solutions to this.
        """
        raise UsePythonMethod("use pickle, json, or yaml.")

    # 5.3.14.1
    def push_active_policy(self):
        """
        Not implemented.
        """
        raise UVMNotImplemented("policies not implemented yet")

    # 5.3.14.2
    def pop_active_policy(self):
        """
        Not implemented.
        """
        raise UVMNotImplemented("policies not implemented yet")

    # 5.3.14.3
    def get_active_policy(self):
        """
        Not implemented.
        """
        raise UVMNotImplemented("policies not implemented yet")

    # 5.3.11.1
    def unpack_bytes(self):
        """
        Not implemented. There are Pythonic solutions to this.
        """
        raise UsePythonMethod("use struct, pickle, json, or yaml.")

    # 5.3.11.1
    def unpack_ints(self):
        """
        Not implemented. There are Pythonic solutions to this.
        """
        raise UsePythonMethod("use struct, pickle, json, or yaml.")

    # 5.3.11.1
    def unpack_longints(self):
        """
        Not implemented. There are Pythonic solutions to this.
        """
        raise UsePythonMethod("use struct, pickle, json, or yaml.")

    # 5.3.11.2
    def do_unpack(self):
        """
        Not implemented. There are Pythonic solutions to this.
        """
        raise UsePythonMethod("use struct, pickle, json, or yaml.")

    # 5.3.12
    def set_local(self):
        """
        Not implemented use Python getattr and setattr.
        """
        raise UsePythonMethod("The getattr and setattr functions handle this")

    # 5.3.13.1
    def do_execute_op(self, op):
        """
        Not implemented.
        """
        raise UsePythonMethod("Not needed in Python")


# 5.3.13
class uvm_field_op:
    """
    We do not implement the UVM field op as this is a
    UVM way of providing field-based functionality
    that can better be implemented using Python functionality.
    """

    def __new__(cls, *args, **kwargs):
        raise UsePythonMethod("Python has simpler ways of handling field function.")


# 5.3.14
class uvm_policy:
    """
    The uvm_policy is used to add functionality to
    SystemVerilog that already exists
    in Python. It is not needed in pyuvm.
    """

    def __new__(cls, *args, **kwargs):
        raise UsePythonMethod(
            "Python has simpler ways of handling functionality provided by policies."
        )


# 5.4.1
class uvm_transaction(uvm_object):
    """
    Transactions without interface to logging or waveforms.
    """

    # 5.4.2.1
    def __init__(self, name="", initiator=None):
        """
        :param name: Object name
        :param initiator: component that is the initiator
        """
        super().__init__(name)
        self.set_initiator(initiator)
        self.transaction_id = id(self)
        self._accept_time: Optional[int] = None
        self._begin_time: Optional[int] = None
        self._end_time: Optional[int] = None

    def set_id_info(self, other):
        """
        :param other: uvm_transaction with transaction_id
        :return: None

        Set transaction_id from other

        """
        self.transaction_id = other.transaction_id

    def set_initiator(self, initiator):
        """
        :param initiator: initiator to set
        :return: None

        5.4.2.14
        """
        self._initiator = initiator

    def get_initiator(self):
        """
        :return: initiator

        5.4.2.15
        """
        return self._initiator

    def __not_implemented(self):
        raise UVMNotImplemented("This method is not implemented at this time.")

    # 5.4.2.2
    def accept_tr(self, accept_time=0):
        """
        :param accept_time: Simulation time when the transaction is accepted

        IEEE 1800.2 5.4.2.2
        """
        if (accept_time is not None) and (accept_time != 0):
            self._accept_time = accept_time
        else:
            self._accept_time = get_sim_time()
        # TODO Call 'accept' event pool triggers
        self.do_accept_tr()

    # 5.4.2.3
    def do_accept_tr(self):
        """
        User definable method to add to ``accept_tr()``
        """
        pass

    # 5.4.2.5
    def begin_tr(self, begin_time=0, parent_handle=None) -> int:
        """
        :param begin_time: Simulation time at which
                           the transaction is acted upon by the driver
        :param parent_handle:
        """
        if (begin_time is not None) and (begin_time != 0):
            # begin_time must be >= accept_time. If accept_tr() was never called
            # there is no accept constraint to enforce.
            if self._accept_time is not None and begin_time < self._accept_time:
                raise UVMFatalError(
                    f"begin_time : {begin_time} is less than"
                    f" accept_time: {self._accept_time} for"
                    f" the transaction : {self.get_name()}"
                )
            else:
                self._begin_time = begin_time
        else:
            self._begin_time = get_sim_time()
        # TODO: update recodring API calls
        self.do_begin_tr()
        # TODO Call 'begin' event pool triggers
        # Update return value when recording is enabled
        return 0

    # 5.4.2.5
    def do_begin_tr(self):
        """
        User definable method
        """
        pass

    # 5.4.2.6
    def end_tr(self, end_time=0, free_handle=True) -> None:
        """
        :param end_time: Simulation time at which the transaction
                         is marked as acted upon
        :param free_handle:
        :return: None
        """
        if end_time is not None and end_time != 0:
            # end_time must be >= accept_time and >= begin_time. Any stage that
            # was never reached imposes no constraint.
            if self._accept_time is not None and end_time < self._accept_time:
                raise UVMFatalError(
                    f"end_time : {end_time} is less than"
                    f" accept_time : {self._accept_time}"
                    f" for the transaction : {self.get_name()}"
                )
            if self._begin_time is not None and end_time < self._begin_time:
                raise UVMFatalError(
                    f"end_time : {end_time} is less than"
                    f" begin_time : {self._begin_time}"
                    f" for the transaction : {self.get_name()}"
                )
            else:
                self._end_time = end_time
        else:
            self._end_time = get_sim_time()
        # TODO: update recodring API calls
        self.do_end_tr()
        # TODO Call 'end' event pool triggers
        # Update return value when recording is enabled

    # 5.4.2.7
    def do_end_tr(self):
        """
        Not implemented
        """
        pass

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
    def get_accept_time(self) -> int:
        """
        :return: Accept time of transaction
        :raises UVMError: if ``accept_tr()`` was never called

        """
        if self._accept_time is None:
            raise UVMError(f"accept_tr() was never called on {self.get_name()}")
        return self._accept_time

    def get_begin_time(self) -> int:
        """
        :return: Begin time of transaction
        :raises UVMError: if ``begin_tr()`` was never called

        """
        if self._begin_time is None:
            raise UVMError(f"begin_tr() was never called on {self.get_name()}")
        return self._begin_time

    def get_end_time(self) -> int:
        """
        :return: End time of transaction
        :raises UVMError: if ``end_tr()`` was never called

        """
        if self._end_time is None:
            raise UVMError(f"end_tr() was never called on {self.get_name()}")
        return self._end_time

    # 5.4.2.17
    def set_transaction_id(self, txn_id):
        """
        :param txn_id: Transaction ID

        Sets transaction's transaction_id
        """
        assert isinstance(txn_id, int), "Transaction ID must be an integer."
        self.transaction_id = txn_id

    # 5.4.2.18
    def get_transaction_id(self):
        """
        :return: Transaction ID

        Returns transaction_id
        """
        if self.transaction_id is None:
            return id(self)
        else:
            return self.transaction_id
