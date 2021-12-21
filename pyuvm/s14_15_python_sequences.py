# The SystemVerilog sequences provided much more functionality
# than most users ever used. This led to extremely complicated
# code.
#
# This file implements the uvm sequence functionality in
# Python using Python features instead of emulating
# SystemVerilog features.


from pyuvm.s05_base_classes import *
from pyuvm.s12_uvm_tlm_interfaces import *
from cocotb.triggers import Event as CocotbEvent

# The sequence system allows users to create and populate sequence
# items and then send them to a driver. The driver
# loops through getting the next sequence item,
# processing it, and sending the result back.
#
# Remembering that all run_phases run in their own
# thread we see this code in the driver.
#
# def run_phase(phase):
#     while True:
#        req = self.seq_item_port.get_next_item()
#        # send the req to the tinyALU and get rsp
#        self.seq_item_port.item_done(rsp)
#
# or
#    while True:
#        req = self.seq_item_port.get_next_item()
#        # do stuff
#        self.seq_item_port.item_done()
#        self.seq_item_port.put(rsp)
#
# Either way the sequence in this case does:
#
# start_item(req)
# finish_item(req)
# rsp = get_response()
#
# We see above that the driver is a simple uvm_component
# with a special port. The port does all the synchronization.
# It blocks until there is a req and then it sends the response
# back and notifies the sequencer that the transaction is done.  we have:
#
#
# From the other side, the sequence side we get this:
#
# First someone starts the sequence:
#
# test_seq.start(seqr)
#
# This puts a handle to the sequencer (seqr) in the sequence.
# Then this happens.
#
# def body():
#    req = Req()
#    self.start_item(req) # Request the sequencer
#    req.A = 1
#    req.B = 5
#    req.op = operators.ADD
#    self.finish_item(req) # Send and wait for item_done
#    rsp = self.get_response()
#
#    The above puts this sequence in a queue and blocks until
#      the sequence's turn comes up.

# So the sequence contains:
# start()
# start_item()
# finish_item()
# get_response()
#
# The seq_item_port (and export) contain:
# get_next_item()
# item_done()
# put()
#
# The sequencer that connects them contains:
# A fifo that holds sequences in order
# A mechanism to notify start_item that it's turn has arrived
# A mechanism to notify finish_item that the item is done
# A mechanism to return responses
# a seq_item_export
#
# The driver contains
# a seq_item_port
#
# We'll build from the seq_item_port out.


# uvm_seq_item_port
# The uvm_seq_item_port is a uvm_put_port with two extra methods.

class ResponseQueue(UVMQueue):
    """
    Returns either the next response or the item with the id.
    """

    def __init__(self, maxsize: int = 0):
        super().__init__(maxsize=maxsize)
        self.put_event = CocotbEvent("put event")

    def put_nowait(self, item):
        super().put_nowait(item)
        self.put_event.set()
        self.put_event.clear()

    async def get_response(self, txn_id=None):
        if txn_id is None:
            return await self.get()
        else:
            while True:
                item_list = list(self._queue)
                txn_list = [xx
                            for xx in item_list
                            if xx.transaction_id == txn_id]
                if len(txn_list) == 0:
                    await self.put_event.wait()
                else:
                    assert len(txn_list) == 1, \
                        f"Multiple transactionsn have the same ID: {txn_id}"
                    _ = self._queue.index(txn_list[0])
                    self._queue.remove(txn_list[0])
                    return txn_list[0]

    def __str__(self):
        return str([str(xx) for xx in self.queue])


class uvm_sequence_item(uvm_transaction):
    """
    The pyuvm uvm_sequence_item has conditions to
    implement start_item() and finish_item()
    """

    def __init__(self, name):
        super().__init__(name)
        self.start_condition = CocotbEvent()
        self.finish_condition = CocotbEvent()
        self.item_ready = CocotbEvent()
        self.parent_sequence_id = None
        self.response_id = None

    def set_context(self, item):
        """
        Use this to link a new response transaction to the request transaction.
        rsp.set_context(req)

        :param item: The request transaction
        :return:
        """
        self.response_id = (item.parent_sequence_id, item.get_transaction_id())


