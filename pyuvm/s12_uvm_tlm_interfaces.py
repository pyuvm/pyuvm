# The UVM TLM class hierarchy wraps the behavior of objects (usually Queues) in
# a set of classes and objects.
#
# The UVM LRM calls for three levels of classes to implement TLM: ports, exports,
# and imp:
# (from 12.2.1)
#
# * ports---Instantiated in components that require or use the associate interface
# to initiate transaction requests.
#
# * exports---Instantiated by components that forward an implementation of
# the methods defined in the associated interface.
#
# * imps---Instantiated by components that provide an implementation of or
# directly implement the methods defined.
#
# These three levels are unnecessary for Python because Python has
# multiple inheritances and duck typing.  You don't need to define
# different ports for each type being transferred.
#
# Ports have a data member named an export that implements the port
# functionality. uvm_put_port.put() calls its export.put(). Ports get
# their various flavors through multiple inheritance.


from pyuvm.s13_uvm_component import uvm_component
import queue
from pyuvm.error_classes import UVMTLMConnectionError
from pyuvm.utility_classes import UVMQueue
from pyuvm import error_classes


# 12.2.2
# This section describes a variety of classes without
# giving each one its own section using * to represent
# a variety of implementations (get, put, blocking_put, etc)

# Python provides multiple inheritance and we'll use that below
# to smooth implementation. Python does not require that we
# repeat the __init__ for classes that do not change the
# __init__ functionality.


# 12.2.5
# Port Classes
#
# The following port classes can be connected to "export" classes.
# They check that the export is of the correct type.
#
# uvm_port_base adds the correct methods to this class
# rather than reference them because Python allows
# you to assign functions to objects dynamically.

# We use these classes to check the connect phase
# to avoid illegal connections


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
        self.connected_to = {}
        self.provided_to = {}
        self.export = None

    def connect(self, export):
        """
        Attach this port to the associated export.
        :param export:
        :return:
        """
        try:
            self.export = export
            self.connected_to[export.get_full_name()] = export
            export.provided_to[self.get_full_name()] = self
        except KeyError:
            raise UVMTLMConnectionError(f"Error connecting {self.get_name()} using {export}")

    @staticmethod
    def check_export(export, check_class):
        if not isinstance(export, check_class):
            raise UVMTLMConnectionError(f"{export} must be an instance of\n{check_class} not\n{type(export)}")


# put

