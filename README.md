# Important Note about pyuvm 2.0
**Release 2.0 breaks release 1.0 code.**

**pyuvm** originally used threads to manage concurrent simulation events. While this provided flexiblity to use **pyuvm** with any DPI interface to the simulator, it was much more difficult to use and it didn't take advantage of the excellent work done in **cocotb**.

You can get the original threaded version on the `threaded` branch in GitHub.  This version is better than the `1.0` tag as it has regression scripts.



# Description

**pyuvm** is the Universal Verification Methodology implemented in Python instead of SystemVerilog. **pyuvm** uses cocotb to interact with the simulator and schedule simulation events.

**pyuvm** implements the most often-used parts of the UVM while taking advantage of the fact that Python does not have strict typing and does not require parameterized classes. The project refactors pieces of the UVM that were either overly complicated due to typing or legacy code.

The code is based in the IEEE 1800.2 specification and most classes and methods have the specification references in the comments.

The following IEEE 1800.2 sections have been implemented:

|Section|Name|Description|
|-------|----|-----------|
|5|Base Classes|uvm_object does not capture transaction timing information|
|6|Reporting Classes|Leverages logging, controlled using UVM hierarchy|
|8|Factory Classes|All uvm_void classes automatically registered|
|9|Phasing|Simplified to only common phases. Supports objection system|
|12|UVM TLM Interfaces|Fully implemented|
|13|Predefined Component Classes|Implements uvm_component with hierarchy, uvm_root singleton,run_test(), simplified ConfigDB, uvm_driver, etc|
|14 & 15|Sequences, sequencer, sequence_item|Refactored sequencer functionality leveraging Python language capabilities. Simpler and more direct implementation|


## Installation

You can install **pyuvm** using `pip`. This will also install **cocotb** as a requirement for **pyuvm**.

```bash
% pip install pyuvm
```

Then you can run a simple test:

```
% python
>>> from pyuvm import *
>>> my_object = uvm_object("my_object")
>>> type(my_object)
<class 's05_base_classes.uvm_object'>
>>> print("object name:", my_object.get_name())
object name: my_object
```

## Running from the repository

You can run pyuvm from a cloned repository by adding the repository path to `PYTHONPATH`

```bash
% export PYTHONPATH=$PYTHONPATH:<path to repository>
```

If you also cloned **cocotb** you'll need to add that to the `PYTHONPATH` as well.

# Usage

This section demonstrates running an example simulation and then shows how the example has been put together demonstrating what the UVM looks like in Python. 

## Running the simulation

The TinyALU is, as its name implies, a tiny ALU. It has four operations: ADD, AND, NOT, and MUL. This example shows us running the Verilog version of the design, but there is also a VHDL version.

**cocotb** uses a Makefile to run its simulation. We see it in `examples/TinyALU`:

```makefile
CWD=$(shell pwd)
COCOTB_REDUCED_LOG_FMT = True
SIM ?= icarus
VERILOG_SOURCES =$(CWD)/hdl/verilog/tinyalu.sv
MODULE := tinyalu_cocotb
TOPLEVEL := tinyalu
COCOTB_HDL_TIMEUNIT=1us
COCOTB_HDL_TIMEPRECISION=1us
include $(shell cocotb-config --makefiles)/Makefile.sim
```

