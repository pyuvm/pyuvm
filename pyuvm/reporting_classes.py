'''
pyuvm uses the Python logging system to do reporting.  Therefore we're not
translating this section.
'''
from base_classes import uvm_object
import logging

class uvm_report_object(uvm_object):
    def __init__(self, name):
        super().__init__(name)
        self.logger=logging.getLogger(name)