class uvm_blocking_put_port(uvm_port_base):
    """
    12.2.5.1
    Access the blocking put interfaces
    """

    def connect(self, export):
        self.check_export(export, uvm_blocking_put_port)
        super().connect(export)

    def put(self, data, timeout=None):
        """
        12.2.4.2.1
        A blocking put that calls the export.put
        :param timeout: Timeout
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
        self.check_export(export, uvm_nonblocking_put_port)
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


# 12.2.5.1
# The put port delivers blocking puts and gets.  Here is the multiple inheritance that
# SV lacked
class uvm_put_port(uvm_blocking_put_port, uvm_nonblocking_put_port):
    ...


# get
class uvm_blocking_get_port(uvm_port_base):
    """
    12.2.5.1
    Access the blocking get export methods
    """

    def connect(self, export):
        self.check_export(export, uvm_blocking_get_port)
        super().connect(export)

    def get(self, timeout=None):
        """
        12.2.4.2.2
        A blocking get that returns the data got
        :return: data
        """
        try:
            data = self.export.get(timeout=timeout)
            return data
        except AttributeError:
            raise UVMTLMConnectionError(f"Missing or wrong export in {self.get_full_name()}. Did you connect it?")
        except :
            raise


class uvm_nonblocking_get_port(uvm_port_base):
    """
    12.2.5.1
    Access the non_blocking methods in export
    """

    def connect(self, export):
        self.check_export(export, uvm_nonblocking_get_port)
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

        return success, data

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


class uvm_get_port(uvm_blocking_get_port, uvm_nonblocking_get_port):
    ...


# peek
class uvm_blocking_peek_port(uvm_port_base):
    """
    12.2.5.1
    """

    def connect(self, export):
        self.check_export(export, uvm_blocking_peek_port)
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
        self.check_export(export, uvm_nonblocking_peek_port)
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


class uvm_peek_port(uvm_blocking_peek_port, uvm_nonblocking_peek_port):
    ...


# get_peek

class uvm_blocking_get_peek_port(uvm_blocking_get_port, uvm_blocking_peek_port):
    def connect(self, export):
        if not (isinstance(export, uvm_blocking_get_port) or isinstance(export, uvm_blocking_peek_port)):
            raise UVMTLMConnectionError(
                f"Tried to connect {type(export)} to uvm_blocking_get_peek {self.get_full_name()}")
        super().connect(export)


class uvm_nonblocking_get_peek_port(uvm_nonblocking_get_port, uvm_nonblocking_peek_port):
    def connect(self, export):
        if not (isinstance(export, uvm_nonblocking_get_port) or isinstance(export, uvm_nonblocking_peek_port)):
            raise UVMTLMConnectionError(
                f"Tried to connect an {export} to uvm_blocking_get_peek {self.get_full_name()}")
        super().connect(export)


class uvm_get_peek_port(uvm_blocking_get_peek_port, uvm_nonblocking_get_peek_port):
    def connect(self, export):
        if not (isinstance(export, uvm_nonblocking_get_port) or isinstance(export, uvm_nonblocking_peek_port)
                or isinstance(export, uvm_blocking_get_port) or isinstance(export, uvm_blocking_peek_port)):
            raise UVMTLMConnectionError(
                f"Tried to connect an illegal export to uvm_blocking_get_peek {self.get_full_name()}")
        super().connect(export)


# transport
class uvm_blocking_transport_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent)

    def connect(self, export):
        self.check_export(export, uvm_blocking_transport_port)
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
        self.check_export(export, uvm_nonblocking_transport_port)
        super().connect(export)

    def nb_transport(self, put_data):
        try:
            success, get_data = self.export.nb_transport(put_data)
        except AttributeError:
            raise UVMTLMConnectionError(f"Missing or wrong export in {self.get_full_name()}. Did you connect it?")
        return success, get_data


class uvm_transport_port(uvm_blocking_transport_port, uvm_nonblocking_transport_port):
    ...


# master
class uvm_blocking_master_port(uvm_blocking_put_port, uvm_blocking_get_peek_port):
    ...


class uvm_nonblocking_master_port(uvm_nonblocking_put_port, uvm_nonblocking_get_peek_port):
    ...


class uvm_master_port(uvm_blocking_master_port, uvm_nonblocking_master_port):
    ...


class uvm_blocking_slave_port(uvm_blocking_put_port, uvm_blocking_get_peek_port):
    ...


class uvm_nonblocking_slave_port(uvm_nonblocking_get_peek_port, uvm_nonblocking_put_port):
    ...


class uvm_slave_port(uvm_nonblocking_slave_port, uvm_blocking_slave_port):
    ...


class uvm_analysis_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent)

        self.subscribers = []

    def connect(self, export):
        self.check_export(export, uvm_analysis_port)
        self.subscribers.append(export)

    def write(self, data):
        """
        12.2.8.1
        :param data: data to send
        :return: None
        """
        for export in self.subscribers:
            if not hasattr(export, "write"):
                raise UVMTLMConnectionError(f"No write() method in {export}. Did you connect it?")
            export.write(data)



# THE UNNECESSARY EXPORTS
# It turns out the entire export class is unnecessary in Python
# Since the port's connect() method can connect to either a port
# or export (they both provided the needed methods) it means
# that an export is simply a port with the methods filled in.
#
# One could have made ports abstract base classes, but that
# would add complications to the metatypes that implement
# the factory, so we don't do that.

# We provide the export class below to follow the spec
# and to acknowledge that the name "export" does imply
# a port with implemented functions.

class uvm_nonblocking_put_export(uvm_nonblocking_put_port):
    ...


class uvm_blocking_put_export(uvm_blocking_put_port):
    ...


class uvm_put_export(uvm_nonblocking_put_export, uvm_blocking_put_export):
    ...


# get
class uvm_nonblocking_get_export(uvm_nonblocking_get_port):
    ...


class uvm_blocking_get_export(uvm_blocking_get_port):
    ...


class uvm_get_export(uvm_blocking_get_export, uvm_nonblocking_get_export):
    ...


# peek
class uvm_nonblocking_peek_export(uvm_nonblocking_peek_port):
    ...


class uvm_blocking_peek_export(uvm_blocking_peek_port):
    ...


class uvm_peek_export(uvm_nonblocking_peek_export, uvm_blocking_peek_export):
    ...


# get_peek
class uvm_blocking_get_peek_export(uvm_blocking_get_peek_port):
    ...


class uvm_nonblocking_get_peek_export(uvm_nonblocking_get_peek_port):
    ...


class uvm_get_peek_export(uvm_nonblocking_get_peek_export, uvm_blocking_get_peek_export):
    ...


# transport
class uvm_blocking_transport_export(uvm_blocking_transport_port):
    ...


class uvm_nonblocking_transport_export(uvm_nonblocking_transport_port):
    ...


class uvm_transport_export(uvm_nonblocking_transport_export, uvm_blocking_transport_export):
    ...


# master
class uvm_blocking_master_export(uvm_blocking_put_export, uvm_blocking_get_peek_export):
    ...


class uvm_nonblocking_master_export(uvm_blocking_peek_export, uvm_nonblocking_get_peek_export):
    ...


class uvm_master_export(uvm_blocking_master_export, uvm_nonblocking_master_export):
    ...


# slave
class uvm_blocking_slave_export(uvm_blocking_put_export, uvm_blocking_get_peek_export):
    ...


class uvm_nonblocking_slave_export(uvm_nonblocking_put_export, uvm_nonblocking_get_peek_export):
    ...


class uvm_slave_export(uvm_blocking_slave_export, uvm_nonblocking_slave_export):
    ...


class uvm_analysis_export(uvm_analysis_port):
    """
    The analysis export overrides the port's write method and forces otherse
    to override its write method.
    """
    def write(self, data):
        raise error_classes.UVMTLMConnectionError("If you extend uvm_analysis_export, or uvm_subscriber, you must"
                                                  " override the write method")

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


class QueueAccessor:
    def __init__(self, name, parent, queue, ap):
        super(QueueAccessor, self).__init__(name, parent)
        assert (isinstance(queue, UVMQueue)), "Tried to pass a non-UVMQueue to QueueAccessor constructor"
        self.queue = queue
        self.ap = ap


class uvm_tlm_fifo_base(uvm_component):
    """
    Declares and instantiate the exports needed to communicate
    through the Queue.
    """

    class BlockingPutExport(QueueAccessor, uvm_blocking_put_export):
        def put(self, item, timeout=None):
            self.queue.put(item, timeout=timeout)
            self.ap.write(item)

    #  12.2.8.1.3
    class NonBlockingPutExport(QueueAccessor, uvm_nonblocking_put_export):

        def can_put(self):
            return not self.queue.full()

        def try_put(self, item):
            try:
                self.queue.put_nowait(item)
                self.ap.write(item)
                return True
            except queue.Full:
                return False

    class PutExport(BlockingPutExport, NonBlockingPutExport):
        ...

    class BlockingGetExport(QueueAccessor, uvm_blocking_get_export):
        def get(self, timeout=None):
            item = self.queue.get(timeout=timeout)
            self.ap.write(item)
            return item

    class NonBlockingGetExport(QueueAccessor, uvm_nonblocking_get_export):
        def can_get(self):
            return not self.queue.empty()

        def try_get(self):
            try:
                item = self.queue.get_nowait()
                self.ap.write(item)
                return True, item
            except queue.Empty:
                return False, None

    class GetExport(BlockingGetExport, NonBlockingGetExport):
        ...

    class BlockingPeekExport(QueueAccessor, uvm_blocking_peek_export):
        def peek(self):
            peek_data = self.queue.peek()
            return peek_data

    class NonBlockingPeekExport(QueueAccessor, uvm_nonblocking_peek_export):
        def can_peek(self):
            return not self.queue.empty()

        def try_peek(self):
            if self.queue.empty():
                return False, None
            else:
                return True, self.queue.peek()

    class PeekExport(BlockingPeekExport, NonBlockingPeekExport):
        ...

    class BlockingGetPeekExport(BlockingGetExport, BlockingPeekExport):
        ...

    class NonBlockingGetPeekExport(NonBlockingGetExport, NonBlockingPeekExport):
        ...

    #  12.2.8.1.4
    class GetPeekExport(GetExport, PeekExport):
        ...

    def __init__(self, name, parent, maxsize=1):
        super().__init__(name, parent)
        self.queue = UVMQueue(maxsize=maxsize)
        self.get_ap = uvm_analysis_port("get_ap", self)
        self.put_ap = uvm_analysis_port("put_ap", self)

        self.blocking_put_export = self.BlockingPutExport("blocking_put_export",
                                                          self, self.queue, self.put_ap)
        self.nonblocking_put_export = self.NonBlockingPutExport("nonblocking_put_export",
                                                                self, self.queue, self.put_ap)
        self.put_export = self.PutExport("put_export", self, self.queue, self.put_ap)

        self.blocking_get_export = self.BlockingGetExport("blocking_get_export", self,
                                                          self.queue, self.get_ap)
        self.nonblocking_get_export = self.NonBlockingGetExport("nonblocking_get_export", self,
                                                                self.queue, self.put_ap)

        self.get_export = self.GetExport("get_export", self, self.queue, self.get_ap)

        self.blocking_peek_export = self.BlockingPeekExport("blocking_peek_export", self,
                                                            self.queue, self.get_ap)
        self.nonblocking_peek_export = self.NonBlockingPeekExport("nonblocking_peek_export", self,
                                                                  self.queue, self.get_ap)
        self.peek_export = self.PeekExport("peek_export", self,
                                           self.queue, self.get_ap)

        self.blocking_get_peek_export = self.BlockingGetPeekExport("blocking_get_peek_export", self,
                                                                   self.queue, self.get_ap)
        self.nonblocking_get_peek_export = self.NonBlockingGetPeekExport("nonblocking_get_peek_export", self,
                                                                         self.queue, self.get_ap)
        self.get_peek_export = self.GetPeekExport("get_peek_export", self, self.queue, self.get_ap)


class uvm_tlm_fifo(uvm_tlm_fifo_base):

    def __init__(self, name=None, parent=None, size=1):
        """
        12.2.8.2.1
        :param name:
        :param parent:
        :param size:
        """
        super().__init__(name, parent, size)

    def size(self):
        """
        12.2.8.2.2
        :return:
        """
        return self.queue.maxsize

    def used(self):
        """
        12.2.8.2.3
        :return:
        """
        return self.queue.qsize()

    def is_empty(self):
        """
        12.2.8.2.4
        :return:
        """
        return self.queue.empty()

    def is_full(self):
        """
        12.2.8.2.5
        :return:
        """
        return self.queue.full()

    #  12.2.8.2.6
    def flush(self):
        """
        The SystemVerilog UVM flushes the Queue
        using a while loop and counting the number
        of threads waiting for a get. If there are
        still threads waiting after the loop runs
        it issues an error.

        In pyuvm we just flush the loop and clear
        all the unfinished tasks.
        """
        self.queue.mutex.acquire()
        self.queue.queue.clear()
        self.queue.all_tasks_done.notify_all()
        self.queue.unfinished_tasks = 0
        self.queue.mutex.release()


class uvm_tlm_analysis_fifo(uvm_tlm_fifo):
    class AnalysisExport(QueueAccessor, uvm_analysis_port):
        def write(self, item):
            try:
                self.queue.put(item, block=False)
            except queue.Full:
                raise queue.Full(f"Full analysis fifo: {self.__name__}. This should never happen")

    def __init__(self, name, parent=None):
        super().__init__(name, parent, 0)
        self.analysis_export = self.AnalysisExport(name="analysis_export", parent=self,
                                                   queue=self.queue, ap=None)


#    12.2.9.1
class uvm_tlm_req_rsp_channel(uvm_component):
    class MasterSlaveExport(uvm_master_port, uvm_get_peek_port):
        def __init__(self, name, parent, put_export, get_peek_export):
            super().__init__(name, parent)
            self.put_export = put_export
            self.get_peek_export = get_peek_export

        def put(self, item, timeout=None):
            self.put_export.put(item)

        def can_put(self):
            return self.put_export.can_put()

        def try_put(self, item):
            return self.put_export.try_put(item)

        def get(self, timeout=None):
            return self.get_peek_export.get(timeout=timeout)

        def can_get(self):
            return self.get_peek_export.can_get()

        def try_get(self):
            return self.get_peek_export.try_get

    def __init__(self, name, parent=None, request_fifo_size=1, response_fifo_size=1):
        super().__init__(name, parent)
        self.req_tlm_fifo = uvm_tlm_fifo("request_fifo", self, request_fifo_size)
        self.rsp_tlm_fifo = uvm_tlm_fifo("response_fifo", self, response_fifo_size)

        self.put_request_export = self.req_tlm_fifo.put_export  # 12.2.9.1.3
        self.get_peek_response_export = self.rsp_tlm_fifo.get_peek_export  # 12.2.9.1.4
        self.get_peek_request_export = self.req_tlm_fifo.get_peek_export  # 12.2.9.1.5
        self.put_response_export = self.rsp_tlm_fifo.put_export  # 12.2.9.1.6
        self.request_ap = uvm_analysis_port("request_ap", self)  # 12.2.9.1.7
        self.response_ap = uvm_analysis_port("response_ap", self)  # 12.2.9.1.8

        self.master_export = self.MasterSlaveExport(name="master_export", parent=self,
                                                    put_export=self.put_request_export,
                                                    get_peek_export=self.get_peek_response_export)  # 12.2.9.1.9
        self.slave_export = self.MasterSlaveExport(name="slave_export",
                                                   parent=self,
                                                   get_peek_export=self.get_peek_request_export,
                                                   put_export=self.put_response_export)  # 12.2.9.1.10

    def connect_phase(self):
        self.request_ap.connect(self.req_tlm_fifo.put_ap)  # 12.2.9.1.7
        self.response_ap.connect(self.rsp_tlm_fifo.get_ap)  # 12.2.9.1.8


class uvm_tlm_transport_channel(uvm_tlm_req_rsp_channel):
    class TransportExport(uvm_transport_port):
        def __init__(self, name, parent, req_fifo, rsp_fifo):
            super().__init__(name, parent)
            self.req_fifo = req_fifo
            self.rsp_fifo = rsp_fifo

        def transport(self, req, timeout=None):
            self.req_fifo.put_export.put(req)
            return self.rsp_fifo.get_peek_export.get(timeout=timeout)

        def nb_transport(self, req):
            if not self.req_fifo.put_export.try_put(req):
                return False
            return self.rsp_fifo.get_peek_export.try_get()

    def __init__(self, name, parent=None):
        super().__init__(name, parent, 1, 1)
        self.transport_export = self.TransportExport("transport_export", self,
                                                     req_fifo=self.req_tlm_fifo,
                                                     rsp_fifo=self.rsp_tlm_fifo)

# UVM TLM 2
# 12.3

# This is left for future development.
