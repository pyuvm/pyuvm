import pytest
from pyuvm import *


def test_object_creation():
    """
    Test that we actually get a logger in our object.
    """
    ro = uvm_report_object('ro')
    assert hasattr(ro, "logger")
    assert not ro.logger.propagate


@pytest.mark.parametrize('level,msg', [(logging.DEBUG, 'debug'),
                                       (logging.INFO, 'info'),
                                       (logging.ERROR, 'error'),
                                       (logging.CRITICAL, 'critical')])
def test_logging(level, msg, caplog):
    ro = uvm_report_object('ro')
    ro.logger.propagate = True  # workaround for 'caplog'
    caplog.set_level(logging.DEBUG, ro.logger.name)
    ro.logger.log(level, msg)
    assert caplog.record_tuples == [(ro.logger.name, level, msg)]
