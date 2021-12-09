# The UVM TLM class hierarchy wraps the behavior of objects (usually Queues) in
# a set of classes and objects.
#
# The UVM LRM calls for three levels of classes to
# implement TLM: ports, exports, and imp:
# (from 12.2.1)
#
# * ports---Instantiated in components that require or use the associated
# interface to initiate transaction requests.
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
from pyuvm.error_classes import UVMTLMConnectionError
from pyuvm.utility_classes import UVMQueue, FIFO_DEBUG
from cocotb.queue import QueueEmpty, QueueFull


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

# uvm_export_base provides the provided_to
# associative array.
class uvm_export_base(uvm_component):
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.provided_to = {}


class uvm_port_base(uvm_export_base):
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
    # This is the list of all TLM functions. Each port class
    # uses this to create a list of methods that an export
    # must support.
    __tlm_method_list = ["put", "get", "peek",
                         "try_put", "try_get", "try_peek",
                         "can_put", "can_get", "can_peek",
                         "transport", "nb_transport",
                         "write",
                         "put_req", "put_response", "get_next_item",
                         "item_done", "get_response"]

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.connected_to = {}
        self.export = None
        self.needed_methods = []

        # Compare the list of all tlm methods to the
        # methods in this class to create a list of
        # needed
        for method in self.__tlm_method_list:
            if hasattr(self, method):
                self.needed_methods.append(method)

    def check_export(self, export):
        """Check that the export implements needed methods"""
        if not isinstance(export, uvm_export_base):
            raise UVMTLMConnectionError(
                f"{export} must be a subclass of uvm_export_base")
        for needed in self.needed_methods:
            if not hasattr(export, needed):
                raise UVMTLMConnectionError(
                    f"{export} must implement '{needed}()'"
                    f" to connect to a {self.__class__}")

    def connect(self, export):
        """
        Attach this port to the associated export.

        :param export:
        :return:
        """
        self.check_export(export)
        try:
            self.export = export
            self.connected_to[export.get_full_name()] = export
            export.provided_to[self.get_full_name()] = self
        except KeyError:
            raise UVMTLMConnectionError(
                f"Error connecting {self.get_name()} using {export}")

# put

# 12.2.5.1


class uvm_blocking_put_port(uvm_port_base):
    """
    Access the blocking put interfaces
    """

    # 12.2.4.2.1
    async def put(self, datum):
        """
         A blocking put that calls the export.put
        :param datum: Datum to put
        :return: None
        """
        try:
            await self.export.put(datum)
        except AttributeError:
            raise UVMTLMConnectionError(
                "Missing or wrong export in"
                f" {self.get_full_name()}. Did you connect it?")


# 12.2.5.1
class uvm_nonblocking_put_port(uvm_port_base):
    """
    Access the non_blocking put interface
    """

    # 12.2.4.2.4
    def try_put(self, data):
        """
        Tries to put data on a port, but if the
        port is full it returns False

        :param data: data to deliver
        :return: True = success
        """
        try:
            success = self.export.try_put(data)
            return success
        except AttributeError:
            raise UVMTLMConnectionError(
                "Missing or wrong export "
                f"in {self.get_full_name()}. Did you connect it?")

    # 12.2.4.2.5
    def can_put(self):
        """
        Returns true if there is room for data to
        be put on the port

        :return: bool
        """
        try:
            can_do_it = self.export.can_put()
            return can_do_it
        except AttributeError:
            raise UVMTLMConnectionError(
                "Missing or wrong export in"
                f" {self.get_full_name()}. Did you connect it?")


# 12.2.5.1
# The put port delivers blocking puts and gets.
# Here is the multiple inheritance that SV lacked
class uvm_put_port(uvm_blocking_put_port, uvm_nonblocking_put_port):
    ...


# 12.2.5.1
class uvm_blocking_get_port(uvm_port_base):
    """
        Access the blocking get export methods
    """

    # 12.2.4.2.2
    async def get(self):
        """

        A blocking get that returns the data got
        :return: data
        """
        try:
            data = await self.export.get()
            return data
        except AttributeError:
            raise UVMTLMConnectionError(
                "Missing or wrong export in "
                f"{self.get_full_name()}. Did you connect it?")


