from pyuvm import *
import random
import logging
from enum import Enum, unique, auto

# The TinyALU testbench is a simulation of a simulation demonstrating what a testbench
# looks like when written with pyuvm.

# The TinyALU is a two leg ALU with four operations ADD, AND, XOR, and MUL. This testbench
# runs ten transactions through the ALU and checks the results.

# The DUT is a uvm_component that acts similar to an XRTL testbench with a blocking set
# of function calls that return the most recently monitored command and result. 

# This example demonstrates how easily one can write a testbench in UVM, especially
# since one doesn't have to spend a lot of energy on parameters and typing.


#
# This is how Python implements an enumeration. The enumeration values are class variables
# of a class of type Enum.

@unique
class ALUOps(Enum):
    ADD = auto()
    AND = auto()
    XOR = auto()
    MUL = auto()


#
# The command transaction contains an A-leg value, a B-leg value, and an operation. 
# 
# Note that pyuvm automatically adds all classes that extend uvm_void to the factory
#
class command_transaction(uvm_sequence_item):

    def __init__(self, name, A=0, B=0, op=ALUOps.ADD):
        """
        Similar to the `new()` method in SystemVerilog. It initializes the
        transaction.
        """
        super().__init__(name)
        self.A = A
        self.B = B
        self.op = op


    def __str__(self):
        """
        The equivalent of the UVM convert2string() method but works 
        automatically with all functions that take a string as an input
        such as print()
        """
        if((self.op == ALUOps.AND) or (self.op == ALUOps.XOR)):
            return f"{self.A:#0x} {self.op} {self.B:#0x}"
        else: 
            return f"{self.A} {self.op} {self.B}"

class result_transaction(uvm_transaction):
    """
    The transaction created by the result monitor and used for comparison
    in the scoreboard.
    """
    def __init__(self, name, r):
        super().__init__(name)
        self.result = r

    # The convert2string() equivalent
    def __str__(self):
        return str(self.result)

    # This is similar to the do_compare() method
    # in the UVM. There are functions in Python that
    # can do deep comparisons if necessary.
    def __eq__(self, other):
        return self.result == other.result


# Driver
class driver(uvm_driver):
    """
    A classic UVM driver.  It inherits a seq_item_port and uses it 
    to get sequence items sent by the sequencer
    """
    def run_phase(self):
        #
        # Here is the pyuvm version of the config_db. The pyuvm
        # uvm_component has conveience routines that set and get
        # objects out of the config_db.  As with the UVM config_db
        # the component path controls which items one sees in the
        # config_db.
        #
        # The config_db is much easier to use now that we don't
        # need to worry about types.  All the data goes into a singleton
        # that manages component path names and the database.
        #

        self.bfm = self.config_db_get("DUT")

        # The bfm is a handle to the DUT, but in a real testbench
        # it would be a handle to a bfm.
        
        while True:
            command = self.seq_item_port.get_next_item()
            self.bfm.send_op(command.A, command.B, command.op)
            self.seq_item_port.item_done()


#
# Like the driver the command_monitor gets a handle to the 
# BFM from the config_db. 
#
# The bfm provides a blocking get_cmd function that returns
# commands when it sees them in the simulation
#

class command_monitor(uvm_component):
        """
        A monitor that watches the commands in the DUT and
        sends them into the analysis port as a transaction.
        """
        def build_phase(self, phase = None):
            self.ap = uvm_analysis_port("ap", self)

        def run_phase(self):
            self.monitor_bfm = self.config_db_get("DUT")
            while True:
                (A, B, op) = self.monitor_bfm.get_cmd() # the tuple allows three values to return
                mon_tr = command_transaction("mon_tr", A, B, op) # convert to a transaction
                self.ap.write(mon_tr)


class result_monitor(uvm_component):
    """
    Sends results when the TinyALU produces them into the analysis port
    as a result transaction.
    """
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    def run_phase(self):
        self.result_mon = self.config_db_get("DUT")
        while True:
            result = self.result_mon.get_result() #blocks until there is a result
            result_t = result_transaction("result", result) # create a transaction
            self.ap.write(result_t) # write it into the analysis port.


# The uvm_subscriber class extends analysis_export (which is a uvm_component)
# The subscriber promises to override the write() method.

