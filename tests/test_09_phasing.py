import pyuvm_unittest
from pyuvm import *
import inspect

this_function_name = inspect.currentframe().f_code.co_name


class s09_phasing_TestCase(pyuvm_unittest.pyuvm_TestCase):
    phase_list = {}

    class my_comp(uvm_component):
        def log_phase(self):
            """
            Log this function to the phase list
            """
            comp_name = self.get_name()
            function_name = inspect.stack()[1][3]

            s09_phasing_TestCase.phase_list[function_name].append(comp_name)

        def build_phase(self):
            self.log_phase()

        def connect_phase(self):
            self.log_phase()

        def end_of_elaboration_phase(self):
            self.log_phase()

        def start_of_simulation_phase(self):
            self.log_phase()

        def run_phase(self):
            self.log_phase()

        def extract_phase(self):
            self.log_phase()

        def check_phase(self):
            self.log_phase()

        def report_phase(self):
            self.log_phase()

        def final_phase(self):
            self.log_phase()

    def setUp(self):
        s09_phasing_TestCase.phase_list = {}
        for phase_class in uvm_common_phases:
            phase_func = phase_class.__name__[4:]
            s09_phasing_TestCase.phase_list[phase_func] = []

        self.top = self.my_comp("top", None)
        #
        # top +-> A +-> C
        #           +-> D
        #     +-> B +-> E
        #           +-> F
        #
        A = self.my_comp("A", self.top)
        B = self.my_comp("B", self.top)
        self.my_comp("C", A)
        self.my_comp("D", A)
        self.my_comp("E", B)
        self.my_comp("F", B)

    def tearDown(self):
        uvm_root().clear_hierarchy()

    # 9.3.1.3.1/9.3.1.3.5
    def test_stub(self):
        """testing the basic testing mechanism"""
        self.top.build_phase()
        self.assertEqual("top", s09_phasing_TestCase.phase_list["build_phase"][0])

    def test_traverse(self):
        top_down = ['top', 'A', 'C', 'D', 'B', 'E', 'F']
        bottom_up = ['C', 'D', 'A', 'E', 'F', 'B', 'top']
        sorted_list = sorted(top_down)
        for phase_class in uvm_common_phases:
            phase = phase_class()
            phase.traverse(self.top)
            if phase_class == uvm_run_phase:
                utility_classes.RunningThreads().join_all()
            function_name = phase_class.__name__[4:]
            returned_comps = s09_phasing_TestCase.phase_list[function_name]
            if isinstance(phase, uvm_run_phase):
                self.assertEqual(sorted_list, sorted(returned_comps))
            elif isinstance(phase, uvm_topdown_phase):
                self.assertEqual(top_down, returned_comps)
            elif isinstance(phase, uvm_bottomup_phase):
                self.assertEqual(bottom_up, returned_comps)
            else:
                # Should not get here.
                self.assertTrue(False)

        pass