# 12.2.5.1
class uvm_nonblocking_get_port(uvm_port_base):
    """
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

        try:
            (success, data) = self.export.try_get()
        except AttributeError:
            raise UVMTLMConnectionError(
                "Missing or wrong export in"
                f" {self.get_full_name()}. Did you connect it?")

        return success, data

    # 12.2.4.2.7
    def can_get(self):
        """
        Returns true if there is data to get

        :return: bool
        """
        try:
            can = self.export.can_get()
        except AttributeError:
            raise UVMTLMConnectionError(
                "Missing or wrong export in"
                f" {self.get_full_name()}. Did you connect it?")

        return can


class uvm_get_port(uvm_blocking_get_port, uvm_nonblocking_get_port):
    ...


#
# 12.2.5.1
class uvm_blocking_peek_port(uvm_port_base):
    """
    Provides access to the peek methods
    """

    # 12.2.4.2.3
    async def peek(self):
        """
        A blocking peek that returns data without
        consuming it.

        :return: datum
        """
        try:
            datum = await self.export.peek()
            return datum
        except AttributeError:
            raise UVMTLMConnectionError(
                "Missing or wrong export in"
                f" {self.get_full_name()}. Did you connect it?")


# 12.2.5.1
class uvm_nonblocking_peek_port(uvm_port_base):
    """
    Try a peek
    """

    # 12.2.4.2.8
    def try_peek(self):
        """

        Tries to peek for data and returns
        a tuple with success and the data
        :return: (success, data)
        """
        try:
            success, data = self.export.try_peek()
        except AttributeError:
            raise UVMTLMConnectionError(
                "Missing or wrong export in"
                f" {self.get_full_name()}. Did you connect it?")
        return success, data

    # 12.2.4.2.9
    def can_peek(self):
        """
        Checks if peeking will be successful

        :return: True if can peek
        """
        can = self.export.can_peek()
        return can


class uvm_peek_port(uvm_blocking_peek_port, uvm_nonblocking_peek_port):
    ...


# get_peek

class uvm_blocking_get_peek_port(uvm_blocking_get_port,
                                 uvm_blocking_peek_port):
    ...


class uvm_nonblocking_get_peek_port(uvm_nonblocking_get_port,
                                    uvm_nonblocking_peek_port):
    ...


class uvm_get_peek_port(uvm_blocking_get_peek_port,
                        uvm_nonblocking_get_peek_port):
    ...


class uvm_blocking_transport_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent)

    async def transport(self, put_data):
        try:
            get_data = await self.export.transport(put_data)
        except AttributeError:
            raise UVMTLMConnectionError(
                "Missing or wrong export in"
                f" {self.get_full_name()}. Did you connect it?")
        return get_data


class uvm_nonblocking_transport_port(uvm_port_base):

    def __init__(self, name, parent):
        super().__init__(name, parent)

    def nb_transport(self, put_data):
        try:
            success, get_data = self.export.nb_transport(put_data)
        except AttributeError:
            raise UVMTLMConnectionError(
                "Missing or wrong export in"
                f" {self.get_full_name()}. Did you connect it?")
        return success, get_data


class uvm_transport_port(uvm_blocking_transport_port,
                         uvm_nonblocking_transport_port):
    ...


# master
class uvm_blocking_master_port(uvm_blocking_put_port,
                               uvm_blocking_get_peek_port):
    ...


class uvm_nonblocking_master_port(uvm_nonblocking_put_port,
                                  uvm_nonblocking_get_peek_port):
    ...


class uvm_master_port(uvm_blocking_master_port, uvm_nonblocking_master_port):
    ...


class uvm_blocking_slave_port(uvm_blocking_put_port,
                              uvm_blocking_get_peek_port):
    ...


class uvm_nonblocking_slave_port(uvm_nonblocking_get_peek_port,
                                 uvm_nonblocking_put_port):
    ...


class uvm_slave_port(uvm_nonblocking_slave_port,
                     uvm_blocking_slave_port):
    ...


class uvm_analysis_port(uvm_port_base):
    def __init__(self, name, parent):
        super().__init__(name, parent)

        self.subscribers = []

    # 12.2.8.1
    def write(self, datum):
        """
        :param datum: data to send
        :return: None
        """
        for export in self.subscribers:
            if not hasattr(export, "write"):
                raise UVMTLMConnectionError(
                    f"No write() method in {export}. Did you connect it?")
            export.write(datum)

    def connect(self, export):
        self.check_export(export)
        self.subscribers.append(export)


class uvm_nonblocking_put_export(uvm_export_base):
    ...


class uvm_blocking_put_export(uvm_export_base):
    ...


class uvm_put_export(uvm_nonblocking_put_export, uvm_blocking_put_export):
    ...


# get
class uvm_nonblocking_get_export(uvm_export_base):
    ...


class uvm_blocking_get_export(uvm_export_base):
    ...


class uvm_get_export(uvm_blocking_get_export, uvm_nonblocking_get_export):
    ...


# peek
class uvm_nonblocking_peek_export(uvm_export_base):
    ...


class uvm_blocking_peek_export(uvm_export_base):
    ...


class uvm_peek_export(uvm_nonblocking_peek_export, uvm_blocking_peek_export):
    ...


# get_peek
class uvm_blocking_get_peek_export(uvm_export_base):
    ...


class uvm_nonblocking_get_peek_export(uvm_export_base):
    ...


class uvm_get_peek_export(uvm_nonblocking_get_peek_export,
                          uvm_blocking_get_peek_export):
    ...


# transport
class uvm_blocking_transport_export(uvm_export_base):
    ...


class uvm_nonblocking_transport_export(uvm_export_base):
    ...


class uvm_transport_export(uvm_nonblocking_transport_export,
                           uvm_blocking_transport_export):
    ...


# master
class uvm_blocking_master_export(uvm_blocking_put_export,
                                 uvm_blocking_get_peek_export):
    ...


class uvm_nonblocking_master_export(uvm_blocking_peek_export,
                                    uvm_nonblocking_get_peek_export):
    ...


class uvm_master_export(uvm_blocking_master_export,
                        uvm_nonblocking_master_export):
    ...


# slave
class uvm_blocking_slave_export(uvm_blocking_put_export,
                                uvm_blocking_get_peek_export):
    ...


class uvm_nonblocking_slave_export(uvm_nonblocking_put_export,
                                   uvm_nonblocking_get_peek_export):
    ...


class uvm_slave_export(uvm_blocking_slave_export,
                       uvm_nonblocking_slave_export):
    ...


class uvm_analysis_export(uvm_export_base):
    ...


# 12.2.8 FIFO Classes
#
# These classes provide synchronization control between
# threads using the Queue class.
#
# One note.  The RLM has only 12.2.8.1.3 and 12.2.8.1.4, put_export
# and get_peek_export, but the UVM code has all the variants
# of exports.
#
# The SystemVerilog UVM relies upon static type checking
# and polymorphism to make sure that users connect the
# correct ports to these exports, but we don't have
# static checking, so we implement classes for all the
# port variants. This creates the runtime assertion checking
# that we need.


class uvm_QueueAccessor:
    def __init__(self, name, parent, uvm_queue, ap):
        super(uvm_QueueAccessor, self).__init__(name, parent)
        assert (isinstance(uvm_queue, UVMQueue)), \
            "Tried to pass a non-UVMQueue to QueueAccessor constructor"
        self.queue = uvm_queue
        self.ap = ap


class uvm_tlm_fifo_base(uvm_component):
    """
    Declares and instantiate the exports needed to communicate
    through the Queue.
    """

    class uvm_BlockingPutExport(uvm_QueueAccessor, uvm_blocking_put_export):
        async def put(self, item):
            self.logger.log(FIFO_DEBUG, f"blocking put: {item}")
            await self.queue.put(item)
            self.logger.log(FIFO_DEBUG, f"success put {item}")
            self.ap.write(item)

    #  12.2.8.1.3
    class uvm_NonBlockingPutExport(uvm_QueueAccessor,
                                   uvm_nonblocking_put_export):

        def can_put(self):
            return not self.queue.full()

        def try_put(self, item):
            try:
                self.queue.put_nowait(item)
                self.ap.write(item)
                return True
            except QueueFull:
                return False

    class uvm_PutExport(uvm_BlockingPutExport, uvm_NonBlockingPutExport):
        ...

    class uvm_BlockingGetExport(uvm_QueueAccessor, uvm_blocking_get_export):
        async def get(self):
            self.logger.log(FIFO_DEBUG, "Attempting blocking get")
            item = await self.queue.get()
            self.logger.log(FIFO_DEBUG, f"got {item}")
            self.ap.write(item)
            return item

    class uvm_NonBlockingGetExport(uvm_QueueAccessor,
                                   uvm_nonblocking_get_export):
        def can_get(self):
            get_ok = not self.queue.empty()
            return get_ok

        def try_get(self):
            try:
                item = self.queue.get_nowait()
                self.ap.write(item)
                return True, item
            except QueueEmpty:
                return False, None

    class uvm_GetExport(uvm_BlockingGetExport, uvm_NonBlockingGetExport):
        ...

    class uvm_BlockingPeekExport(uvm_QueueAccessor, uvm_blocking_peek_export):
        async def peek(self):
            self.logger.log(FIFO_DEBUG, "Attempting blocking peek")
            peek_data = await self.queue.peek()
            self.logger.log(FIFO_DEBUG, f"peeked at {peek_data}")
            return peek_data

    class uvm_NonBlockingPeekExport(uvm_QueueAccessor,
                                    uvm_nonblocking_peek_export):
        def can_peek(self):
            return not self.queue.empty()

        def try_peek(self):
            try:
                datum = self.queue.peek_nowait()
                return True, datum
            except QueueEmpty:
                return False, None

    class uvm_PeekExport(uvm_BlockingPeekExport, uvm_NonBlockingPeekExport):
        ...

    class uvm_BlockingGetPeekExport(uvm_BlockingGetExport,
                                    uvm_BlockingPeekExport):
        ...

    class uvm_NonBlockingGetPeekExport(uvm_NonBlockingGetExport,
                                       uvm_NonBlockingPeekExport):
        ...

    #  12.2.8.1.4
    class uvm_GetPeekExport(uvm_GetExport, uvm_PeekExport):
        ...

    def __init__(self, name, parent, maxsize=1):
        super().__init__(name, parent)
        self.queue = UVMQueue(maxsize=maxsize)
        self.get_ap = uvm_analysis_port("get_ap", self)
        self.put_ap = uvm_analysis_port("put_ap", self)

        self.blocking_put_export = self.uvm_BlockingPutExport("blocking_put_export",  # noqa: E501
                                                              self, self.queue,
                                                              self.put_ap)
        self.nonblocking_put_export = self.uvm_NonBlockingPutExport("nonblocking_put_export",  # noqa: E501
                                                                    self, self.queue, self.put_ap)  # noqa: E501
        self.put_export = self.uvm_PutExport("put_export", self, self.queue, self.put_ap)  # noqa: E501

        self.blocking_get_export = self.uvm_BlockingGetExport("blocking_get_export", self,  # noqa: E501
                                                              self.queue, self.get_ap)  # noqa: E501
        self.nonblocking_get_export = self.uvm_NonBlockingGetExport("nonblocking_get_export", self,  # noqa: E501
                                                                    self.queue, self.put_ap)  # noqa: E501

        self.get_export = self.uvm_GetExport("get_export", self, self.queue,
                                             self.get_ap)

        self.blocking_peek_export = self.uvm_BlockingPeekExport("blocking_peek_export", self,  # noqa: E501
                                                                self.queue, self.get_ap)  # noqa: E501
        self.nonblocking_peek_export = self.uvm_NonBlockingPeekExport("nonblocking_peek_export", self,  # noqa: E501
                                                                      self.queue, self.get_ap)  # noqa: E501
        self.peek_export = self.uvm_PeekExport("peek_export", self,
                                               self.queue, self.get_ap)

        self.blocking_get_peek_export = self.uvm_BlockingGetPeekExport("blocking_get_peek_export", self,  # noqa: E501
                                                                       self.queue, self.get_ap)  # noqa: E501
        self.nonblocking_get_peek_export = self.uvm_NonBlockingGetPeekExport("nonblocking_get_peek_export", self,  # noqa: E501
                                                                             self.queue, self.get_ap)  # noqa: E501
        self.get_peek_export = self.uvm_GetPeekExport("get_peek_export", self, self.queue, self.get_ap)  # noqa: E501


class uvm_tlm_fifo(uvm_tlm_fifo_base):

    #  12.2.8.2.1
    def __init__(self, name=None, parent=None, size=1):
        """ uvm_tlm_fifo is a uvm_component"""
        super().__init__(name, parent, size)

    # 12.2.8.2.2
    def size(self):
        """
        Return the size of the fifo

        :return: size of FIFO
        """
        return self.queue.maxsize

    # 12.2.8.2.3
    def used(self):
        """
        How much of the FIFO is being used?

        :return: Size of the FIFO
        """
        return self.queue.qsize()

    # 12.2.8.2.4
    def is_empty(self):
        """
        Returns true if FIFO is empty

        :return: True if empty
        """
        return self.queue.empty()

    # 12.2.8.2.5
    def is_full(self):
        """
        Test for full FIFO

        :return: True if full
        """
        return self.queue.full()

    #  12.2.8.2.6
    #     The SystemVerilog UVM flushes the Queue
    #     using a while loop and counting the number
    #     of threads waiting for a get. If there are
    #     still threads waiting after the loop runs
    #     it issues an error.
    #
    #     In pyuvm we just flush the loop and clear
    #     all the unfinished tasks.

    def flush(self):
        """
        Flush out the FIFO
        """
        self.queue._queue.clear()


class uvm_tlm_analysis_fifo(uvm_tlm_fifo):
    class uvm_AnalysisExport(uvm_QueueAccessor, uvm_analysis_port):
        def write(self, item):
            try:
                self.queue.put_nowait(item)
            except QueueFull:
                raise QueueFull(
                    f"Full analysis fifo: {self.__name__}. This should never happen")  # noqa: E501

    def __init__(self, name, parent=None):
        super().__init__(name, parent, 0)
        self.analysis_export = self.uvm_AnalysisExport(name="analysis_export",
                                                       parent=self,
                                                       uvm_queue=self.queue,
                                                       ap=None)


#    12.2.9.1
class uvm_tlm_req_rsp_channel(uvm_component):
    class uvm_MasterSlaveExport(uvm_master_port, uvm_get_peek_port):
        def __init__(self, name, parent, put_export, get_peek_export):
            super().__init__(name, parent)
            self.put_export = put_export
            self.get_peek_export = get_peek_export

        async def put(self, item):
            await self.put_export.put(item)

        def can_put(self):
            return self.put_export.can_put()

        def try_put(self, item):
            return self.put_export.try_put(item)

        async def get(self):
            return await self.get_peek_export.get()

        def can_get(self):
            return self.get_peek_export.can_get()

        def try_get(self):
            return self.get_peek_export.try_get

    def __init__(self, name, parent=None, request_fifo_size=1,
                 response_fifo_size=1):
        super().__init__(name, parent)
        self.req_tlm_fifo = uvm_tlm_fifo("request_fifo", self,
                                         request_fifo_size)
        self.rsp_tlm_fifo = uvm_tlm_fifo("response_fifo", self,
                                         response_fifo_size)

        self.put_request_export = self.req_tlm_fifo.put_export
        self.get_peek_response_export = self.rsp_tlm_fifo.get_peek_export
        self.get_peek_request_export = self.req_tlm_fifo.get_peek_export
        self.put_response_export = self.rsp_tlm_fifo.put_export
        self.request_ap = uvm_analysis_port("request_ap", self)
        self.response_ap = uvm_analysis_port("response_ap", self)

        self.master_export = self.uvm_MasterSlaveExport(
            name="master_export",
            parent=self,
            put_export=self.put_request_export,
            get_peek_export=self.get_peek_response_export)
        self.slave_export = self.uvm_MasterSlaveExport(
            name="slave_export",
            parent=self,
            get_peek_export=self.get_peek_request_export,
            put_export=self.put_response_export)

    def connect_phase(self):
        self.request_ap.connect(self.req_tlm_fifo.put_ap)
        self.response_ap.connect(self.rsp_tlm_fifo.get_ap)


class uvm_tlm_transport_channel(uvm_tlm_req_rsp_channel):
    class uvm_TransportExport(uvm_transport_port):
        def __init__(self, name, parent, req_fifo, rsp_fifo):
            super().__init__(name, parent)
            self.req_fifo = req_fifo
            self.rsp_fifo = rsp_fifo

        async def transport(self, req):
            self.req_fifo.put_export.put(req)
            return await self.rsp_fifo.get_peek_export.get()

        def nb_transport(self, req):
            if not self.req_fifo.put_export.try_put(req):
                return False
            return self.rsp_fifo.get_peek_export.try_get()

    def __init__(self, name, parent=None):
        super().__init__(name, parent, 1, 1)
        self.transport_export = self.uvm_TransportExport(
            "transport_export", self,
            req_fifo=self.req_tlm_fifo,
            rsp_fifo=self.rsp_tlm_fifo)

# UVM TLM 2
# 12.3

# This is left for future development.
