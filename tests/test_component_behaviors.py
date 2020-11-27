import pyuvm_unittest
from pyuvm import *
import utility_classes
import inspect
# These tests ensure that components work. We'll test
# things like phasing order, TLM communication between run_phase
# thread, the config_db, etc.


class t_data(metaclass=utility_classes.Singleton):
    """
    Holds data structure that all tests can access
    """
    def __init__(self):
        self.phase_list = []


class phase_component(uvm_component):
    """
    A component that writes its full name and phase to the phase list
    """

    def trace(self):
        phase = inspect.stack()[1][3]
        t_data().phase_list.append((self.get_full_name(), phase))

    def build_phase(self):
        self.trace()

    def connect_phase(self):
        self.trace()

    def end_of_elaboration_phase(self):
        self.trace()

    def start_of_simulation_phase(self):
        self.trace()

    def run_phase(self):
        self.trace()

    def extract_phase(self):
        self.trace()

    def check_phase(self):
        self.trace()

    def report_phase(self):
        self.trace()

    def final_phase(self):
        self.trace()

class s19_register_layer_interaction_with_RTL_TestCase(pyuvm_unittest.pyuvm_TestCase):

    def test_basic_phases(self):
        uvm_root().run_test("phase_component")
        pass

    def test_phase_hierarchy(self):
        class t_comp(phase_component):
            def build_phase(self):
                super().build_phase()
                aa = phase_component("aa", self)
                bb = phase_component("bb", self)

        uvm_root().run_test("t_comp")
        pass

