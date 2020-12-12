# The SystemVerilog sequences provided much more functionality
# than most users ever used. This led to extremely complicated
# code.
#
# This file implements the uvm sequence functionality in
# Python using Python features instead of emulating
# SystemVerilog features.


from pyuvm.s05_base_classes import *
from pyuvm.s12_uvm_tlm_interfaces import *
from threading import Condition, enumerate


"""
The sequence system allows users to create and populate sequence items and then send them to a driver. The driver 
loops through getting the next sequence item, processing it, and sending the result back.

Remembering that all run_phases run in their own thread we see this code in the driver.

def run_phase(phase):
    while True:
       req = self.seq_item_port.get_next_item()
       # send the req to the tinyalu and get rsp
       self.seq_item_port.item_done(rsp)

or
   while True:
       req = self.seq_item_port.get_next_item()
       # do stuff   
       self.seq_item_port.item_done()
       self.seq_item_port.put(rsp)
       
Either way the sequence in this case does:

start_item(req)
finish_item(req)
rsp = get_response()

We see above that the driver is a simple uvm_component with a special port. The port
does all the synchronization.  It blocks until there is a req and then it sends the response
back and notifies the sequencer that the transaction is done.  we have:


From the other side, the sequence side we get this:

First someone starts the sequence:

test_seq.start(seqr)

This puts a handle to the sequencer (seqr) in the sequence. Then this happens.

def body():
   req = Req()
   self.start_item(req) # Request the sequencer
   # The above puts this sequence in a queue and blocks until the sequence's turn comes up.
   req.A = 1
   req.B = 5
   req.op = operators.ADD
   self.finish_item(req) # Send and wait for item_done
   rsp = self.get_response()

So the sequence contains:
start()
start_item()
finish_item()
get_response()

The seq_item_port (and export) contain:
get_next_item()
item_done()
put()

The sequencer that connects them contains:
A fifo that holds sequences in order
A mechanism to notify start_item that it's turn has arrived
A mechanism to notify finish_item that the item is done
A mechanism to return responses
a seq_item_export

The driver contains
a seq_item_port

We'll build from the seq_item_port out. 
"""


# uvm_seq_item_port
# The uvm_seq_item_port is a uvm_put_port with two extra methods.

class ResponseQueue(UVMQueue):
    """
    Returns either the next response or the item with the id.
    """

    def get_response(self, txn_id=None, timeout=None):

        if txn_id is None:
            return self.get(timeout=timeout)
        else:
            plucked = None
            with self.not_empty:
                while plucked is None:
                    pluck_list = list(self.queue)
                    try:
                        plucked = next(xx for xx in pluck_list if xx.transaction_id == txn_id)
                    except StopIteration:
                        plucked = None
                    if plucked is None:
                        self.not_empty.wait()
                    else:
                        index = pluck_list.index(plucked)
                        self.queue.remove(pluck_list[index])
                return plucked

    def __str__(self):
        return str([str(xx) for xx in self.queue])


class uvm_sequence_item(uvm_transaction):
    """
    The pyuvm uvm_sequence_item has conditions to
    implement start_item() and finish_item()
    """

    def __init__(self, name):
        super().__init__(name)
        self.start_condition = Condition()
        self.finish_condition = Condition()
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

    def put_req(self, item):
        """
        put request into request queue

        :param item: request item
        :return:
        """
        self.req_q.put(item)

    def put(self, item, timeout=None):
        """
        Put response into response queue

        :param timeout:
        :param item: response item
        :return:
        """
        self.rsp_q.put(item, timeout=timeout)

    def get_next_item(self, timeout=None):
        """
        Get the next item out of the item queue
        :param timeout:
        :return: item to process
        """
        if self.current_item is not None:
            raise error_classes.UVMSequenceError("You must call item_done() before calling get_next_item again")
        self.current_item = self.req_q.get(timeout=timeout)
        return self.current_item

    def item_done(self, rsp=None):
        """
        Signal that the item has been completed. If item is not none
        put it into the response queue.

        :param rsp: item to put in response queue if not None
        """
        if self.current_item is None:
            raise error_classes.UVMSequenceError("You must call get_next_item before calling item_done")

        with self.current_item.finish_condition:
            self.current_item.finish_condition.notify_all()
        self.current_item = None
        if rsp is not None:
            self.put(rsp)

    def get_response(self, transaction_id=None, timeout=None):
        """
        If transaction_id is not none, block until a response with the transaction
        id becomes available.
        :param transaction_id:
        :return:
        """
        datum = self.rsp_q.get_response(transaction_id, timeout)
        return datum


