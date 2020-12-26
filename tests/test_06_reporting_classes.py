import pyuvm_unittest
from pyuvm import *

class s06_reporting_classes_TestCase (pyuvm_unittest.pyuvm_TestCase):
    """Basic test cases."""

    def test_object_creation(self):
        """
        Test that we actually get a logger in our object.
        """
        ro = uvm_report_object('ro')
        self.assertTrue(hasattr(ro, "logger"))
        with self.assertLogs(ro.logger, level='DEBUG') as cm:
            ro.logger.debug('debug')
            ro.logger.info('info')
            ro.logger.error('error')
            ro.logger.critical('critical')
            self.assertEqual(cm.output, ['DEBUG:ro:debug',
                                         'INFO:ro:info',
                                         'ERROR:ro:error',
                                         'CRITICAL:ro:critical'])







