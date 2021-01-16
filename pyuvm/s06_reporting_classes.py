'''
pyuvm uses the Python logging system to do reporting.  Still, we need this base class
to be true to the hierarchy.  Every instance of a child class has its own logger.

There may be a need to implement uvm_info, uvm_error, uvm_warning, and uvm_fatal, but
it would be best to first see how the native Python logging system does the job.
'''
from pyuvm.s05_base_classes import uvm_object
import logging


# 6.2.1
class uvm_report_object(uvm_object):
    def __init__(self, name):
        super().__init__(name)
        full_name = self.get_full_name()
        self.logger = logging.getLogger(full_name)
        self.logger.setLevel(level=logging.INFO)
        self.logger.propagate=False
        handler = logging.StreamHandler()
        handler.setLevel(logging.NOTSET)
        formatter = logging.Formatter("%(levelname)s: %(filename)s(%(lineno)d)[%(name)s]: %(message)s")
        handler.setFormatter(formatter)
        self.add_logging_handler(handler)
        pass


    def set_logging_level(self, logging_level):
        self.logger.setLevel(logging_level)

    def add_logging_handler(self, handler):
        assert isinstance(handler, logging.Handler), \
            f"You must pass a logging.Handler not {type(handler)}"
        self.logger.addHandler(handler)

    def remove_logging_handler(self, handler):
        assert isinstance(handler, logging.Handler), \
            f"You must pass a logging.Handler not {type(handler)}"
        self.logger.removeHandler(handler)

    def set_formatter_on_handlers(self, formatter):
        assert isinstance(formatter, logging.Formatter), \
            f"You must pass a logging.Formatter not {type(formatter)}"
        for handler in self.logger.handlers:
            handler.setFormatter(formatter)