class uvm_seq_item_port(uvm_blocking_put_port):
    def connect(self, export):
        self.check_export(export, uvm_seq_item_export)
        super().connect(export)

    def put_req(self, item):
        """Put a request item in the request queue"""
        self.export.put_req(item)

    def put(self, item):
        """Put a response back in the queue. aka put_response"""
        self.export.put(item)

    def get_next_item(self, timeout=None):
        """get the next sequence item from the request queue
        :param timeout:
        """
        return self.export.get_next_item(timeout=timeout)

    def item_done(self, rsp=None):
        """Notify finish_item that the item is complete"""
        self.export.item_done(rsp)

    def get_response(self, transaction_id=None):
        """
        Either get a response item with the given transaction_id, or get the first one in the queue.
        Removes the found transaction.
        If there is no transaction in the queue with transaction_id, block until it appears.
        """
        datum = self.export.get_response(transaction_id)
        return datum

# The UVM sequence is really just a holder for the seq_item_export that does all
# the work.


class uvm_sequencer(uvm_component):
    """
    The uvm_sequencer arbitrates between multiple sequences that want to send
    items to driver (connected to seq_export) It exposes put_req, get_next_item,
    get_response from the export. The sequence will use these to coordinate
    items with the sequencer.
    """
    def __init__(self, name, parent):
        super().__init__(name, parent)
        self.seq_item_export = uvm_seq_item_export("seq_item_export", self)
        self.seq_q = UVMQueue(0)

    def run_phase(self):
        while True:
            next_item = self.seq_q.get()
            with next_item.start_condition:
                next_item.start_condition.notify_all()

    def start_item(self, item):
        self.seq_q.put(item)
        with item.start_condition:
            item.start_condition.wait()

    def finish_item(self, item):
        self.seq_item_export.put_req(item)
        with item.finish_condition:
            item.finish_condition.wait()

    def put_req(self, req):
        self.seq_item_export.put_req(req)

    def get_response(self, txn_id=None):
        datum = self.seq_item_export.get_response(txn_id)
        return datum

    def get_next_item(self, timeout=None):
        next_item = self.seq_item_export.get_next_item(timeout)
        return next_item


class uvm_sequence(uvm_object):
    """
    The uvm_sequence creates a series of sequence items and feeds them to the sequencer
    using start_item() and finish_item(). It can also get back results with get_response()
    body() gets launched in a thread at start.
    """

    def __init__(self, name):
        super().__init__(name)
        self.sequencer = None
        self.running_item = None
        self.body_thread = None
        self.sequence_id = id(self)

    def body(self):
        """
        This function gets launched in a thread when you run start()
        You generally override it in any extension.
        """

    def start(self, seqr=None):
        if seqr is not None:
            assert (isinstance(seqr, uvm_sequencer)), "Tried to start a sequence with a non-sequencer"
        self.sequencer = seqr
        self.body()



    def start_item(self, item):
        """
        Sends an item to the sequencer and waits to be notified
        when the item has been selected to be run.

        :param item: The sequence item to send to the driver.
        """
        if self.sequencer is None:
            raise error_classes.UVMSequenceError(f"Tried start_item in a virtual sequence {self.get_full_name()}")
        item.parent_sequence_id = self.sequence_id
        self.sequencer.start_item(item)

    def finish_item(self, item):
        if self.sequencer is None:
            raise error_classes.UVMSequenceError(f"Tried finish_item in virtual sequence: {self.get_full_name()}")
        self.sequencer.finish_item(item)

    def get_response(self):
        if self.sequencer is None:
            raise error_classes.UVMSequenceError(
                f"Tried to do get_response in a virtual sequence: {self.get_full_name()}")
        datum = self.sequencer.get_response(self.running_item.response_id)
        return datum
