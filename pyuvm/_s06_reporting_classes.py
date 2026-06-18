# pyuvm uses the Python logging system to do reporting.
# Still, we need this base class to be true to the hierarchy.
# Every instance of a child class has its own logger.
#
# There may be a need to implement uvm_info, uvm_error,
# uvm_warning, and uvm_fatal, but it would be best to
# first see how the native Python logging system does the job.

import logging
import sys

from pyuvm._s05_base_classes import uvm_object
from pyuvm._utils import cocotb_version_info
from pyuvm.uvm_reporting import get_sv_uvm_style_reporting_enabled
from pyuvm.uvm_reporting.uvm_report_server import uvm_report_server

if cocotb_version_info < (2, 0):
    from cocotb.log import SimColourLogFormatter, SimLogFormatter, SimTimeContextFilter
    from cocotb.utils import want_color_output

    if want_color_output():
        FormatterBase = SimColourLogFormatter
    else:
        FormatterBase = SimLogFormatter
else:
    from cocotb.logging import SimLogFormatter, SimTimeContextFilter

    FormatterBase = SimLogFormatter


class PyuvmSimTimeContextFilter(SimTimeContextFilter):
    """Use cocotb sim time, but tolerate pytest/docs runs outside simulation."""

    def filter(self, record):
        try:
            return super().filter(record)
        except RuntimeError:
            # cocotb's filter needs a running simulator. Plain pytest and docs
            # imports do not have one, but should still be able to log.
            record.created_sim_time = None
            return True


class PyuvmFormatter(FormatterBase):
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
        msg_temp = record.msg
        new_msg = f"[{self.full_name}]: {record.msg}"
        record.msg = new_msg
        name_temp = record.name
        record.name = f"{record.pathname}({record.lineno})"
        formatted_msg = super().format(record)
        record.msg = msg_temp
        record.name = name_temp
        return formatted_msg


def configure_uvm_root_logger():
    """Attach pyuvm's default stream handler once to the shared uvm logger."""
    if not get_sv_uvm_style_reporting_enabled():
        return None

    uvm_root_logger = logging.getLogger("uvm")
    uvm_root_logger.setLevel(logging.INFO)
    uvm_root_logger.propagate = False
    for handler in uvm_root_logger.handlers:
        if getattr(handler, "_pyuvm_default_handler", False):
            return handler

    streaming_handler = logging.StreamHandler(sys.stdout)
    streaming_handler._pyuvm_default_handler = True
    streaming_handler.addFilter(PyuvmSimTimeContextFilter())
    streaming_handler.setLevel(logging.NOTSET)
    streaming_handler.setFormatter(FormatterBase())
    uvm_root_logger.addHandler(streaming_handler)

    manager = uvm_report_server.get_or_none()
    if manager is not None:
        manager.register_logger(uvm_root_logger)
    return streaming_handler


configure_uvm_root_logger()


# 6.2.1
class uvm_report_object(uvm_object):
    """ The basis of all classes that can report """

    def __init__(self, name):
        """
        :param name: The name of the object
        :returns: None

        """
        super().__init__(name)
        self._uvm_formatter = PyuvmFormatter(self.get_full_name())
        if get_sv_uvm_style_reporting_enabled():
            configure_uvm_root_logger()
            self.logger.propagate = True
            for handler in list(self.logger.handlers):
                if getattr(handler, "_pyuvm_object_default_handler", False):
                    self.logger.removeHandler(handler)
            self._streaming_handler = None
        else:
            self.logger.propagate = False
            self._streaming_handler = logging.StreamHandler(sys.stdout)
            self._streaming_handler._pyuvm_object_default_handler = True
            self._streaming_handler.addFilter(PyuvmSimTimeContextFilter())
            self._streaming_handler.setLevel(logging.NOTSET)
            self.add_logging_handler(self._streaming_handler)

    @staticmethod
    def set_default_logging_level(default_logging_level):
        """
        :param default_logging_level: The default logging level
        :returns: None

        """
        uvm_object.set_default_logging_level(default_logging_level)

    @staticmethod
    def get_default_logging_level():
        """
        :returns: The default logging level

        """
        return uvm_object.get_default_logging_level()

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
        assert isinstance(handler, logging.Handler), (
            f"You must pass a logging.Handler not {type(handler)}"
        )
        if handler.formatter is None:
            handler.addFilter(PyuvmSimTimeContextFilter())
            handler.setFormatter(self._uvm_formatter)
        self.logger.addHandler(handler)
        manager = uvm_report_server.get_or_none()
        if manager is not None:
            manager.register_logger(self.logger)

    def remove_logging_handler(self, handler):
        """
        :param handler: The logging handler to remove
        :returns: None

        """
        assert isinstance(handler, logging.Handler), (
            f"You must pass a logging.Handler not {type(handler)}"
        )
        self.logger.removeHandler(handler)

    def remove_streaming_handler(self):
        """
        :returns: None

        Removes the streaming handler
        """
        if self._streaming_handler is None:
            return
        self.logger.removeHandler(self._streaming_handler)
        self._streaming_handler = None

    def disable_logging(self):
        """
        :returns: None

        Disables logging
        """
        self.remove_streaming_handler()
        self.logger.propagate = False
        self.add_logging_handler(logging.NullHandler())
