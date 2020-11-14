import pyuvm_unittest
from pyuvm import *

class s09_phasing_TestCase (pyuvm_unittest.pyuvm_TestCase):

    # 9.3.1.3.1/9.3.1.3.5
    def test_phase_creation_and_type(self):
        for phase_type in [uvm_phase_imp, uvm_phase_node, uvm_phase_schedule, uvm_phase_domain]:
            pp = phase_type("test")
            self.assertTrue(type(pp), pp.get_type)

    # 9.3.1.3.3-6
    def test_set_get_max_iterations(self):
        pp = uvm_phase("tester")
        pp.set_max_ready_to_end_iterations()
        self.assertEqual(20, pp.get_default_max_ready_to_end_iterations())
        pp.set_default_max_ready_to_end_iterations(35)
        self.assertEqual(35, pp.get_default_max_ready_to_end_iterations())
        self.assertEqual(20, pp.get_max_ready_to_end_iterations())
        pp.set_max_ready_to_end_iterations(50)
        self.assertEqual(50, pp.get_max_ready_to_end_iterations())

    # 9.3.1.4.1
    def test_get_state(self):
        pp = uvm_phase("tester")
        self.assertEqual(pp.get_state(), uvm_phase_state.UVM_PHASE_UNINITIALIZED)

    # 9.3.1.4.2
    def test_get_run_count(self):
        pp = uvm_phase()
        self.assertEqual(0, pp.get_run_count())

