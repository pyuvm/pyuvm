from pyuvm import uvm_object
from s13_predefined_component_classes import *
import error_classes
import threading
import utility_classes
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

    def execute(self, comp):
        """
        Strips the "uvm_" from this class's name and uses the remainder
        to get a function call out of the component and execute it.

        :param comp: The component whose turn it is to execute
        """
        assert(isinstance(self, common_phase)), "We only support phases whose names start with uvm_"
        method_name = self.get_type_name()[4:]
        try:
            method = getattr(comp, method_name)
        except AttributeError:
            raise error_classes.UVMBadPhase(f"{comp.get_name()} is missing {method_name} function")
        method(self)

    def raise_objection(self):
        """
        Does whatever one does to keep the sim runnng
        """

    def drop_objection(self):
        """
        Does whatever one does to let the sim finish
        """

class uvm_topdown_phase(uvm_phase):
    """
    Runs phases from the top down.
    """

    def traverse(self, comp):
        """
        Given a component, we traverse the component tree
        top to bottom calling the phase functions as we go
        :param comp: The component whose hierarchy will be tranversed
        """
        assert(comp, uvm_component), "You can only traverse uvm_components with a phase"
        self.execute(comp) # first we execute this node then its children
        for child in comp.get_children():
            self.traverse(child)

class uvm_bottomup_phase(uvm_phase):
    """
    Runs the phases from bottom up.
    """
    def traverse(self, comp):
        assert(comp, uvm_component), "You can only traverse uvm_components with a phase"
        for child in comp.get_children():
            self.traverse(child)
        self.execute(comp)

class uvm_threaded_execute_phase(uvm_phase):
    """
    This phase launches the phase function in a thread and
    returns the thread to the caller.  The caller can then
    join all the threads.
    """

# 9.8 Predefined Phases
# 9.8.1 Common Phases
# These are all Singleton objects
class common_phase():
    """
    This is used for a simple error checking line.
    """
    ...

# The common phases are described in the order of their execution.
# 9.8.1.1
class uvm_build_phase(common_phase):
    ...

# 9.8.1.2
class uvm_connect_phase(common_phase):
    ...

# 9.8.1.3
class uvm_end_of_elaboration_phase(common_phase):
    ...

# 9.8.1.4
class uvm_start_of_simulation_phase(common_phase):
    ...

# 9.8.1.5
class uvm_run_phase(common_phase):
    ...

# 9.8.1.6
class uvm_extract_phase(common_phase):
    ...

# 9.8.1.7
class uvm_check_phase(common_phase):
    ...

# 9.8.1.8
class uvm_report_phase(common_phase):
    ...

# 9.8.1.9
class uvm_final_phase(common_phase):
    ...
# 9.8.2
# Left as an exercise for an enterprising soul


