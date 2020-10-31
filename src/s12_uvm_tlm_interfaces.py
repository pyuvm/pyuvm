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
from error_classes import UVMTLMConnectionError
from enum import Enum
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

## We use these classes to check the connect phase
## to avoid illegal connections




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
        self.export = None

    def connect(self, export):
        """
        Attach this port to the associated export.
        :param export:
        :return:
        """
        try:
            self.export=export
            self.connected_to[export.get_full_name()]=export
            export.provided_to[self.get_full_name()]=self
        except:
            raise UVMTLMConnectionError(f"Error connecting {self.get_name()} using {export}")

    def check_export(self, export, check_class):
        if not isinstance(export, check_class):
            raise UVMTLMConnectionError(f"You tried to connect an {type(export)} to {self.get_full_name()}")

#put

class uvm_blocking_put_port(uvm_port_base):
    """
    12.2.5.1
    Access the blocking put interfaces
    """

    def connect(self, export):
        self.check_export(export, uvm_blocking_put_export)
        super().connect(export)

    def put(self, data):
        """
        12.2.4.2.1
        A blocking put that calls the export.put
        :param data:
        :return: None
        """
        try:
            self.export.put(data)
        except AttributeError:
            raise UVMTLMConnectionError(f"Missing or wrong export in {self.get_full_name()}. Did you connect it?")


class uvm_nonblocking_put_port(uvm_port_base):
    """
    12.2.5.1
    Access the non_blocking put interface
    """

    def connect(self, export):
        self.check_export(export, uvm_nonblocking_put_export)
        super().connect(export)

    def try_put(self, data):
        """
        12.2.4.2.4
        Tries to put data on a port, but if the
        port is full it returns False
        :param data: data to deliver
        :return: True = success
        """
        try:
            success = self.export.try_put(data)
            return success
        except AttributeError:
            raise UVMTLMConnectionError(f"Missing or wrong export in {self.get_full_name()}. Did you connect it?")

    def can_put(self):
        """
        12.2.4.2.5
        Returns true if there is room for data to
        be put on the port
        :return: bool
        """
        try:
            can_do_it = self.export.can_put()
            return can_do_it
        except AttributeError:
            raise UVMTLMConnectionError(f"Missing or wrong export in {self.get_full_name()}. Did you connect it?")

class uvm_put_port(uvm_blocking_put_port, uvm_nonblocking_put_port):...

#get
class uvm_blocking_get_port(uvm_port_base):
    """
    12.2.5.1
    Access the blocking get export methods
    """

    def connect(self, export):
        self.check_export(export, uvm_blocking_get_export)
        super().connect(export)

    def get(self):
        """
        12.2.4.2.2
        A blocking get that returns the data got
        :return: data
        """
        try:
            data = self.export.get()
            return data
        except AttributeError:
            raise UVMTLMConnectionError(f"Missing or wrong export in {self.get_full_name()}. Did you connect it?")

class uvm_nonblocking_get_port(uvm_port_base):
    """
    12.2.5.1
    Access the non_blocking methods in export
    """

    def connect(self, export):
        self.check_export(export, uvm_nonblocking_get_export)
        super().connect(export)

    def try_get(self):
        """
        12.2.4.2.6
        Returns a tuple containing success and the data
        This is different than SV UVM that returns the
        data through the argument list.
        :return: (success, data)
        """

        try:
            (success, data) = self.export.try_get()
        except AttributeError:
            raise UVMTLMConnectionError(f"Missing or wrong export in {self.get_full_name()}. Did you connect it?")

        return (success, data)
        

    def can_get(self):
        """
        12.2.4.2.7
        Returns true if there is data to get
        :return: bool
        """
        try:
            can = self.export.can_get()
        except AttributeError:
            raise UVMTLMConnectionError(f"Missing or wrong export in {self.get_full_name()}. Did you connect it?")

        return can

class uvm_get_port(uvm_blocking_get_port, uvm_nonblocking_get_port):...

#peek
class uvm_blocking_peek_port(uvm_port_base):
    """
    12.2.5.1
    """

    def connect(self, export):
        self.check_export(export, uvm_blocking_peek_export)
        super().connect(export)

    def peek(self):
        """
        12.2.4.2.3
        A blocking peek that returns data without
        consuming it.
        :return: data
        """
        try:
            data = self.export.peek()
            return data
        except AttributeError:
            raise UVMTLMConnectionError(f"Missing or wrong export in {self.get_full_name()}. Did you connect it?")

