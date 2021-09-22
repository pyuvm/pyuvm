import pytest
import pyuvm_unittest
from pyuvm import *


class s06_reporting_classes_TestCase(pyuvm_unittest.pyuvm_TestCase):
    """Basic test cases."""

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def test_object_creation(self):
        """
        Test that we actually get a logger in our object.
        """
        ro = uvm_report_object('ro')
        assert hasattr(ro, "logger")
        assert not ro.logger.propagate

    def test_logging_of_debug_messages(self):
        ro = uvm_report_object('ro')
        ro.logger.propagate = True # workaround for 'caplog'
        self._caplog.set_level(logging.DEBUG, ro.logger.name)
        ro.logger.debug('debug')
        assert self._caplog.record_tuples == [(ro.logger.name, logging.DEBUG, 'debug')]

    def test_logging_of_info_messages(self):
        ro = uvm_report_object('ro')
        ro.logger.propagate = True # workaround for 'caplog'
        self._caplog.set_level(logging.DEBUG)
        ro.logger.info('info')
        assert self._caplog.record_tuples == [(ro.logger.name, logging.INFO, 'info')]

    def test_logging_of_error_messages(self):
        ro = uvm_report_object('ro')
        ro.logger.propagate = True # workaround for 'caplog'
        self._caplog.set_level(logging.DEBUG)
        ro.logger.error('error')
        assert self._caplog.record_tuples == [(ro.logger.name, logging.ERROR, 'error')]

    def test_logging_of_critical_messages(self):
        ro = uvm_report_object('ro')
        ro.logger.propagate = True # workaround for 'caplog'
        self._caplog.set_level(logging.DEBUG)
        ro.logger.critical('critical')
        assert self._caplog.record_tuples == [(ro.logger.name, logging.CRITICAL, 'critical')]
