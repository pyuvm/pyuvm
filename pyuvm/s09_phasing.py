from pyuvm.s05_base_classes import uvm_object
import pyuvm.error_classes as error_classes
import cocotb

# 9.1
#
# This is a dramatically simplified version of UVM phasing. We are not going
# to deal with the complexities of custom phasing as described in IEEE 1800.2
# #
# So this system simply traverses the common phases, calling the appropriate
# method in each component.
#
# Much of the work in the SV phasing code has to do with handling the passage
# of time. We use cocotb for our simulation interaction, so that all goes away.
#
# Also, the generalized phasing system is rarely used and so that
# is left as an exercise for future developers.  Instead we have a simple
# topdown and bottom up traversal of calling methods in component
# classes based on the phase name.
#
# We're not doing schedules or domains. We're just creating a list of classes
# and traversing them in order. The order it dependent upon whether they
# are topdown or bottom up phases.


# 9.3.1.2 Class declaration
class uvm_phase(uvm_object):

    # Strips the "uvm_" from this class's name and uses the remainder
    # to get a function call out of the component and execute it.
    # 'uvm_run_phase' becomes 'run_phase' and is called as 'run_phase()'
    @classmethod
    def execute(cls, comp):
        """
        :param comp: The component whose turn it is to execute
        """
        method_name = cls.__name__[4:]
        try:
            method = getattr(comp, method_name)
        except AttributeError:
            raise error_classes.UVMBadPhase(
                f"{comp.get_name()} is missing {method_name} function")
        method()

    def __str__(self):
        return self.__name__[4:]


class uvm_topdown_phase(uvm_phase):
    """
    Runs phases from the top down.
    """
    @classmethod
    def traverse(cls, comp):
        """
        :param comp: The component whose hierarchy will be traversed

        Given a component, we traverse the component tree
        top to bottom calling the phase functions as we go
        """
        cls.execute(comp)  # first we execute this node then its children
        for child in comp.get_children():
            cls.traverse(child)


class uvm_bottomup_phase(uvm_phase):
    """
    Runs the phases from bottom up.
    """
    @classmethod
    def traverse(cls, comp):
        """
        :param comp: The component whose hierarchy will be traversed

        Given a component, we traverse the component tree
        bottom to top calling the phase functions as we go
        """
        for child in comp.get_children():
            cls.traverse(child)
        cls.execute(comp)


class uvm_threaded_execute_phase(uvm_phase):
    """
    This phase launches the phase function in a thread and
    returns the thread to the caller.  The caller can then
    join all the threads.
    """

    @classmethod
    def execute(cls, comp):
        phase_name = cls.__name__
        assert phase_name.startswith("uvm_"), \
            "We only support phases whose names start with uvm_"
        method_name = cls.__name__[4:]
        try:
            method = getattr(comp, method_name)
        except AttributeError:
            raise error_classes.UVMBadPhase(
                f"{comp.get_name()} is missing {method_name} function")
        cocotb.start_soon(method())


# 9.8 Predefined Phases
# 9.8.1 Common Phases
# The common phases are described in the order of their execution.
# 9.8.1.1
class uvm_build_phase(uvm_topdown_phase):
    ...


# 9.8.1.2
class uvm_connect_phase(uvm_bottomup_phase):
    ...


# 9.8.1.3
class uvm_end_of_elaboration_phase(uvm_topdown_phase):
    ...


# 9.8.1.4
class uvm_start_of_simulation_phase(uvm_topdown_phase):
    ...


# 9.8.1.5
class uvm_run_phase(uvm_threaded_execute_phase, uvm_bottomup_phase):
    ...


# 9.8.1.6
class uvm_extract_phase(uvm_topdown_phase):
    ...


# 9.8.1.7
class uvm_check_phase(uvm_topdown_phase):
    ...


# 9.8.1.8
class uvm_report_phase(uvm_topdown_phase):
    ...


# 9.8.1.9
class uvm_final_phase(uvm_topdown_phase):
    ...


# 9.8.2
# UVM run-time phases are left as an exercise for an enterprising soul
# I cannot imagine why anyone would implement this.
# One could add phases by simply extending uvm_topdown_phase
# or uvm_bottom_up phase with a new phase named 'uvm_my_phase' and adding
# the my_phase() method to a uvm component with setattr.  Then insert the new
# phase into the list of phases to be executed below:

uvm_common_phases = [uvm_build_phase,
                     uvm_connect_phase,
                     uvm_end_of_elaboration_phase,
                     uvm_start_of_simulation_phase,
                     uvm_run_phase,
                     uvm_extract_phase,
                     uvm_check_phase,
                     uvm_report_phase,
                     uvm_final_phase]