class uvm_nonblocking_peek_port(uvm_port_base):
    """
    12.2.5.1
    Try a peek
    """

    def connect(self, export):
        self.check_export(export, uvm_nonblocking_peek_export)
        super().connect(export)

    def try_peek(self):
        """
        12.2.4.2.8
        Tries to peek for data and returns
        a tuple with success and the data
        :return: (success, data)
        """
        try:
            success, data = self.export.try_peek()
        except AttributeError:
            raise UVMTLMConnectionError(f"Missing or wrong export in {self.get_full_name()}. Did you connect it?")
        return success, data

    def can_peek(self):
        """
        12.2.4.2.9
        Checks if peeking will be successful
        :return: bool
        """
        can = self.export.can_peek()
        return can

class uvm_peek_port(uvm_blocking_peek_port, uvm_nonblocking_peek_port):...

#getpeek

class uvm_blocking_get_peek_port(uvm_blocking_get_port, uvm_blocking_peek_port):
    def connect(self, export):
        if not (isinstance(export, uvm_blocking_get_export) or isinstance(export, uvm_blocking_peek_export)):
            raise UVMTLMConnectionError(
                f"Tried to connect {type(export)} to uvm_blocking_get_peek {self.get_full_name()}")
        super().connect(export)

class uvm_nonblocking_get_peek_port(uvm_blocking_get_port, uvm_blocking_peek_port):
    def connect(self, export):
        if not (isinstance(export, uvm_nonblocking_get_export) or isinstance(export, uvm_nonblocking_peek_export)):
            raise UVMTLMConnectionError(
                f"Tried to connect an {export} to uvm_blocking_get_peek {self.get_full_name()}")
        super().connect(export)

class uvm_get_peek_port(uvm_blocking_peek_port, uvm_nonblocking_peek_port):
    def connect(self, export):
        if not (isinstance(export, uvm_nonblocking_get_export) or isinstance(export, uvm_nonblocking_peek_export) \
                or isinstance(export, uvm_blocking_get_export) or isinstance(export, uvm_blocking_peek_export)):
            raise UVMTLMConnectionError(
                f"Tried to connect an illegal export to uvm_blocking_get_peek {self.get_full_name()}")

#transport
class uvm_blocking_transport_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent)

    def connect(self, export):
        self.check_export(export, uvm_blocking_transport_export)
        super().connect(export)

    def transport(self, put_data):
        try:
            get_data = self.export.transport(put_data)
        except AttributeError:
            raise UVMTLMConnectionError(f"Missing or wrong export in {self.get_full_name()}. Did you connect it?")
        return get_data

class uvm_nonblocking_transport_port(uvm_port_base):

    def __init__(self, name, parent):
        super().__init__(name, parent)

    def connect(self, export):
        self.check_export(export, uvm_nonblocking_transport_export)
        super().connect(export)

    def nb_transport(self, put_data):
        try:
            success, get_data = self.export.nb_transport(put_data)
        except AttributeError:
            raise UVMTLMConnectionError(f"Missing or wrong export in {self.get_full_name()}. Did you connect it?")
        return success, get_data

class uvm_transport_port(uvm_blocking_transport_port, uvm_nonblocking_transport_port):...

#master
class uvm_master_port(uvm_blocking_put_port, uvm_blocking_get_port):...

class uvm_slave_port(uvm_blocking_put_port, uvm_blocking_get_port):...


"""
12.2.5.1
The put port delivers blocking puts and gets.  Here is the multiple inheritance that
SV lacked
"""

class uvm_analyis_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent)

        self.subscribers = []

    def connect(self, export):
        self.subscribers.append(export)

    def write(self, data):
        """
        12.2.8.1
        :param data: data to send
        :return: None
        """
        try:
            for export in self.subscribers:
                export.write(data)

        except AttributeError:
            raise UVMTLMConnectionError(f"Missing or wrong export in {self.get_full_name()}. Did you connect it?")

class uvm_export_base(uvm_component):

    def __init__(self, name="", parent = None):
        super().__init__(name, parent)
        self.provided_to = {}

# put
class uvm_nonblocking_put_export(uvm_export_base): ...

class uvm_blocking_put_export(uvm_export_base): ...

class uvm_put_export(uvm_nonblocking_put_export, uvm_blocking_put_export): ...

# get
class uvm_nonblocking_get_export(uvm_export_base):...

class uvm_blocking_get_export(uvm_export_base):...

class uvm_get_export(uvm_nonblocking_get_export, uvm_blocking_get_export):...

#peek
class uvm_nonblocking_peek_export(uvm_export_base):...

class uvm_blocking_peek_export(uvm_export_base):...

class uvm_peek_export(uvm_nonblocking_peek_export, uvm_blocking_peek_export):...

#getpeek
class uvm_nonblocking_get_peek_export(uvm_export_base):...

class uvm_blocking_get_peek_export(uvm_export_base):...

class uvm_get_peek_export(uvm_nonblocking_get_peek_export, uvm_blocking_get_peek_export):...

#transport
class uvm_nonblocking_transport_export(uvm_export_base):...

