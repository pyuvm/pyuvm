import 05_base_classes

'''
This section and sequences are the crux of pyuvm. The classes here allow us to build classic UVM
testbenches in Python.

Section 13 of the IEEE-UVM Refernce Manual (1800.2-2017) lists five pieces of uvm_component functionality.
pyuvm implements much of this functionality using Python:

a: Hierarchy---This is implemented in pyuvm
b: Phasing---This is also implemented in pyuvm, but is hardcoded to the standard UVM phases.
c: Hierarchical Reporting---We manage this with the logging module. It is orthogonal to the components.
d: Transaction Recording---We do not record transactions since pyuvm does not run in the simulator. This
could be added later if we see a need or way to do it.
e: Factory---pyuvm manages the factory throught the create() method without all the SystemVerilog typing overhead.

'''

# Class Declarations

class uvm_component(uvm_object):
    '''
The specification calls for uvm_component to extend uvm_report_object. However, pyuvm
uses the logging module orthogonally to class structure. It may be that in future
we find a reason to wrap the basic logging package in the uvm code, but at this point
we are better off leaving logging to itself.

The choice then becomes whether to create a uvm_report_object class as a placeholder
to preserve the UVM reference manual hierarchy or to code what is really going on.
We've opted for the latter.
    '''