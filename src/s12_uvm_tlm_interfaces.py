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

These three levels are unecessary for Python because Python has
multiple inheritances and duck typing.  You don't need to define
different ports for each type being transferred.

Ports have a data member named an export that implements the port
functionality. uvm_put_port.put() calls its export.put(). Ports get
their various flavors through multiple inheritance.

'''

from s13_predefined_component_classes import uvm_component
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
12.2.5
Port Classes

The following port classes can be connected to "export" classes.
They check that the export is of the correct type.

uvm_port_base adds the correct methods to this class
rather than reference them because Python allows 
you to assign functions to objects dynamically.
'''

class uvm_port_base(uvm_component):
    """
    A uvm_port_base is a uvm_component with a connect() function.
    The connect function creates an __export data member that
    implements the put/get,etc methods.

    We'll build functionality from uvm_port_base to create the
    other combinations of ports through multiple inheritance.

    pyuvm will make extensive use of Pythons "ask forgiveness" policy
    If you try to use the wrong method for the port you created
    then you'll get a exception, maybe a missing attribute one, though
    we could catch that one and deliver a more useful message.

    Unlike the SV implementation of UVM we return results from get and peek
    as function call returns. This is more pythonic.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.connected_to={}
        self.__export = None

    def connect(self, export):
        """
        Attach this port to the associated export.
        :param export:
        :return:
        """
        self.__export=export
        self.connected_to[export.get_full_name()]=export
        export.provided_to[self.get_full_name()]=self

class uvm_blocking_put_port(uvm_port_base):
    """
    12.2.5.1
    Access the blocking put interfaces
    """
    def __init__(self, name, parent):
        super().__init__(name, parent)

    def put(self, data):
        """
        12.2.4.2.1
        A blocking put that calls the export.put
        :param data:
        :return: None
        """
        self.__export.put(data)

class uvm_blocking_get_port(uvm_port_base):
    """
    12.2.5.1
    Access the blocking get export methods
    """
    def get(self):
        """
        12.2.4.2.2
        A blocking get that returns the data got
        :return: data
        """
        data = self.__export.get()
        return data

class uvm_peek_port(uvm_port_base):
    """
    12.2.5.1
    """
    def peek(self):
        """
        12.2.4.2.3
        A blocking peek that returns data without
        consuming it.
        :return: data
        """
        data = self.__export.peek()
        return data

class uvm_nonblocking_put_port(uvm_port_base):
    """
    12.2.5.1
    Access the non_blocking put interface
    """
    def __init__(self, name, parent):
        super().__init__(name, parent)

    def try_put(self, data):
        """
        12.2.4.2.4
        Tries to put data on a port, but if the
        port is full it returns False
        :param data: data to deliver
        :return: True = success
        """
        success = self.__export.try_put(data)
        return success

    def can_put(self):
        """
        12.2.4.2.5
        Returns true if there is room for data to
        be put on the port
        :return: bool
        """
        can_do_it = self.__export.can_put()
        return can_do_it

class uvm_nonblocking_get_port(uvm_port_base):
    """
    12.2.5.1
    Access the non_blocking methods in export
    """

    def try_get(self):
        """
        12.2.4.2.6
        Returns a tuple containing success and the data
        This is different than SV UVM that returns the
        data through the argument list.
        :return: (success, data)
        """
        (success, data) = self.__export.try_get()
        return (success, data)

    def can_get(self):
        """
        12.2.4.2.7
        Returns true if there is data to get
        :return: bool
        """
        can = self.__export.can_get()
        return can

class get_peek_port(uvm_port_base):
    """
    12.2.5.1
    Try a peek
    """
    def try_peek(self):
        """
        12.2.4.2.8
        Tries to peek for data and returns
        a tuple with success and the data
        :return: (success, data)
        """
        success, data = self.__export.try_peek()
        return success, data

    def can_peek(self):
        """
        12.2.4.2.9
        Checks if peeking will be successful
        :return: bool
        """
        can = self.__export.can_peek()
        return can

class uvm_put_port(uvm_port_base, uvm_blocking_put_port, uvm_blocking_get_port):...
"""
12.2.5.1  
The get port delivers blocking and non_blocking functionality
"""
class uvm_get_port(uvm_port_base, uvm_blocking_get_port, uvm_nonblocking_get_port):...
"""
12.2.5.1
The put port delivers blocking puts and gets.  Here is the multiple inheritance that
SV lacked
"""

class uvm_analyis_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent)

    def write(self, data):
        """
        12.2.8.1
        :param data: data to send
        :return: None
        """
        self.__export.write(data)




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


class QueueAccessor():
    def __init__(self, queue, ap=None):
        assert(isinstance(queue, Queue)), "Tried to pass a non-Queue to export construtor"
        self.queue = queue
        self.ap = ap

class uvm_tlm_fifo_base(uvm_component):

    class BlockingPutExport(QueueAccessor):
        def put(self,item):
            self.queue.put(item)
            self.ap.write(item)

    class NonBlockingPutExport(QueueAccessor):
        '''
        12.2.8.1.3
        '''

        def can_put(self):
            return not self.queue.full()

        def try_put(self, item):
            try:
                self.queue.put_nowait ( item )
                self.ap.write(item)
                return True
            except QueueFull:
                return False

    class PutExport(BlockingPutExport, NonBlockingPutExport): ...

    class BlockingGetExport(QueueAccessor):
        def get(self):
            item = self.queue.get()
            self.ap.write(item)
            return item

    class NonBlockingGetExport(QueueAccessor):
        def can_get(self):
            return not self.queue.empty()

        def try_get(self):
            try:
                item = self.queue.get_nowait ()
                self.ap.write(item)
                return True, item
            except QueueEmpty:
                return False, None


    class GetExport(BlockingGetExport, NonBlockingGetExport):...

    class BlockingPeekExport(QueueAccessor):
        def peek(self):
            while self.queue.empty ():
                self.queue.not_empty.wait ()
            queue_data = self.queue.queue
            return queue_data[0]

    class NonBlockingPeekExport(QueueAccessor):
        def can_peek(self):
            return not self.queue.empty()

        def try_peek(self):
            if self.queue.empty():
                return False, None
            else:
                return True, self.queue.queue[0]

    class PeekExport(BlockingPeekExport, NonBlockingPeekExport): ...

    class BlockingGetPeekExport(BlockingGetExport, BlockingPeekExport):...

    class NonBlockingGetPeekExport(NonBlockingGetExport, NonBlockingPeekExport):...

    class GetPeekExport(GetExport, PeekExport):
        '''
        12.2.8.1.4
        '''

    def __init__(self, name, parent, maxsize):
        super().__init__(name,parent)
        self.__queue=Queue(maxsize=size)
        self.get_ap=uvm_analyis_port()
        self.put_ap=uvm_analyis_port()

        self.put_export=self.PutExport(self.__queue, )
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



class uvm_tlm_fifo(uvm_tlm_fifo_base):

    def __init__(self, name = None,parent = None, size=1):
        super().__init__(name, parent, size)


    def size(self):
        return self.__queue.maxsize

    def used(self):
        return self.__queue.qsize()

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

    class AnalysisExport(QueueAccessor):
        def write(self, item):
            try:
                self..put_nowait(item)
            except QueueFull:
                raise QueueFull(f"Full analysis fifo: {self.fullname}. This should never happen")

    def __init__(self):
        super().__init__(0)
        self.__queue = Queue()
        self.analysis_export = self.AnalysisExport(self.__queue)


class uvm_tlm_req_rsp_channel(uvm_component):
    '''
    12.2.9.1
    '''

    class MasterSlaveExport (QueueAccessor):
        def __init__(self, queue, put_export, get_peek_export):
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