class uvm_blocking_transport_export(uvm_export_base):...

class uvm_transport_export(uvm_nonblocking_transport_export, uvm_blocking_transport_export):...

#master
class uvm_blocking_master_export(uvm_blocking_put_export, uvm_blocking_get_peek_export):...

class uvm_nonblocking_master_export(uvm_blocking_peek_export, uvm_nonblocking_get_peek_export):...

class uvm_master_export(uvm_blocking_master_export, uvm_nonblocking_master_export):...

#slave
class uvm_blocking_slave_export(uvm_blocking_put_export, uvm_blocking_get_peek_export):...

class uvm_nonblocking_slave_export(uvm_nonblocking_put_export, uvm_nonblocking_get_peek_export):...

class uvm_slave_export(uvm_blocking_slave_export, uvm_nonblocking_slave_export):...

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
    def __init__(self, name, parent, queue, ap):
        super(QueueAccessor, self).__init__(name, parent)
        assert(isinstance(queue, Queue)), "Tried to pass a non-Queue to export construtor"
        self.queue = queue
        self.ap = ap

class uvm_tlm_fifo_base(uvm_component):
    """
    Declares and instantiate the exports needed to communicate
    through the Queue.
    """
    class BlockingPutExport(QueueAccessor, uvm_blocking_put_export):
        def put(self,item):
            self.queue.put(item)
            self.ap.write(item)

    class NonBlockingPutExport(QueueAccessor, uvm_nonblocking_put_export):
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

    class BlockingGetExport(QueueAccessor, uvm_blocking_get_export):
        def get(self):
            item = self.queue.get()
            self.ap.write(item)
            return item

    class NonBlockingGetExport(QueueAccessor, uvm_nonblocking_get_export):
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

    class BlockingPeekExport(QueueAccessor, uvm_blocking_peek_export):
        def peek(self):
            while self.queue.empty ():
                self.queue.not_empty.wait ()
            queue_data = self.queue.queue
            return queue_data[0]

    class NonBlockingPeekExport(QueueAccessor, uvm_nonblocking_peek_export):
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
        self.queue=Queue(maxsize=maxsize)
        self.get_ap=uvm_analyis_port("get_ap", self)
        self.put_ap=uvm_analyis_port("put_ap", self)

        self.blocking_put_export=self.BlockingPutExport("blocking_put_export",
                                                        self, self.queue, self.put_ap)
        self.nonblocking_put_export=self.NonBlockingPutExport("nonblocking_put_export",
                                                              self, self.queue, self.put_ap)
        self.put_export=self.PutExport("put_export", self, self.queue, self.put_ap)


        self.blocking_get_export = self.BlockingGetExport("blocking_get_export", self,
                                                          self.queue, self.get_ap)
        self.nonblocking_get_export = self.NonBlockingPutExport("nonblocking_get_export", self,
                                                                self.queue, self.put_ap)

        self.get_export = self.GetExport("get_export", self, self.queue, self.get_ap)


        self.blocking_peek_export = self.BlockingPeekExport("blocking_peek_export", self,
                                                            self.queue, self.get_ap)
        self.nonblocking_peek_export = self.NonBlockingPeekExport("nonblocking_peek_export", self,
                                                                  self.queue, self.get_ap)
        self.peek_export = self.PeekExport("peek_export", self,
                                           self.queue,self.get_ap)

        self.blocking_get_peek_export=self.BlockingGetPeekExport("blocking_get_peek_export", self,
                                                                 self.queue, self.get_ap)
        self.nonblocking_get_peek_export=self.NonBlockingGetPeekExport("nonblocking_get_peek_export", self,
                                                                       self.queue, self.get_ap)
        self.get_peek_export=self.GetPeekExport("get_peek_export", self, self.queue, self.get_ap)

class uvm_tlm_fifo(uvm_tlm_fifo_base):

    def __init__(self, name = None,parent = None, size=1):
        super().__init__(name, parent, size)


    def size(self):
        return self.queue.maxsize

    def used(self):
        return self.queue.qsize()

    def is_empty(self):
        return self.queue.empty()

    def is_full(self):
        return self.queue.full()

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
        self.queue.mutex.acquire()
        self.queue.queue.clear()
        self.queue.all_tasks_done.notify_all()
        self.queue.unfinished_tasks=0
        self.queue.mutex.release()

class uvm_tlm_analysis_fifo(uvm_tlm_fifo):

    class AnalysisExport(QueueAccessor):
        def write(self, item):
            try:
                self.queue.put(item, block=False)
            except QueueFull:
                raise QueueFull(f"Full analysis fifo: {self.fullname()}. This should never happen")

    def __init__(self, queue):
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
    class TransportExport(QueueAccessor):
        def __init__(self, queue):
            super().__init__(queue)
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
