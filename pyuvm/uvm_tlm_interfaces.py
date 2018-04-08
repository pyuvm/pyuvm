'''
The SystemVerilog UVM was built for a statically typed language
that lacked (at the time) OOP interfaces.  The UVM developers
worked around this problem by creating classes (imp) that delivered
the behavior associated with an interface.

Python is not statically typed and, while there is an `interface`
module that delivers interface behavior,  this is not a Pythonic
way of coding.

Python's duck-typing says that you'll get errors when you try
to use a class improperly, there is less emphasis on not allowing
the program to even compile if there is an error.

All of this also applies to the paramaterized typing in the UMV
TLM SystemVerilog implementation.  This is also unnecessary.

That said, asking users to use the basic Queue class for TLM commmunication
is a suboptimal solution.  There is no mechanism to enforce putting
and getting in the right places and while you can write code in
Python that references a Queue that you expect upper level code to
provide, there is no guarantee that the Queue will be provided with
the correct name.  Hilarity would ensue.

This file implements the basics of UVM TLM without the overhead
needed to do the job in old SystemVerilog.
'''

from base_classes import uvm_policy, pyuvm_export_base, uvm_component, uvm_object, uvm_port_base
from queue import Full as QueueFull, Empty as QueueEmpty
from types import FunctionType
'''
12.2.2
This section describes a variety of classes without
giving each one its own section using * to represent
a variety of implementations (get, put, blocking_put, etc)

Python provides multiple inheritance and we'll use that below
to smooth implementation. Python does not require that we
repeat the __init__ for classes that do not change the 
__init__ functionality.
'''

class pyuvm_tlm_export_base(pyuvm_export_base):
    def __init__(self, name, parent, queue):
        assert(queue.maxqueue == 1), f'Tried to create a blocking export using a queue with maxsize not 1'
        super().__init__(name, parent, queue)

class pyuvm_analysis_export_base(pyuvm_export_base):
    def __init__(self, name, parent, queue):
        assert(queue.maxqueue == 0), f'Tried to create an analysis export using a blocking queue'
        super().__init__(name, parent, queue)


class uvm_blocking_put_export(pyuvm_tlm_export_base):
    def put(self,item):
        self.__queue.put(item, block=True)

class uvm_nonblocking_put_export(pyuvm_tlm_export_base):
    def try_put(self,item):
        try:
            self.__queue.put_nowait(item)
            return True
        except QueueFull:
            return False

    def can_put(self):
        return not self.__queue.full()


class uvm_put_export(uvm_blocking_put_export, uvm_nonblocking_put_export):
    '''
    Combines the functions of blocking and non_blocking put
    '''
class uvm_blocking_get_export(pyuvm_tlm_export_base):
    def get(self):
        return self.__queue.get()


class uvm_nonblocking_get_export(pyuvm_tlm_export_base):
    '''
    Python doesn't support call by reference, so we'll
    return None if try_get doesn't get a value.
    '''
    def try_get(self):
        try:
            return self.__queue.get_nowait()
        except QueueEmpty:
            return None

    def can_get(self):
        return not self.__queue.empty()

class uvm_get_export(uvm_blocking_get_export, uvm_nonblocking_get_export):
    '''
    Combines the functions of blocking and non_blocking get
    '''

class uvm_blocking_peek_export(pyuvm_tlm_export_base):
    '''
    Python Queues look down upon peeking and do not
    provide that function inherently.  We need
    to hack our way around to get what we want
    '''

    def peek(self):
        while self.__queue.empty():
            self.__queue.not_empty.wait()
        queue_data = self.__queue.queue
        return queue_data[0]


class uvm_nonblocking_peek_export(pyuvm_tlm_export_base):

    def try_peek(self):
        if self.__queue.empty():
            return None
        else:
            return self.__queue.queue[0]

    def can_peek(self):
        return not self.__queue.empty()


class uvm_peek_export(uvm_blocking_peek_export,uvm_nonblocking_peek_export):
    '''
    Combine the above two
    '''

class uvm_blocking_get_peek_export(uvm_blocking_get_export, uvm_blocking_peek_export):
    '''
    Combining the above two
    '''

class uvm_nonblocking_get_peek_export(uvm_nonblocking_get_export, uvm_nonblocking_peek_export):
    '''
    Combining the above two
    '''
class uvm_get_peek_export(uvm_get_export, uvm_peek_export):
    '''
    All together now!
    '''

class uvm_analysis_export(pyuvm_analysis_export_base):
    def write(self,item):
        self.__queue.put(item)

'''
Port Classes

The following port classes can be connected to export classes.
They check that the export is of the correct type.

uvm_port_base adds the correct methods to this class
because Python allows you to assign functions to
objects dynamically.
'''

class uvm_blocking_put_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_blocking_put_export)

class uvm_nonblocking_put_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_nonblocking_put_export)

class uvm_put_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name,parent, uvm_put_export)

class uvm_blocking_get_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_blocking_get_export)

class uvm_nonblocking_get_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_nonblocking_get_export)

class uvm_get_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name,parent, uvm_get_export)

class uvm_blocking_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_blocking_peek_export)

class uvm_nonblocking_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_nonblocking_peek_export)

class uvm_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name,parent, uvm_peek_export)

class uvm_blocking_get_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_blocking_get_peek_export)

class uvm_nonblocking_get_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_nonblocking_get_peek_export)

class uvm_get_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name,parent, uvm_get_peek_export)

class uvm_analyis_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_analysis_export)


'''
12.2.3.1
Creating the bidirectional transport functionality
'''







