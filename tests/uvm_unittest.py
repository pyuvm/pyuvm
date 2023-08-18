import unittest
import logging
import pytest


@pytest.mark.usefixtures("initialize_pyuvm")
class uvm_TestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('uvm_TestCase')