class scoreboard(uvm_subscriber):
    """
    Waits to get results and then uses the most
    recent command to create a predicted value. Then
    it compares them and pronounces a verdict.
    """
    def build_phase(self):
        self.cmd_f = uvm_tlm_analysis_fifo("cmd_f", self) # fifo for commands
        self.cmd_p =  uvm_get_port("cmd_p", self) # a port for reading the fifo

    def connect_phase(self):
        self.cmd_p.connect(self.cmd_f.get_export) # Connect the fifo export to the port.

    # Static methods don't use the self pointer or the cls pointer. 
    # They could go anywhere but are in the class for convenience
    @staticmethod
    def predict_result(cmd):
        result = None
        if cmd.op == ALUOps.ADD:    # python replaces case with elif cascades.
            result = cmd.A + cmd.B
        elif cmd.op == ALUOps.AND:
            result = cmd.A & cmd.B
        elif cmd.op == ALUOps.XOR:
            result = cmd.A ^ cmd.B
        elif cmd.op == ALUOps.MUL:
            result = cmd.A * cmd.B
        else:
            error_classes.UVMFatalError(f"Got illegal operation {cmd.op}") # replace the uvm_fatal 
                                                                           # error message with an exception

        return result_transaction("predicted", result) # create a transaction and return it

    # Overrides the write method in the analysis_export
    def write(self, result_t):
        """
        Use the most recent command to predict a result and compare
        to the result sent to write.
        """
        success, cmd = self.cmd_p.try_get()
        if not success:
            raise error_classes.UVMFatalError(f"Got result: {result_t} with no cmd in queue")
        predicted_t = self.predict_result(cmd)
        if((cmd.op==ALUOps.AND) or (cmd.op==ALUOps.XOR)):
            predicted_s = hex(predicted_t.result)
            result_s = hex(result_t.result)
        else:
            predicted_s = predicted_t.result
            result_s = result_t.result
        if predicted_t != result_t:
            print(f"Avast! Bug here! {cmd} should make {predicted_s}, made {result_s}")
        else:
            print(f"Test passed: {cmd} = {result_s}")

# The uvm_agent encapsulates the drivers, monitors, sequencer, and scoreboard. 
# This one does not turn off the driver/sequencer pair.
class tinyalu_agent(uvm_agent):
    """ Provides the sequence and monitoring structure. """
    def build_phase(self):
        """
        Build the components that drive and monitor
        the TinyALU and put them in one component
        with exposed analysis ports.
        """

        self.cm_h = command_monitor("cm_h",self) # Add the command monitor
        self.dr_h = driver("dr_h", self)         # the driver (note no parameter)
        self.seqr = uvm_sequencer("seqr", self)  # the sequncer (note no parameter here either)

        self.config_db_set(self.seqr, "SEQR", "*") # Store the sequencer in the config_db

        # Make with the factory
        self.rm_h = self.create_component("result_monitor", "rm_h") # Now the factory methods
        self.sb_h = self.create_component("scoreboard", "sb")       # can be part of uvm_component
                                                                    # No typing issues.

        self.cmd_mon_ap = uvm_analysis_port("cmd_mon_ap", self)     # The agent provides two
        self.result_ap = uvm_analysis_port("result_ap", self)       # analysis ports.

    def connect_phase(self):
                                               # Notice that ports can be connected to ports.
        self.cm_h.ap.connect(self.cmd_mon_ap)  # connect the command monitor ap to the exposed ap
        self.rm_h.ap.connect(self.result_ap)   # connect the result monitor ap to the expose ap

        self.dr_h.seq_item_port.connect(self.seqr.seq_item_export) # Connect driver to sequencer
        
        self.cm_h.ap.connect(self.sb_h.cmd_f.analysis_export) # Connect the command monitor to an
                                                              # analysis FIFO in the scoreboard
        self.rm_h.ap.connect(self.sb_h)  # The scoreboard connects directly to the result analysis_port.


