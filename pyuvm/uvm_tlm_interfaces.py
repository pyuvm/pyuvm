'''
The UVM TLM class hierarchy wraps the behavior of objects (usually Queues) in
a set of classes and objects.

The UVM LRM calls for three levels of classes to implement TLM: ports, exports,
and imp:
(from 12.2.1)

* ports---Instantiated in components that require or use the associate interface
to initiate transaction requests.

* exports---Instantiated by components that forward an implementation of
the methods defined in the associated interface.

* imps---Instantiated by components that provide an implementation of or
directly implement the methods defined.

This is all a bit much for Python which, because of dynamic typing doesn't
need so many layers.

Specifically, pyuvm implements the _imp classes using an abstact base
class and any class that extends the _imp class must provide the associated
functions (becoming an 'export')  There is no longer a need for the
export classes since we don't have to define variables that "forward" the
interface.

Therefore we do not implement 12.2.6
'''

from predefined_component_classes import uvm_component
from queue import Full as QueueFull, Empty as QueueEmpty, Queue
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
12.2.7
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
    def get(self):
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
    def peek(self):
        pass

class uvm_nonblocking_peek_imp(ABC):
    @abstractmethod
    def try_peek(self):
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

class uvm_nonblocking_transport_imp( ABC ):
    @abstractmethod
    def nb_transport(self, req):
        '''
        As above we return None when the UVM version would
        return 0.  Otherwise we return rsp.
        :param req: Request
        :return: rsp as Response
        '''
        return None

class uvm_transport_imp( uvm_blocking_transport_imp, uvm_nonblocking_transport_imp ):
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
12.2.5
Port Classes

The following port classes can be connected to "export" classes.
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


'''
12.2.8 FIFO Classes

These classes provide synchronization control between
threads using the Queue class.

One note.  The RLM has only 12.2.8.1.3 and 12.2.8.1.4, put_export
and get_peek_export, but the UVM code has all the variants
of exports. 

The SystemVerilog UVM relies upon static type checking
and polymorphism to make sure that users connect the
correct ports to these exports, but we don't have
static checking, so we implement classes for all the
port variants. This creates the runtime assertion checking
that we need.
'''

class uvm_tlm_fifo_base(uvm_component):

    class BlockingPutExport(uvm_blocking_put_imp):
        def put(self,item):
            self.__queue.put(item)
            self.put_ap(item)

    class NonBlockingPutExport(uvm_nonblocking_put_imp):
        '''
        12.2.8.1.3
        '''

        def can_put(self):
            return not self.__queue.full()

        def try_put(self, item):
            try:
                self.__queue.put_nowait ( item )
                self.put_ap(item)
                return True
            except QueueFull:
                return False

    class PutExport(BlockingPutExport, NonBlockingPutExport): ...

    class BlockingGetExport(uvm_blocking_get_imp):
        def get(self):
            item = self.__queue.get()
            self.get_ap(item)
            return item

    class NonBlockingGetExport(uvm_nonblocking_get_imp):
        def can_get(self):
            return not self.__queue.empty()

        def try_get(self):
            try:
                item = self.__queue.get_nowait ()
                self.get_ap(item)
                return item
            except QueueEmpty:
                return None


    class GetExport(BlockingGetExport, NonBlockingGetExport):...

    class BlockingPeekExport(uvm_blocking_peek_imp):
        def peek(self):
            while self.__queue.empty ():
                self.__queue.not_empty.wait ()
            queue_data = self.__queue.queue
            return queue_data[0]

    class NonBlockingPeekExport(uvm_nonblocking_peek_imp):
        def can_peek(self):
            return not self.__queue.empty()

        def try_peek(self):
            if self.__queue.empty():
                return None
            else:
                return self.__queue.queue[0]

    class PeekExport(BlockingPeekExport, NonBlockingPeekExport): ...

    class BlockingGetPeekExport(BlockingGetExport, BlockingPeekExport):...

    class NonBlockingGetPeekExport(NonBlockingGetExport, NonBlockingPeekExport):...

    class GetPeekExport(GetExport, PeekExport):
        '''
        12.2.8.1.4
        '''

    def __init__(self, name, parent):
        super().__init__(name,parent)
        self.__queue=None

        self.put_export=self.PutExport()
        self.blocking_put_export=self.BlockingPutExport()
        self.nonblocking_get_export = self.NonBlockingPutExport()

        self.get_peek_export=self.GetPeekExport()
        self.blocking_get_peek_export=self.BlockingGetPeekExport()
        self.nonblocking_get_peek_export=self.NonBlockingGetPeekExport()

        self.blocking_get_export = self.BlockingGetExport()
        self.nonblocking_get_export = self.NonBlockingGetExport()
        self.get_export = self.GetExport()

        self.blocking_peek_export = self.BlockingPeekExport()
        self.nonblocking_peek_export = self.NonBlockingPeekExport()
        self.peek_export = self.PeekExport()

        self.blocking_get_peek_export = self.BlockingGetPeekExport()
        self.nonblocking_get_peek_export = self.NonBlockingGetPeekExport()
        self.get_peek_export=self.GetPeekExport()

        self.get_ap=uvm_analyis_port()
        self.put_ap=uvm_analyis_port()