class uvm_seq_item_export(uvm_blocking_put_export):
    """
    The sequence item port with a request queue and
    a response queue.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.req_q = UVMQueue()
        self.rsp_q = ResponseQueue()
        self.current_item = None

    async def put_req(self, item):
        """
        put request into request queue

        :param item: request item
        :return:
        """
        await self.req_q.put(item)

    def put_response(self, item):
        """
        Put response into response queue

        :param item: response item
        :return:
        """
        self.rsp_q.put_nowait(item)

    async def get_next_item(self):
        """
        Get the next item out of the item queue
        :return: item to process
        """
        if self.current_item is not None:
            raise error_classes.UVMSequenceError(
                "You must call item_done() before calling get_next_item again")
        self.current_item = await self.req_q.get()
        self.current_item.start_condition.set()
        self.current_item.start_condition.clear()
        await self.current_item.item_ready.wait()
        return self.current_item

    def item_done(self, rsp=None):
        """
        Signal that the item has been completed. If item is not none
        put it into the response queue.

        :param rsp: item to put in response queue if not None
        """
        if self.current_item is None:
            raise error_classes.UVMSequenceError(
                "You must call get_next_item before calling item_done")
        self.current_item.finish_condition.set()
        self.current_item.finish_condition.clear()
        self.current_item = None
        if rsp is not None:
            self.put_response(rsp)

    async def get_response(self, transaction_id=None):
        """
        If transaction_id is not none, block until a
        response with the transaction id becomes available.
        :param transaction_id: The transaction ID of the response
        :return:
        """
        datum = await self.rsp_q.get_response(transaction_id)
        return datum


class uvm_seq_item_port(uvm_port_base):
    def connect(self, export):
        self.check_export(export)
        super().connect(export)

    async def put_req(self, item):
        """Put a request item in the request queue"""
        await self.export.put_req(item)

    def put_response(self, item):
        """Put a response back in the queue. aka put_response"""
        self.export.put_response(item)

    async def get_next_item(self):
        """get the next sequence item from the request queue
        """
        try:
            return await self.export.get_next_item()
        except AttributeError:
            assert self.export is not None, "export is not connected"
            raise

    def item_done(self, rsp=None):
        """Notify finish_item that the item is complete"""
        self.export.item_done(rsp)

    async def get_response(self, transaction_id=None):
        """
        Either get a response item with the given transaction_id,
        or get the first one in the queue.

        Removes the found transaction.

        If there is no transaction in the queue with transaction_id,
        block until it appears.
        """
        datum = await self.export.get_response(transaction_id)
        return datum


# The UVM sequencer is really just a holder for the
# seq_item_export that does all the work.


class uvm_sequencer(uvm_component):
    """
    The uvm_sequencer arbitrates between multiple sequences that want to send
    items to driver (connected to seq_export) It exposes put_req,
    get_next_item, get_response from the export.
    The sequence will use these to coordinate
    items with the sequencer.
    """

    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.seq_item_export = uvm_seq_item_export("seq_item_export", self)
        self.seq_q = UVMQueue(0)

    async def run_phase(self):
        while True:
            next_item = await self.seq_q.get()
            await self.seq_item_export.put_req(next_item)

    async def start_item(self, item):
        await self.seq_q.put(item)
        await item.start_condition.wait()

    async def finish_item(self, item):
        item.item_ready.set()
        item.item_ready.clear()
        await item.finish_condition.wait()

    async def put_req(self, req):
        await self.seq_item_export.put_req(req)

    async def get_response(self, txn_id=None):
        datum = await self.seq_item_export.get_response(txn_id)
        return datum

    async def get_next_item(self):
        next_item = await self.seq_item_export.get_next_item()
        return next_item


class uvm_sequence(uvm_object):
    """
    The uvm_sequence creates a series of sequence
    items and feeds them to the sequencer
    using start_item() and finish_item(). It can
    also get back results with get_response()
    body() gets launched in a thread at start.
    """

    def __init__(self, name="uvm_sequence"):
        super().__init__(name)
        self.sequencer = None
        self.running_item = None
        self.sequence_id = id(self)

    async def body(self):
        """
        This function gets launched in a thread when you run start()
        You generally override it in any extension.
        """

    async def start(self, seqr=None):
        if seqr is not None:
            assert (isinstance(seqr, uvm_sequencer)), \
                "Tried to start a sequence with a non-sequencer"
        self.sequencer = seqr
        await self.body()

    async def start_item(self, item):
        """
        Sends an item to the sequencer and waits to be notified
        when the item has been selected to be run.

        :param item: The sequence item to send to the driver.
        """
        if self.sequencer is None:
            raise error_classes.UVMSequenceError(
                "Tried start_item in a virtual "
                f"sequence {self.get_full_name()}")
        item.parent_sequence_id = self.sequence_id
        self.running_item = item
        await self.sequencer.start_item(item)

    async def finish_item(self, item):
        if self.sequencer is None:
            raise error_classes.UVMSequenceError(
                "Tried finish_item in virtual"
                f" sequence: {self.get_full_name()}")
        await self.sequencer.finish_item(item)

    async def get_response(self):
        if self.sequencer is None:
            raise error_classes.UVMSequenceError(
                "Tried to do get_response in a virtual "
                f"sequence: {self.get_full_name()}")
        datum = await self.sequencer.get_response(
            self.running_item.response_id)
        return datum
