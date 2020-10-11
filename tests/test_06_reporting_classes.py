import pyuvm_unittest
from uvm_pkg import *

class s06_reporting_classes_TestCase (pyuvm_unittest.pyuvm_TestCase):
    """Basic test cases."""

    def test_object_creation_6_2_2_1(self):
        """
        Test that we actually get a logger in our object.
        """
        ro = uvm_report_object("ro")
        self.assertTrue(hasattr(ro, "logger"))
        with self.assertLogs('ro', level='INFO') as cm:
            ro.logger.info('first message')
            ro.logger.error('second message')
            self.assertEqual(cm.output, ['INFO:ro:first message',
                                         'ERROR:ro:second message'])