class uvm_tlm_fifo(uvm_tlm_fifo_base):

    def __init__(self, size=1):
        super().__init__()
        self.__queue=Queue(maxsize=size)

    def size(self):
        return self.__queue.maxsize

    def used(self):
        return self.qsize(self)

    def is_empty(self):
        return self.__queue.empty()

    def is_full(self):
        return self.__queue.full()

    def flush(self):
        '''
        The SystemVerilog UVM flushes the Queue
        using a while loop and counting the number
        of threads waiting for a get. If there are
        still threads waiting after the loop runs
        it issues an error.

        In pyuvm we just flush the loop and clear
        all the unfinished tasks.
        :return: None
        '''
        self.__queue.mutex.acquire()
        self.__queue.queue.clear()
        self.__queue.all_tasks_done.notify_all()
        self.__queue.unfinished_tasks=0
        self.__queue.mutex.release()

class uvm_tlm_analysis_fifo(uvm_tlm_fifo):

    class AnalysisExport(uvm_analysis_imp):
        def write(self, item):
            try:
                self.__queue.put_nowait(item)
            except QueueFull:
                raise QueueFull(f"Full analysis fifo: {self.fullname}. This should never happen")

    def __init__(self):
        super().__init__(0)
        self.analysis_export = self.AnalysisExport()

class uvm_tlm_req_rsp_channel(uvm_component):
    '''
    12.2.9.1
    '''

    class MasterSlaveExport ( uvm_master_imp ):
        def __init__(self, put_export, get_peek_export):
            self.put_export = put_export
            self.get_peek_export = get_peek_export

        def put(self, item):
            self.put_export.put ( item )

        def can_put(self):
            return self.put_export.can_put ()

        def try_put(self, item):
            return self.put_export.try_put ( item )

        def get(self):
            return self.get_peek_export.get ()

        def can_get(self):
            return self.get_peek_export.can_get ()

        def try_get(self):
            return self.get_peek_export.try_get

    def __init__(self, name, parent=None, request_fifo_size=1, response_fifo_size = 1):
        self.__req_tlm_fifo = uvm_tlm_fifo("request_fifo", self, request_fifo_size)
        self.__rsp_tlm_fifo = uvm_tlm_fifo("rsponse_fifo")

        self.put_request_export = self.__req_tlm_fifo.put_export # 12.2.9.1.3
        self.get_peek_response_export = self.__rsp_tlm_fifo.get_peek_export # 12.2.9.1.4
        self.get_peek_request_export = self.__req_tlm_fifo.get_peek_export #12.2.9.1.5
        self.put_response_export = self.__rsp_tlm_fifo.put_export #12.2.9.1.6
        self.request_ap = uvm_analyis_port("request_ap", self) #12.2.9.1.7
        self.response_ap = uvm_analyis_port("response_ap", self) #12.2.9.1.8

        self.master_export = self.MasterSlaveExport(self.put_request_export, self.get_peek_response_export) #12.2.9.1.9
        self.slave_export  = self.MasterSlaveExport(self.get_peek_request_export, self.put_response_export) #12.2.9.1.10

    def connect_phase(self):
        self.request_ap.connect(self.__req_tlm_fifo.put_ap) #12.2.9.1.7
        self.response_ap.connect(self.__rsp_tlm_fifo.get_ap) #12.2.9.1.8

class uvm_tlm_transport_channel(uvm_tlm_req_rsp_channel):
    '''

    '''
    class TransportExport(uvm_transport_imp):
        def transport(self, req):
            self.__req_tlm_fifo.put_export.put(req)
            return self.__rsp_tlm_fifo.get_peek_export.get()

        def nb_transport(self, req):
            if not self.__req_tlm_fifo.put_export.try_put(req):
                return False
            return self.__rsp_tlm_fifo.get_peek_export.try_get()

    def __init__(self, name, parent=None):
        super().__init__(name, parent, 1, 1)
        self.transport_export=self.TransportExport


'''
UVM TLM 2
12.3

This is left for future development.
'''
