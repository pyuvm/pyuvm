# pyuvm uses the Python logging system to do reporting.
# Still, we need this base class to be true to the hierarchy.
# Every instance of a child class has its own logger.
#
# There may be a need to implement uvm_info, uvm_error,
# uvm_warning, and uvm_fatal, but it would be best to
# first see how the native Python logging system does the job.

from pyuvm.s05_base_classes import uvm_object
import logging
from logging import DEBUG, CRITICAL, ERROR, WARNING, INFO, NOTSET  # noqa: F401


# 6.2.1
class uvm_report_object(uvm_object):
    """ The basis of all classes that can report """

    def __init__(self, name):
        super().__init__(name)
        uvm_root_logger = logging.getLogger('uvm')
        # Every object gets its own logger
        logger_name = self.get_full_name() + str(id(self))
        self.logger = uvm_root_logger.getChild(logger_name)
        self.logger.setLevel(level=logging.INFO)  # Default is to print INFO
        # We are not sending log messages up the hierarchy
        self.logger.propagate = False
        self._streaming_handler = logging.StreamHandler()
        # Don't let the handler interfere with logger level
        self._streaming_handler.setLevel(logging.NOTSET)
        # Make log messages look like UVM messages
        self._uvm_formatter = logging.Formatter(
            "%(levelname)s: %(filename)s(%(lineno)d)[" + self.get_full_name() + "]: %(message)s")  # noqa: E501
        self.add_logging_handler(self._streaming_handler)

    def set_logging_level(self, logging_level):
        """ Sets the logger level """
        self.logger.setLevel(logging_level)

    def add_logging_handler(self, handler):
        """ Adds a handler """
        assert isinstance(handler, logging.Handler), \
            f"You must pass a logging.Handler not {type(handler)}"
        if handler.formatter is None:
            handler.setFormatter(self._uvm_formatter)
        self.logger.addHandler(handler)

    def remove_logging_handler(self, handler):
        """ Removes a specific handler  """
        assert isinstance(handler, logging.Handler), \
            f"You must pass a logging.Handler not {type(handler)}"
        self.logger.removeHandler(handler)

    def remove_streaming_handler(self):
        self.logger.removeHandler(self._streaming_handler)

    def set_formatter_on_handlers(self, formatter):
        """ Set an identical formatter on all handlers """
        assert isinstance(formatter, logging.Formatter), \
            f"You must pass a logging.Formatter not {type(formatter)}"
        for handler in self.logger.handlers:
            handler.setFormatter(formatter)
