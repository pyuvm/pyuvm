'''
The UVM TLM class hierarchy wraps the behavior of objects (usually Queues) in
a set of classes and objects.  There are three levels of object that
deliver functionality to the user.

The _imp classes are abstract base classes (like pure virutual classes)
that define
'''

from predefined_component_classes import uvm_component
from queue import Full as QueueFull, Empty as QueueEmpty
from abc import ABC, abstractmethod
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

'''
Old SystemVerilog (pre-2012) did not have interfaces in 
the sense that Java or C++ did.  There was no way to 
promise that a given class would implement a function
call such as put() or get(). 

To work around this, the developers created the concept
of an _imp.  You instantiated the _imp in your component
and the _imp would make a call to the required method. If
you hadn't supplied the method you got a run-time error. 
(Quasi-duck typing.)

The most common example of this is the uvm_subscriber which
instantiates a subscriber imp and requires that someone
who extends uvm_subscriber create a write() method.n

Since Python has the concept of an Abstract Base Class
and since Python has multiple inheritance, we will implement
the _imp classes as abstract base classes.  This will
'''

class pyuvm_export_base(uvm_component):
    '''
    This class does not exist in the UVM LRM, since
    the UVM LRM uses a data member in the uvm_port_base
    to say what kind of behavior it is implementing.

    All predefined exports in pyuvm instantiate a
    Python Queue, so we do that here.

    '''

    def __init__(self, name, parent, queue):
        '''
        The export in pyuvm carries the Queue stored in a
        tlm_fifo and provides the get and put methods to
        interact with that Queue.

        This means that if you instantiate the correct
        export you will only be able to access the
        queue in the ways intended (no putting in a get.)

        You cannot instantiate an export without providing
        a Queue since that makes no sense.

        :param queue: The communication queue
        '''
        super().__init__(name, parent)
        assert(isinstance(queue,Queue))
        self.__queue=queue

    @property
    def queue(self):
        return self.__queue

'''
The _imp classes force users to implement the correct
interface for the various TLM directions. 
'''

class uvm_blocking_put_imp(ABC):
    @abstractmethod
    def put(self,item):
        pass

class uvm_nonblocking_put_imp(ABC):
    @abstractmethod
    def try_put(self,item):
        return None

    @abstractmethod
    def can_put(self):
        return False

class uvm_put_imp(uvm_blocking_put_imp,uvm_nonblocking_put_imp):
    '''
    Combination of the previous two
    '''

class uvm_blocking_get_imp(ABC):
    @abstractmethod
    def get(self,item):
        pass

class uvm_nonblocking_get_imp(ABC):
    @abstractmethod
    def try_get(self,item):
        return None

    @abstractmethod
    def can_get(self):
        return False

class uvm_analysis_imp(ABC):
    @abstractmethod
    def write(self, item):
        pass

class uvm_get_imp(uvm_blocking_get_imp,uvm_nonblocking_get_imp):
    '''
    Combination of the previous two
    '''

class uvm_blocking_peek_imp(ABC):
    @abstractmethod
    def peek(self,item):
        pass

class uvm_nonblocking_peek_imp(ABC):
    @abstractmethod
    def try_peek(self,item):
        return None

    @abstractmethod
    def can_peek(self):
        return False

class uvm_peek_imp(uvm_blocking_peek_imp,uvm_nonblocking_peek_imp):
    '''
    Combination of the previous two
    '''

class uvm_blocking_get_peek_imp(uvm_blocking_get_imp, uvm_blocking_peek_imp):
    '''
    Combine the above
    '''

class uvm_nonblocking_get_peek_imp(uvm_nonblocking_get_imp,uvm_nonblocking_peek_imp):
    '''
    Combining the above
    '''

class uvm_get_peek_imp(uvm_get_imp, uvm_peek_imp):
    '''
    Combing the above
    '''

class uvm_blocking_transport_imp(ABC):
    @abstractmethod
    def transport(self, req):
        '''
        The UVM returns the rsp through the
        parameter list, but we don't do that
        in Python.  So we return either rsp
        or None.
        :param req: Request
        :return: rsp
        '''
        return None

class uvm_non_blocking_transport_imp(ABC):
    @abstractmethod
    def nb_transport(self, req):
        '''
        As above we return None when the UVM version would
        return 0.  Otherwise we return rsp.
        :param req: Request
        :return: rsp as Response
        '''
        return None

class uvm_transport_imp(uvm_blocking_transport_imp, uvm_non_blocking_transport_imp):
    '''
    Must provide both of the above.
    '''

class uvm_blocking_master_imp(uvm_blocking_put_imp, uvm_blocking_get_peek_imp):
    '''
    Everybody blocks
    '''

class uvm_nonblocking_master_imp(uvm_nonblocking_put_imp, uvm_nonblocking_get_peek_imp):
    '''
    Nobody blocks
    '''

class uvm_master_imp(uvm_nonblocking_master_imp, uvm_blocking_master_imp):
    '''
    Block or don't, your choice.
    '''

class uvm_blocking_slave_imp(uvm_blocking_put_imp, uvm_blocking_get_peek_imp):
    '''
    Everybody blocks
    '''

