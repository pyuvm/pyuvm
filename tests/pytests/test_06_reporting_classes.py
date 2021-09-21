import pyuvm_unittest
from pyuvm import *


class s06_reporting_classes_TestCase(pyuvm_unittest.pyuvm_TestCase):
    """Basic test cases."""

    def test_object_creation(self):
        """
        Test that we actually get a logger in our object.
        """
        ro = uvm_report_object('ro')
        assert hasattr(ro, "logger")
        assert not ro.logger.propagate

    def test_logging_of_debug_messages(self):
        ro = uvm_report_object('ro')
        with self.assertLogs(ro.logger, level='DEBUG') as cm:
            ro.logger.debug('debug')
            assert cm.output == [f'DEBUG:uvm.ro{id(ro)}:debug']

    def test_logging_of_info_messages(self):
        ro = uvm_report_object('ro')
        with self.assertLogs(ro.logger, level='DEBUG') as cm:
            ro.logger.info('info')
            assert cm.output == [f'INFO:uvm.ro{id(ro)}:info']

    def test_logging_of_error_messages(self):
        ro = uvm_report_object('ro')
        with self.assertLogs(ro.logger, level='DEBUG') as cm:
            ro.logger.error('error')
            assert cm.output == [f'ERROR:uvm.ro{id(ro)}:error']

    def test_logging_of_critical_messages(self):
        ro = uvm_report_object('ro')
        with self.assertLogs(ro.logger, level='DEBUG') as cm:
            ro.logger.critical('critical')
            assert cm.output == [f'CRITICAL:uvm.ro{id(ro)}:critical']
