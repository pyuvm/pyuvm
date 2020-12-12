from pyuvm.s05_base_classes import uvm_object
import pyuvm.error_classes as error_classes
import threading
import pyuvm.utility_classes as utility_classes

'''
9.1

This is a dramatically simplified version of UVM phasing. We don't have
to deal with simulation time and we are not going to deal with a generalized
phasing system.

So this system simply traverses the common phases, calling the appropriate
method in each component.

Much of the work in the SV phasing code has to do with handling the passage
of time.  There is no timewheel in Python, so all of that code can go
away.
 
Also, the generalized phasing system is rarely used and so that 
is left as an exercise for future developers.  Instead we have a simple
topdown and bottom up traversal of calling methods in component
classes based on the phase name.

We're not doing schedules or domains. We're just creating a list of classes
and traversing them in order. The order it dependent upon whether they
are topdown or bottom up phases.

'''


# 9.3.1.2 Class declaration


class uvm_phase(uvm_object):

    @classmethod
    def execute(cls, comp):
        """
        Strips the "uvm_" from this class's name and uses the remainder
        to get a function call out of the component and execute it.

        :param comp: The component whose turn it is to execute
        """
        assert (issubclass(cls, common_phase)), "We only support phases whose names start with uvm_"
        method_name = cls.__name__[4:]
        try:
            method = getattr(comp, method_name)
        except AttributeError:
            raise error_classes.UVMBadPhase(f"{comp.get_name()} is missing {method_name} function")
        method()




class uvm_topdown_phase(uvm_phase):
    """
    Runs phases from the top down.
    """
    @classmethod
    def traverse(cls, comp):
        """
        Given a component, we traverse the component tree
        top to bottom calling the phase functions as we go
        :param comp: The component whose hierarchy will be traversed
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
        assert (issubclass(cls, common_phase)), "We only support phases whose names start with uvm_"
        method_name = cls.__name__[4:]
        try:
            method = getattr(comp, method_name)
        except AttributeError:
            raise error_classes.UVMBadPhase(f"{comp.get_name()} is missing {method_name} function")
        fork = threading.Thread(target=method, name=comp.get_full_name())
        fork.start()
        utility_classes.RunningThreads().add_thread(fork)


# 9.8 Predefined Phases
# 9.8.1 Common Phases
class common_phase():
    """
    This is used for a simple error checking line.
    """
    ...


# The common phases are described in the order of their execution.
# 9.8.1.1
class uvm_build_phase(uvm_topdown_phase, common_phase):
    ...


# 9.8.1.2
class uvm_connect_phase(uvm_bottomup_phase, common_phase):
    ...


# 9.8.1.3
class uvm_end_of_elaboration_phase(uvm_topdown_phase, common_phase):
    ...


# 9.8.1.4
class uvm_start_of_simulation_phase(uvm_topdown_phase, common_phase):
    ...


# 9.8.1.5
class uvm_run_phase(uvm_threaded_execute_phase, uvm_bottomup_phase, common_phase):
    ...


# 9.8.1.6
class uvm_extract_phase(uvm_topdown_phase, common_phase):
    ...


# 9.8.1.7
class uvm_check_phase(uvm_topdown_phase, common_phase):
    ...


# 9.8.1.8
class uvm_report_phase(uvm_topdown_phase, common_phase):
    ...


# 9.8.1.9
class uvm_final_phase(uvm_topdown_phase, common_phase):
    ...


# 9.8.2
# Left as an exercise for an enterprising soul

uvm_common_phases = [uvm_build_phase, uvm_connect_phase,
                     uvm_end_of_elaboration_phase, uvm_start_of_simulation_phase,
                     uvm_run_phase, uvm_extract_phase, uvm_check_phase,
                     uvm_report_phase, uvm_final_phase]