You can learn more about the Makefile targets at [cocotb.org](https://docs.cocotb.org/en/stable/building.html).  The `cocotb-config` command on the last line points to the **cocotb** Makefile locations and launches the `sim` target. 

Modify the `SIM` variable to match your simulator. All the simulator types are in `cocotb/share/makefiles/simulators/makefile.$(SIM)`.

You should be able to run the simulation like this:

```bash
% cd <path>/pyuvm/examples/TinyALU
% make sim
```

**cocotb** will present a lot of messages, but in the middle of them you will see these UVM messages. It runs four examples with one for each command with randomized operands.

```text
DEBUG: tinyalu_uvm.py(65)[uvm.uvm_test_top.env.driver]: Sent command: cmd_tr : A: 0x42 OP: ADD (1) B: 0x77
DEBUG: tinyalu_uvm.py(65)[uvm.uvm_test_top.env.driver]: Sent command: cmd_tr : A: 0x9f OP: AND (2) B: 0x03
DEBUG: tinyalu_uvm.py(65)[uvm.uvm_test_top.env.driver]: Sent command: cmd_tr : A: 0xe1 OP: XOR (3) B: 0x00
DEBUG: tinyalu_uvm.py(65)[uvm.uvm_test_top.env.driver]: Sent command: cmd_tr : A: 0x99 OP: MUL (4) B: 0xf9
INFO: tinyalu_uvm.py(106)[uvm.uvm_test_top.env.scoreboard]: PASSED: 0x42 ADD 0x77 = 0x00b9
INFO: tinyalu_uvm.py(106)[uvm.uvm_test_top.env.scoreboard]: PASSED: 0x9f AND 0x03 = 0x0003
INFO: tinyalu_uvm.py(106)[uvm.uvm_test_top.env.scoreboard]: PASSED: 0xe1 XOR 0x00 = 0x00e1
INFO: tinyalu_uvm.py(106)[uvm.uvm_test_top.env.scoreboard]: PASSED: 0x99 MUL 0xf9 = 0x94d1
```

# The `pyuvm` testbench

The `tinyalu_uvm.py` contains the entire UVM testbench and connects to the TinyALU through a `CocotbProxy` object defined in `tinyalu_cocotb.py`. This file also contains the **cocotb** test and BFMs.  We'll examine the `tinyalu_uvm.py` file and enough of the **cocotb** test too run the simlation

## Importing `pyuvm`

Testbenches written in the SystemVerilog UVM usually import the package like this:

```systemverilog
import uvm_pkg::*;
```

This gives you access to the class names without needing a package path.  To get 
similar behavior with `pyuvm` us the `from` import syntax.

```python
from pyuvm import *
```
## The AluTest class

We're going to examine the UVM classes from the top, the test, to the bottom, the sequences.

**pyuvm** names the UVM classes as they are named in the specification. Therefore **pyvu use underscore naming as is done in SystemVerilog and not camel-casing.

We extend `uvm_test` to create the `AluTest`, using camel-casing in our code even if **pyuvm** does not use it:

You'll see the following in the test:

* We define a class that extends `uvm_test`. 

* There is no `uvm_component_utils()` macro. **pyuvm** automatically registers classes that extend `uvm_void` with the factory.

* The phases do not have a `phase` variable. Phasing has been refactored to support only the *common phases* as described in the specification. 

* We create the environment using the `create()` method and the factory. Notice that `create()` is now a simple class method. There is no typing-driven incantation.

* `raise_objection()` is now a `uvm_component` method. There is no longer a `phase` variable.

* The `ConfigDB()` singleton acts the same way as the `uvm_config_db` interface in the SystemVerilog UVM. **pyuvm** refactored away the `uvm_resource_db` as there are no issues with classes to manage.

* **pyuvm** leverages the Python logging system and does not implement the UVM reporting system. Every descendent of `uvm_report_object` has a `logger` data member.

* Sequences work as they do in the SystemVerilog UVM.

```python
class AluTest(uvm_test):
    def build_phase(self):
        self.env = AluEnv.create("env", self)

    def end_of_elaboration_phase(self):
        self.set_logging_level_hier(logging.DEBUG)

    async def run_phase(self):
        self.raise_objection()
        seqr = ConfigDB().get(self, "", "SEQR")
        dut = ConfigDB().get(self,"","DUT")
        seq = AluSeq("seq")
        await seq.start(seqr)
        await ClockCycles(dut.clk, 50)  # to do last transaction
        self.drop_objection()

```
All the familiar pieces of a UVM testbench are in **pyuvm**.

## The ALUEnv Class

The `uvm_env` class is a container for the components that make up the testbench.  There are four component classes instantiated:
* `Monitor`—There are actually two monitors instantiated, one to monitor commands (`self.cmd_mod`) and the other to monitor results (`self.result_mon`).  The `Monitor` code is the same for both. We pass them the name of the proxy function that gets the data they monitor.
* `Scoreboard`—The scoreboard gathers all the commands and results and compares predicted results to actual results.
* `Coverage`—The coverage class checks that we've covered all the kinds of operations and issues an error if we did not.
* `Driver`—This `uvm_driver` processes sequences items.
* `uvm_sequencer`—The `uvm_sequencer` queues sequence items and passes them to the `Driver`
* We store `self.seqr` in the `ConfigDB()` so test can get it as we see above.

The `AluEnv` creates all these components in `build_phase()` and connects the exports to the ports in `connect_phase()`. The `build_phase()` is a top-down phase and the `connect_phase()` is a bottom up phase.

```python
class AluEnv(uvm_env):

    def build_phase(self):
        self.cmd_mon = Monitor("cmd_mon", self, "get_cmd")
        self.result_mon = Monitor("result_mon", self, "get_result")
        self.scoreboard = Scoreboard("scoreboard", self)
        self.coverage = Coverage("coverage", self)
        self.driver = Driver("driver", self)
        self.seqr = uvm_sequencer("seqr", self)
        ConfigDB().set(None, "*", "SEQR", self.seqr)
        ConfigDB().set(None, "*", "CVG", self.coverage)
        
    def connect_phase(self):
        self.cmd_mon.ap.connect(self.scoreboard.cmd_export)
        self.cmd_mon.ap.connect(self.coverage)
        self.result_mon.ap.connect(self.scoreboard.result_export)
        self.driver.seq_item_port.connect(self.seqr.seq_item_export)
```
## The Monitor
The `Monitor` extends `uvm_component`. Takes the name of a `CocotProxy` method name as an argument.  It uses the name to find the method in the proxy and then calls the method. You cannot do this in SystemVerilog as there is no introspection. 

The `Monitor` creates an analysis port and writes the data it gets into the analysis port.

Notice in the `run_phase()` we use the `await` keyword to wait for the `get_cmd` or `get_result` coroutine.  Unlike SystemVerilog, Python makes it clear when you are calling a time-consuming task vs a function. Also notice that the `run_phase()` has the `async` keyword to designate that it is a coroutine. (A task in SystemVerilog.)
```python
lass Monitor(uvm_component):
    def __init__(self, name, parent, method_name):
        super().__init__(name, parent)
        self.method_name = method_name
    
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    def connect_phase(self):
        self.proxy = self.cdb_get("PROXY")

    async def run_phase(self):
        while True:
            get_method = getattr(self.proxy, self.method_name)
            datum = await get_method()
            self.ap.write(datum)  
```
## The Scoreboard
The scoreboard receives commands from the command monitor and results from the results monitor in the same order.  It uses the commands to predict the results and compares them.

* The `build_phase` uses `uvm_tlm_analysis_fifos` to receive data from the monitors and store it.
* The scoreboard exposes the FIFO exports by copying them into class data members.  As we see in the environment above, this allows us to connect the exports without reaching into the `Scoreboard's` inner workings.
* We connect the exports in the `connect_phase()`
* The `check_phase() runs after the `run_phase()`.  At this point the scoreboard has all operations and results. It loops through the operations and predicts the result, then it compares the predicted and actual result.
* Notice that we do not use UVM reporting. Instead we us the Python `logging` module. Every `uvm_report_object` and its children has its own logger stored in `self.logger.`
```python
class Scoreboard(uvm_component):  

    def build_phase(self):
        self.cmd_fifo = uvm_tlm_analysis_fifo("cmd_fifo", self)
        self.result_fifo = uvm_tlm_analysis_fifo("result_fifo", self)
        self.cmd_get_port = uvm_get_port("cmd_get_port", self)    
        self.result_get_port = uvm_get_port("result_get_port", self)
        self.cmd_export = self.cmd_fifo.analysis_export
        self.result_export = self.result_fifo.analysis_export

    def connect_phase(self):
        self.cmd_get_port.connect(self.cmd_fifo.get_export)
        self.result_get_port.connect(self.result_fifo.get_export)

    def check_phase(self):
        while self.result_get_port.can_get():
            _, actual_result = self.result_get_port.try_get()
            cmd_success, cmd = self.cmd_get_port.try_get()
            if not cmd_success:
                self.logger.critical(f"result {actual_result} had no command")
            else:
                (A, B, op_numb) = cmd
                op = Ops(op_numb)
                predicted_result = alu_prediction(A, B, op)
                if predicted_result == actual_result:
                    self.logger.info(f"PASSED: 0x{A:02x} {op.name} 0x{B:02x} ="
                                     f" 0x{actual_result:04x}")
                else:
                    self.logger.error(f"FAILED: 0x{A:02x} {op.name} 0x{B:02x} "
                                      f"= 0x{actual_result:04x} expected 0x{predicted_result:04x}")
```
## Coverage

The `Coverage` Class extends `uvm_subscriber` which extends `uvm_analysis_export`.  As we see in the `AluEnv` above, this allows us to pass the object directly to the `connect()` method to connect it to an analysis port.

The `Coverage` Class overrides the `write()` method expected of a `uvm_subscriber`. If it didn't you'd get a runtime error.  The `Coverage` class uses a set to store all the operations seen. Then it subtracts that from the set of all operations. If the result has a length longer than `0` it issues an error.

Since this tesbench loops through all the operations you will not see this error.

```python
class Coverage(uvm_subscriber):
    
    def end_of_elaboration_phase(self):
        self.cvg = set()
    
    def write(self, cmd):
        (_, _, op) = cmd
        self.cvg.add(op)

    def check_phase(self):
        if len(set(Ops) - self.cvg) > 0:
            self.logger.error(f"Functional coverage error. Missed: {set(Ops)-self.cvg}")

```

## Driver

The `Driver` extends `uvm_driver` and so it works with sequences and sequence items.

The `connect_phase()` gets the proxy from the `ConfigDB()` and the `run_phase()` uses it to get items and process them by calling `send_op`.  We use `while True` because we do this forever. **cocotb** will shut down the `run_phase` coroutine at the end of simulation.

```python
class Driver(uvm_driver):
    def connect_phase(self):
        self.proxy = self.cdb_get("PROXY")

    async def run_phase(self):
        while True:
            command = await self.seq_item_port.get_next_item()
            await self.proxy.send_op(command.A, command.B, command.op)
            self.logger.debug(f"Sent command: {command}")
            self.seq_item_port.item_done()
```
## ALU Sequence
The ALU Sequence creates sequence items, randomizes them and sends them to the `Driver`. It inherits `start_item` and `finish_item` from `uvm_sequence`.

It is clear that `start_item` and `finish_item` block because we call them using the `await` keyword.  `start_item` waits for it's turn to use the sequencer, and `finish_item` sends the sequence_item to the driver and returns when the driver calls `item_done()`

```python
class AluSeq(uvm_sequence):
    async def body(self):
        for op in list(Ops): # list(Ops):
            cmd_tr = AluSeqItem("cmd_tr")
            await self.start_item(cmd_tr) 
            cmd_tr.randomize()
            cmd_tr.op = op
            await self.finish_item(cmd_tr) 
            
```

## ALU Sequence Item
The `AluSeqItem` contains the TinyALU commands.  It has two operands and an operation.

The SystemVerilog `uvm_sequence_item` class uses `convert2string()` to convert the item to a string and `do_compare()` to compare the item to another item.  We do not use these in **pyuvm** because Python has magic methods that do these functions.

`__eq__()`—This does the same thing as `do_compare()` It returns `True` if the items are equal.  This method works with the `==` operator.

`__str__()`—This does the same thing as `convert2string()`.  It returns a string version of the item. The `print` function calls this method automatically.

```python
class AluSeqItem(uvm_sequence_item):

    def __init__(self, name, aa=0, bb=0, op=Ops.ADD):
        super().__init__(name)
        self.A = aa
        self.B = bb
        self.op = Ops(op)

    def __eq__(self, other):
        same = self.A == other.A and self.B == other.B and self.op == other.op
        return same

    def __str__(self):
        return f"{self.get_name()} : A: 0x{self.A:02x} OP: {self.op.name} ({self.op.value}) B: 0x{self.B:02x}"
    
    def randomize(self):
        self.A = random.randint(0, 255)
        self.B = random.randint(0, 255)
        self.op = random.choice(list(Ops))
```

Now that we've got the UVM testbench we can call it from a **cocotb** test.
# The Cocotb Test

**cocotb** finds functions identified with the `@cocotb.test()` decorator and launches them as coroutines.  Our test does the following:

* It creates a `CocotbProxy()` object and passes it the DUT. the `CocotbProxy()` defines coroutines that act as the DUT BFMs.

* It puts the proxy and the DUT into the `ConfigDB() so that UVM objects can use them.  For example the `ALUTest` uses the DUT to wait several clock cycles using `dut.clk`.
* It resets the DUT using the `reset()` coroutine.
* It forks off the three BFMs so that the proxy can send operations, read commands, and read results.
* It awaits `uvm_root().run_test("AluTest")`.  This creates an object of type `AluTest` and launches the phases.
  
```python
@cocotb.test()
async def test_alu(dut):
    proxy = CocotbProxy(dut)
    ConfigDB().set(None, "*", "PROXY", proxy)
    ConfigDB().set(None, "*", "DUT", dut)
    await proxy.reset()
    cocotb.fork(proxy.driver_bfm())
    cocotb.fork(proxy.cmd_mon_bfm())
    cocotb.fork(proxy.result_mon_bfm())
    await uvm_root().run_test("AluTest")
```



# Contributing

As people use **pyuvm** they will certainly find features of the UVM that they wish had been implemented, such as the register layer. 

I'm currently building the testing and contribution system, and am looking forward to working with contributors.

Credits: 

* Ray Salemi—Original author, created as an employee of Siemens.
* IEEE 1800.2 Specification
* Siemens for supporting me in this effort.

# License

Copyright 2020 Siemens EDA

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

[http://www.apache.org/licenses/LICENSE-2.0](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


