from pyuvm import *  # pylint: disable=unused-wildcard-import
import pyuvm.utility_classes as utility_classes


class TestHolder:

    def setUp(self):
        self.top = uvm_component("top", None)

    def tearDown(self):
        uvm_root.clear_singletons()
        pass

    def test_no_assert(self):
        pass

    def test_no_assert2(self):
        pass

