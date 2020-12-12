'''
pyuvm uses the Python logging system to do reporting.  Still, we need this base class
to be true to the hierarchy.  Every instance of a child class has its own logger.

There may be a need to implement uvm_info, uvm_error, uvm_warning, and uvm_fatal, but
it would be best to first see how the native Python logging system does the job.
'''
from pyuvm.s05_base_classes import uvm_object
import logging
"""
6.2.1
"""
class uvm_report_object(uvm_object):
    def __init__(self, name):
        super().__init__(name)
        self.logger=logging.getLogger(name)
