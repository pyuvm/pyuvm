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
from cocotb.log import SimTimeContextFilter
from cocotb.log import SimLogFormatter, SimColourLogFormatter
from cocotb.utils import want_color_output
from logging import DEBUG, CRITICAL, ERROR, WARNING, INFO, NOTSET, NullHandler   # noqa: F401, E501


class PyuvmFormatter(SimColourLogFormatter):
    def __init__(self, full_name):
        """
        :param full_name: The full name of the object

        """
        self.full_name = full_name
        super().__init__()

    def format(self, record):
        """
        :param record: The log record

        """
        new_msg = f"[{self.full_name}]: {record.msg}"
        record.msg = new_msg
        name_temp = record.name
        record.name = f"{record.pathname}({record.lineno})"
        if want_color_output():
            formatted_msg = super().format(record)
        else:
            formatted_msg = SimLogFormatter.format(self, record)
        record.name = name_temp
        return formatted_msg


# 6.2.1
class uvm_report_object(uvm_object):
    __default_logging_level = logging.INFO
    """ The basis of all classes that can report """
    def __init__(self, name):
        """
        :param name: The name of the object
        :returns: None

        """
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
        """
        :param default_logging_level: The default logging level
        :returns: None

        """
        uvm_report_object.__default_logging_level = default_logging_level

    @staticmethod
    def get_default_logging_level():
        """
        :returns: The default logging level

        """
        return uvm_report_object.__default_logging_level

    def set_logging_level(self, logging_level):
        """
        :param logging_level: The logging level
        :returns: None

        """
        self.logger.setLevel(logging_level)

    def add_logging_handler(self, handler):
        """
        :param handler: The logging handler
        :returns: None

        """
        assert isinstance(handler, logging.Handler), \
            f"You must pass a logging.Handler not {type(handler)}"
        if handler.formatter is None:
            handler.addFilter(SimTimeContextFilter())
            handler.setFormatter(self._uvm_formatter)
        self.logger.addHandler(handler)

    def remove_logging_handler(self, handler):
        """
        :param handler: The logging handler to remove
        :returns: None

        """
        assert isinstance(handler, logging.Handler), \
            f"You must pass a logging.Handler not {type(handler)}"
        self.logger.removeHandler(handler)

    def remove_streaming_handler(self):
        """
        :returns: None

        Removes the streaming handler
        """
        self.logger.removeHandler(self._streaming_handler)

    def disable_logging(self):
        """
        :returns: None

        Disables logging
        """
        self.remove_streaming_handler()
        self.add_logging_handler(NullHandler())
