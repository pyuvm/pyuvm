# pyuvm uses the Python logging system to do reporting.
# Still, we need this base class to be true to the hierarchy.
# Every instance of a child class has its own logger.
#
# There may be a need to implement uvm_info, uvm_error,
# uvm_warning, and uvm_fatal, but it would be best to
# first see how the native Python logging system does the job.

from pyuvm.s05_base_classes import uvm_object
import logging


# 6.2.1
class uvm_report_object(uvm_object):
    """ The basis of all classes that can report """

    def __init__(self, name):
        super().__init__(name)
        uvm_root_logger = logging.getLogger('uvm')
        # Every object gets its own logger
        self.logger = uvm_root_logger.getChild(self.get_full_name())
        self.logger.setLevel(level=logging.INFO)  # Default is to print INFO
        # We are not sending log messages up the hierarchy
        self.logger.propagate = False
        handler = logging.StreamHandler()
        # Don't let the handler interfere with logger level
        handler.setLevel(logging.NOTSET)
        # Make log messages look like UVM messages
        formatter = logging.Formatter(
            "%(levelname)s: %(filename)s(%(lineno)d)[%(name)s]: %(message)s")
        handler.setFormatter(formatter)
        self.add_logging_handler(handler)
        pass

    def set_logging_level(self, logging_level):
        """ Sets the logger level """
        self.logger.setLevel(logging_level)

    def add_logging_handler(self, handler):
        """ Adds a handler """
        assert isinstance(handler, logging.Handler), \
            f"You must pass a logging.Handler not {type(handler)}"
        self.logger.addHandler(handler)

    def remove_logging_handler(self, handler):
        """ Removes a specific handler  """
        assert isinstance(handler, logging.Handler), \
            f"You must pass a logging.Handler not {type(handler)}"
        self.logger.removeHandler(handler)

    def set_formatter_on_handlers(self, formatter):
        """ Set an identical formatter on all handlers """
        assert isinstance(formatter, logging.Formatter), \
            f"You must pass a logging.Formatter not {type(formatter)}"
        for handler in self.logger.handlers:
            handler.setFormatter(formatter)
