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
        with self.assertLogs(ro.logger, level='DEBUG') as cm:
            ro.logger.debug('debug')
            ro.logger.info('info')
            ro.logger.error('error')
            ro.logger.critical('critical')
            assert cm.output == [f'DEBUG:uvm.ro{id(ro)}:debug',
                                 f'INFO:uvm.ro{id(ro)}:info',
                                 f'ERROR:uvm.ro{id(ro)}:error',
                                 f'CRITICAL:uvm.ro{id(ro)}:critical']