class tinyalu_dut(uvm_component):
    """
    The DUT pretends to be some sort of TLM interface. It exposes
    function calls that deliver the operation and results to the
    associated monitors.
    send_op--Starts an operation
    get_op--Waits for an operation to be available and returns it
    get_result--Waits for a result to be available and returns it
    """

    def build_phase(self):
        # Use FIFOs to send data to ALU and

        # Create infrastructure for getting ALU commands
        self.cmd_put_p = uvm_blocking_put_port("op_put_p", self)
        self.cmd_fifo = uvm_tlm_fifo("fifo", self)
        self.cmd_get_p = uvm_get_port("op_p", self)

        # Create command monitoring infrastructure with analysis fifo
        self.cmd_mon_put_p = uvm_blocking_put_port("op_mon_put_p", self)
        self.cmd_mon_fifo  = uvm_tlm_analysis_fifo("op_mon_fifo", self)
        self.cmd_mon_get_p = uvm_blocking_get_port("op_mon_get_p", self)

        # Here is result monitoring infrastructure with analysis fifo
        self.result_mon_put_p = uvm_blocking_put_port("result_mon_put_p", self)
        self.result_mon_fifo  = uvm_tlm_analysis_fifo("result_mon_fifo", self)
        self.result_mon_get_p = uvm_blocking_get_port("result_mon_get_p", self)

        # Store the DUT where people can get it
        # in the config DB.  Notice that the * works for all paths.
        self.config_db_set(self, "DUT", "*")

    def connect_phase(self):
        # Connect up the command fifo
        self.cmd_get_p.connect(self.cmd_fifo.get_export)
        self.cmd_put_p.connect(self.cmd_fifo.put_export)

        # Connect the command monitoring fifo
        self.cmd_mon_put_p.connect(self.cmd_mon_fifo.put_export)
        self.cmd_mon_get_p.connect(self.cmd_mon_fifo.get_export)

        # Connnect the result monitoring fifo
        self.result_mon_put_p.connect(self.result_mon_fifo.put_export)
        self.result_mon_get_p.connect(self.result_mon_fifo.get_export)


    # The driver calls this function
    def send_op(self, A, B, op):
        """
        Send the A and B values as well as the operation to the ALU
        """
        cmd_t = command_transaction("cmd_t", A, B, op) 
        self.cmd_put_p.put(cmd_t) # blocks until the previous command is processed

    # The command monitor calls this function
    def get_cmd(self):
        """
        Get the command as seen in the DUT
        """
        cmd = self.cmd_mon_get_p.get() # blocks until there is a command seedn on the DUT
        return cmd

    def get_result(self):
        """
        Get the result from the DUT
        """
        result = self.result_mon_get_p.get() # blocks until there is a result seen on the DUT
        return result

    def run_phase(self):
        """
        Gets the next command and processes it.  This is the
        simulated DUT. The sleep statement simulates the simulation
        time spent in the DUT.
        """
        while True:
            cmd = self.cmd_get_p.get()
            self.cmd_mon_put_p.put((cmd.A, cmd.B, cmd.op))
            time.sleep(0.5) # Aparently very slow.
            result = None
            if cmd.op == ALUOps.ADD:
                result = cmd.A + cmd.B
            elif cmd.op == ALUOps.AND:
                result = cmd.A & cmd.B
            elif cmd.op == ALUOps.XOR:
                result = cmd.A ^ cmd.B
            elif cmd.op == ALUOps.MUL:
                result = cmd.A * cmd.B
            self.result_mon_put_p.put(result)

# The environment (env) instantiates the agent.
class env(uvm_env):

    def build_phase(self):
        self.agent = tinyalu_agent("agent",self)

# This is a sequence. It creates command transactions,
# randomizes them, and sends them to the DUT.
class alu_sequence(uvm_sequence):
    """
    Sends ten random transactions to the testbench
    """
    def body(self):
        cmd_tr = command_transaction("cmd_tr")
        for ii in range(10):
            self.start_item(cmd_tr) # UVM start_item gets the sequencer
            cmd_tr.A = random.randint(0,255) # use Python randomization
            cmd_tr.B = random.randint(0,255)
            cmd_tr.op = random.choice(list(ALUOps)) # Pick an operation
            self.finish_item(cmd_tr) # UVM finish_item waits for the driver to call item_done
        time.sleep(1) # give the last transaction time to go through

# The test instantiates the environment and the DUT. There is
# no need to connect them. The DUT stores itself in the
# config_db where the driver and monitors can find it.
class alu_test(uvm_test):
    """
    Runs ten random transactions through the DUT
    """
    def build_phase(self):
        """
        Intantiate the environment and DUT
        """
        self.env = env("env", self)
        self.dut = tinyalu_dut("dut", self)

    def run_phase(self):
        """
        Run the sequence through the DUT
        """
        self.raise_objection() # Keeps the phase from advancing until the sequence is done.
        seq = alu_sequence("seq") # Here is the ten item sequencer
        seqr = self.config_db_get("SEQR") # The sequencer stored itself in the config_db
        seq.start(seqr) # Start the sequence on the sequencer.
        time.sleep(1) # Give everything time to settle out.
        self.drop_objection() # Allow the testbench to go to the next phase


if __name__ == '__main__':
    uvm_root().run_test("alu_test") # Launch the testbench with run_test()

