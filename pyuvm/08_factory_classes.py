'''
Most of the UVM factory code stems from SystemVerilog's lack
of introspection.

This etnire section can essentially be replaced with this:

import sys
class Foo:


ff = getattr(sys.modules[__name__],'Foo')
print(ff)

Factory behavior is now part of the uvm_object class.
'''
