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
import os

from cocotb.log import SimColourLogFormatter, SimTimeContextFilter
from logging import DEBUG, CRITICAL, ERROR, WARNING, INFO, NOTSET, NullHandler   # noqa: F401, E501
from cocotb.utils import get_time_from_sim_steps
import cocotb.ANSI as ANSI

try:
    _suppress = int(os.environ.get("COCOTB_REDUCED_LOG_FMT", "1"))
except ValueError:
    _suppress = 1


# Column alignment
_LEVEL_CHARS = len("UVM_WARNING")
_FILENAME_CHARS = 200
_LINENO_CHARS = 5
_FUNCNAME_CHARS = 100


class PyuvmSimLogFormatter(logging.Formatter):
    """Log formatter to provide consistent UVM like log message handling.

    This will only add simulator timestamps if the handler object this
    formatter is attached to has a :class:`SimTimeContextFilter` filter
    attached, which cocotb ensures by default.
    """

    # Removes the arguments from the base class. Docstring needed to make
    # sphinx happy.
    def __init__(self):
        """Takes no arguments."""
        super().__init__()

    # Justify and truncate
    @staticmethod
    def ljust(string, chars):
        if len(string) > chars:
            return ".." + string[(chars - 2) * -1:]
        return string.ljust(chars)

    @staticmethod
    def rjust(string, chars):
        if len(string) > chars:
            return ".." + string[(chars - 2) * -1:]
        return string.rjust(chars)

    def _format(self, level, record, msg, coloured=False):

        # Wait for Ray Salemi's buy-in uvm_level_str = 'UVM_' + level
        # Not using UVM_ prefix just yet
        uvm_level_str = level
        sim_time = getattr(record, "created_sim_time", None)
        if sim_time is None:
            sim_time_str = "  -.--ns"
        else:
            time_ns = get_time_from_sim_steps(sim_time, "ns")
            sim_time_str = f"{time_ns:6.2f}ns"
        prefix = (
            sim_time_str.rjust(11) + " " + uvm_level_str + " "
        )

        if not _suppress:
            prefix += (
                self.rjust(os.path.split(record.filename)[1], _FILENAME_CHARS)
                + ":"
                + self.ljust(str(record.lineno), _LINENO_CHARS) + " in "
                + self.ljust(str(record.funcName), _FUNCNAME_CHARS) + " "
            )

        # these lines are copied from the builtin logger
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if msg[-1:] != "\n":
                msg = msg + "\n"
            msg = msg + record.exc_text

        prefix_len = len(prefix)
        if coloured:
            prefix_len -= len(level) - _LEVEL_CHARS
        pad = "\n" + " " * (prefix_len)
        return prefix + pad.join(msg.split("\n"))

    def format(self, record):
        """Prettify the log output, annotate with simulation time"""

        msg = record.getMessage()
        level = record.levelname.ljust(_LEVEL_CHARS)

        return self._format(level, record, msg)


class PyuvmSimColourLogFormatter(PyuvmSimLogFormatter):
    """Log formatter to provide consistent log message handling."""

    loglevel2colour = {
        logging.TRACE: "%s",
        logging.DEBUG: "%s",
        logging.INFO: "%s",
        logging.WARNING: ANSI.COLOR_WARNING + "%s" + ANSI.COLOR_DEFAULT,
        logging.ERROR: ANSI.COLOR_ERROR + "%s" + ANSI.COLOR_DEFAULT,
        logging.CRITICAL: ANSI.COLOR_CRITICAL + "%s" + ANSI.COLOR_DEFAULT,
    }

    def format(self, record):
        """Prettify the log output, annotate with simulation time"""

        msg = record.getMessage()

        # Need to colour each line in case coloring is applied in the message
        msg = "\n".join(
            [
                SimColourLogFormatter.loglevel2colour.get(
                    record.levelno, "%s") % line
                for line in msg.split("\n")
            ]
        )
        level = SimColourLogFormatter.loglevel2colour.get(
            record.levelno, "%s"
        ) % record.levelname.ljust(_LEVEL_CHARS)

        return self._format(level, record, msg, coloured=True)


# class PyuvmFormatter(SimColourLogFormatter):
class PyuvmFormatter(PyuvmSimColourLogFormatter):
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
