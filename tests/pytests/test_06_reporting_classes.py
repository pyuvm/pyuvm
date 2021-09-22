import pytest
import pyuvm_unittest
from pyuvm import *


def test_object_creation():
    """
    Test that we actually get a logger in our object.
    """
    ro = uvm_report_object('ro')
    assert hasattr(ro, "logger")
    assert not ro.logger.propagate

def test_logging_of_debug_messages(caplog):
    ro = uvm_report_object('ro')
    ro.logger.propagate = True # workaround for 'caplog'
    caplog.set_level(logging.DEBUG, ro.logger.name)
    ro.logger.debug('debug')
    assert caplog.record_tuples == [(ro.logger.name, logging.DEBUG, 'debug')]

def test_logging_of_info_messages(caplog):
    ro = uvm_report_object('ro')
    ro.logger.propagate = True # workaround for 'caplog'
    caplog.set_level(logging.DEBUG)
    ro.logger.info('info')
    assert caplog.record_tuples == [(ro.logger.name, logging.INFO, 'info')]

def test_logging_of_error_messages(caplog):
    ro = uvm_report_object('ro')
    ro.logger.propagate = True # workaround for 'caplog'
    caplog.set_level(logging.DEBUG)
    ro.logger.error('error')
    assert caplog.record_tuples == [(ro.logger.name, logging.ERROR, 'error')]

def test_logging_of_critical_messages(caplog):
    ro = uvm_report_object('ro')
    ro.logger.propagate = True # workaround for 'caplog'
    caplog.set_level(logging.DEBUG)
    ro.logger.critical('critical')
    assert caplog.record_tuples == [(ro.logger.name, logging.CRITICAL, 'critical')]
