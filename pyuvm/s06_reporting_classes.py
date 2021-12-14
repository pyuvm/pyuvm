# pyuvm uses the Python logging system to do reporting.
# Still, we need this base class to be true to the hierarchy.
# Every instance of a child class has its own logger.
#
# There may be a need to implement uvm_info, uvm_error,
# uvm_warning, and uvm_fatal, but it would be best to
# first see how the native Python logging system does the job.

from pyuvm.s05_base_classes import uvm_object
import logging
import sys
from cocotb.log import SimColourLogFormatter, SimTimeContextFilter
from logging import DEBUG, CRITICAL, ERROR, WARNING, INFO, NOTSET, NullHandler   # noqa: F401, E501


class PyuvmFormatter(SimColourLogFormatter):
    def __init__(self, full_name):
        self.full_name = full_name
        super().__init__()

    def format(self, record):
        new_msg = f"{record.filename}({record.lineno})"
        new_msg += f"[{self.full_name}]: " + record.msg
        record.msg = new_msg
        return super().format(record)


# 6.2.1
class uvm_report_object(uvm_object):
    __default_logging_level = logging.INFO
    """ The basis of all classes that can report """
    def __init__(self, name):
        super().__init__(name)
        uvm_root_logger = logging.getLogger('uvm')
        # Every object gets its own logger
        logger_name = self.get_full_name() + str(id(self))
        self.logger = uvm_root_logger.getChild(logger_name)
        self.logger.setLevel(
            level=uvm_report_object.get_default_logging_level())
        # We are not sending log messages up the hierarchy
        self.logger.propagate = False
        self._streaming_handler = logging.StreamHandler(sys.stdout)
        self._streaming_handler.addFilter(SimTimeContextFilter())
        # Don't let the handler interfere with logger level
        self._streaming_handler.setLevel(logging.NOTSET)
        # Make log messages look like UVM messages
        self._uvm_formatter = PyuvmFormatter(self.get_full_name())
        self.add_logging_handler(self._streaming_handler)

    @staticmethod
    def set_default_logging_level(default_logging_level):
        uvm_report_object.__default_logging_level = default_logging_level

    @staticmethod
    def get_default_logging_level():
        return uvm_report_object.__default_logging_level

    def set_logging_level(self, logging_level):
        """ Sets the logger level """
        self.logger.setLevel(logging_level)

    def add_logging_handler(self, handler):
        """ Adds a handler """
        assert isinstance(handler, logging.Handler), \
            f"You must pass a logging.Handler not {type(handler)}"
        if handler.formatter is None:
            handler.addFilter(SimTimeContextFilter())
            handler.setFormatter(self._uvm_formatter)
        self.logger.addHandler(handler)

    def remove_logging_handler(self, handler):
        """ Removes a specific handler  """
        assert isinstance(handler, logging.Handler), \
            f"You must pass a logging.Handler not {type(handler)}"
        self.logger.removeHandler(handler)

    def remove_streaming_handler(self):
        self.logger.removeHandler(self._streaming_handler)

    def disable_logging(self):
        self.remove_streaming_handler()
        self.add_logging_handler(NullHandler())