class uvm_nonblocking_slave_imp(uvm_nonblocking_put_imp, uvm_nonblocking_get_peek_imp):
    '''
    Nobody blocks
    '''

class uvm_slave_imp(uvm_nonblocking_slave_imp, uvm_blocking_slave_imp):
    '''
    Block or don't, your choice.
    '''

'''
Export Classes
'''

class pyuvm_tlm_export_base(pyuvm_export_base):
    '''
    Accepts a queue that it will use to implement
    TLM.
    '''
    def __init__(self, name, parent, queue):
        assert(queue.maxqueue == 1), f'Tried to create a blocking export using a queue with maxsize not 1'
        super().__init__(name, parent, queue)

class pyuvm_analysis_export_base(pyuvm_export_base):
    def __init__(self, name, parent, queue):
        assert(queue.maxqueue == 0), f'Tried to create an analysis export using a blocking queue'
        super().__init__(name, parent, queue)

class uvm_blocking_put_export(pyuvm_tlm_export_base, uvm_blocking_put_imp):
    def put(self,item):
        self.__queue.put(item, block=True)

class uvm_nonblocking_put_export(pyuvm_tlm_export_base, uvm_nonblocking_put_imp):
    def try_put(self,item):
        try:
            self.__queue.put_nowait(item)
            return True
        except QueueFull:
            return False

    def can_put(self):
        return not self.__queue.full()

class uvm_put_export(uvm_blocking_put_export, uvm_nonblocking_put_export, uvm_put_imp):
    '''
    Combines the functions of blocking and non_blocking put
    '''

class uvm_blocking_get_export(pyuvm_tlm_export_base, uvm_blocking_get_imp):
    def get(self):
        return self.__queue.get()

class uvm_nonblocking_get_export(pyuvm_tlm_export_base, uvm_nonblocking_get_imp):
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

class uvm_get_export(uvm_blocking_get_export, uvm_nonblocking_get_export, uvm_get_imp):
    '''
    Combines the functions of blocking and non_blocking get
    '''

class uvm_blocking_peek_export(pyuvm_tlm_export_base, uvm_blocking_peek_imp):
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

class uvm_nonblocking_peek_export(pyuvm_tlm_export_base, uvm_nonblocking_peek_imp):

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

class uvm_blocking_get_peek_export(uvm_blocking_get_export, uvm_blocking_peek_export, uvm_blocking_get_peek_imp):
    '''
    Combining the above two
    '''

class uvm_nonblocking_get_peek_export(uvm_nonblocking_get_export, uvm_nonblocking_peek_export, uvm_nonblocking_get_peek_imp):
    '''
    Combining the above two
    '''

class uvm_get_peek_export(uvm_get_export, uvm_peek_export, uvm_get_peek_imp):
    '''
    All together now!
    '''

class uvm_analysis_export(pyuvm_analysis_export_base, uvm_analysis_imp):
    def write(self,item):
        self.__queue.put(item)

'''
Port Classes

The following port classes can be connected to export classes.
They check that the export is of the correct type.

uvm_port_base adds the correct methods to this class
rather than reference them because Python allows 
you to assign functions to objects dynamically.
'''

class uvm_port_base(uvm_component):
    '''
    port classes expose the tlm methods to
    the object that instantiates them.  We extend
    this class to create the variety of ports and
    pass this class the implementation type that
    defines the needed methods (put(), get(),
    nb_transport(), etc)

    Connect dynamically adds the functions'
    concrete implementations to the port and
    wraps them so that port.put() calls export.put()



    '''

    def __init__(self, name, parent, imp_type):
        super().__init__(name, parent)
        self.connected_to={}
        self._imp_type=imp_type
        self.uvm_methods = [uvm_method
                            for uvm_method in dir ( imp_type )
                            if isinstance( getattr( imp_type, uvm_method ), FunctionType )]

    def connect(self, export):
        '''
        connect() takes an object that implements _imp_type
        and wraps its implementing methods in the port. That
        way any port can deliver the methods of any imp
        :param export: The concrete object that implements imp
        :return: None
        '''
        isinstance( export, self._imp_type )
        self.__export=export
        self.connected_to[export.full_name]=export
        export.provided_to[self.full_name]=self
        for method in self.uvm_methods:
            exec( f'self.{method}=self.__export.{method}' )


class uvm_blocking_put_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_blocking_put_imp)

class uvm_nonblocking_put_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_nonblocking_put_imp)

class uvm_put_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name,parent, uvm_put_imp)

class uvm_blocking_get_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_blocking_get_imp)

class uvm_nonblocking_get_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_nonblocking_get_imp)

class uvm_get_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name,parent, uvm_get_imp)

class uvm_blocking_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_blocking_peek_imp)

class uvm_nonblocking_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_nonblocking_peek_imp)

class uvm_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name,parent, uvm_peek_imp)

class uvm_blocking_get_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_blocking_get_peek_imp)

class uvm_nonblocking_get_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_nonblocking_get_peek_imp)

class uvm_get_peek_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name,parent, uvm_get_peek_imp)

class uvm_analyis_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent, uvm_analysis_imp)








