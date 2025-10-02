import inspect

import cocotb

from pyuvm import *
from pyuvm import utility_classes

phase_list = {}


class my_comp(uvm_component):
    def log_phase(self):
        """
        Log this function to the phase list
        """
        comp_name = self.get_name()
        function_name = inspect.stack()[1][3]
        phase_list[function_name].append(comp_name)

    def build_phase(self):
        self.log_phase()

    def connect_phase(self):
        self.log_phase()

    def end_of_elaboration_phase(self):
        self.log_phase()

    def start_of_simulation_phase(self):
        self.log_phase()

    async def run_phase(self):
        self.log_phase()

    def extract_phase(self):
        self.log_phase()

    def check_phase(self):
        self.log_phase()

    def report_phase(self):
        self.log_phase()

    def final_phase(self):
        self.log_phase()


def setUp():
    for phase_class in uvm_common_phases:
        phase_func = phase_class.__name__[4:]
        phase_list[phase_func] = []

    top = my_comp("top", None)
    #
    # top +-> aa +-> cc
    #            +-> dd
    #     +-> bb +-> ee
    #            +-> ff
    #
    aa = my_comp("aa", top)
    bb = my_comp("bb", top)
    my_comp("cc", aa)
    my_comp("dd", aa)
    my_comp("ee", bb)
    my_comp("ff", bb)
    return top


def tearDown():
    uvm_root().clear_hierarchy()


class my_test(uvm_test):
    async def run_phase(self):
        self.raise_objection()
        print("Hey, I'm here")
        self.drop_objection()


@cocotb.test()
async def run_test(dut):
    """Test the various nowait flavors"""
    await uvm_root().run_test("my_test")
    assert True


@cocotb.test()
async def test_stub(dut):
    """testing the basic testing mechanism"""
    top = setUp()
    top.build_phase()
    assert "top" == phase_list["build_phase"][0]
    tearDown()


async def test_traverse():
    top = setUp()
    top_down = ["top", "aa", "cc", "dd", "bb", "ee", "ff"]
    bottom_up = ["cc", "dd", "aa", "ee", "ff", "bb", "top"]
    sorted_list = sorted(top_down)
    for phase_class in uvm_common_phases:
        phase = phase_class()
        phase.traverse(top)
        if phase_class == uvm_run_phase:
            await utility_classes.ObjectionHandler().run_phase_complete()
        function_name = phase_class.__name__[4:]
        returned_comps = phase_list[function_name]
        try:
            if isinstance(phase, uvm_run_phase):
                assert sorted_list == sorted(returned_comps)
            elif isinstance(phase, uvm_topdown_phase):
                assert top_down == returned_comps
            elif isinstance(phase, uvm_bottomup_phase):
                assert bottom_up == returned_comps
            else:
                # Should not get here.
                assert False
        except AssertionError:
            tearDown()
            return False
    tearDown()
    return True


@cocotb.test()
async def traverse(self):
    """Testing topdown and bottom up traversal"""
    assert await test_traverse()
