# New in pyuvm 2.6

# 2.6 is potentially a breaking release

This version of pyuvm clears the singletons when you await `uvm_root().run_test()`.

You can disable this behavior with the `keep_singletons=True` argument in `run_test()`.

For example:
```
	await uvm_root().run_test("MYTEST", keep_singletons=True)
```

## `ConfigDB()` empties upon `run_test()`

This means that you cannot store data in the `ConfigDB()` in a `cocotb.test()` and
then await `run_test()`.  This raises the question of getting the `dut` argument
into the `pyuvm` testbench.

The solution is to use the `cocotb.top` in pyuvm to get access to the `dut` handle.
`cocotb.top` has the same handle as `dut` so there is no need to pass the dut
using `ConfigDB()`

## The `uvm_factory()` clears the overrides

You cannot call `set_override...` before awaiting `run_test()` Instead this must
happen in the `uvm_test` or in other components.

## Multiple tests run without side effects

This release solves the problem of side effects from `run_test()`.  **pyuvm**
was original written to have one test per simulation, but **cocotb** can run
multiple tests in one Python file.  The side effects between tests caused
unexpected results.


# Pyuvm 2.5

Thanks to the pyuvm contributors for their help with this release!

## Now requires cocotb 1.6
We now use the `start_soon()` coroutine instead of the deprecated `fork`
This means we must run with **cocotb** 1.6.0 or greater.

## Default logging level
You can now set a default logging level before simulating using a
class method. This allows debug logging in the `build_phase()`

There are two functions:

* `uvm_report_object.set_default_logging_level(<logging level>)
* `uvm_report_object.get_default_logging_level()

## Fixes to uvm_export_base

Refactored the class hierarchy so that `uvm_export_base` no longer has a
`connect()` method, a situtation that violated the UVM specification and
invited bugs.

## Fixes to logging

Logging now uses **cocotb** colorization and provides time stamps.
Also removed the ability to add formatters to the logger. Now you add
the formatter to your handler and add the handler.

You can now disable logging and remove the default streaming handler.

## Fixed the `uvm_subscriber`

`uvm_subscriber` now has an `analysis_export` data member as in the UVM spec.

## Removed the ability to call `clone()` on a `uvm_transaction`

The `clone()` method had been implemented by calling `copy.deepcopy(self)`.  This
hid the actual functionality for no good reason.  Now calls to clone tell the user
to use `copy.deepcopy()`.

copy() and `do_copy()` remains so the user can make decisions about what will be copied.


# Important Note about pyuvm 2.0+
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

You can run pyuvm from a cloned repository by installing the cloned repository using pip.

```bash
% cd <pyuvm repo directory>
% pip install -e .
```

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
MODULE := testbench
TOPLEVEL=tinyalu
TOPLEVEL_LANG=verilog
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
250000.00ns INFO     testbench.py(209)[uvm_test_top.env.scoreboard]: PASSED: 0x34 ADD 0x23 = 0x0057
250000.00ns INFO     testbench.py(209)[uvm_test_top.env.scoreboard]: PASSED: 0xf9 AND 0x29 = 0x0029
250000.00ns INFO     testbench.py(209)[uvm_test_top.env.scoreboard]: PASSED: 0x71 XOR 0x01 = 0x0070
250000.00ns INFO     testbench.py(209)[uvm_test_top.env.scoreboard]: PASSED: 0xb8 MUL 0x47 = 0x3308
250000.00ns INFO     testbench.py(209)[uvm_test_top.env.scoreboard]: PASSED: 0xff ADD 0xff = 0x01fe
250000.00ns INFO     testbench.py(209)[uvm_test_top.env.scoreboard]: PASSED: 0xff AND 0xff = 0x00ff
250000.00ns INFO     testbench.py(209)[uvm_test_top.env.scoreboard]: PASSED: 0xff XOR 0xff = 0x0000
250000.00ns INFO     testbench.py(209)[uvm_test_top.env.scoreboard]: PASSED: 0xff MUL 0xff = 0xfe01
```
# The `TinyAluBfm` in `tinyalu_utils.py`

The `TinyAluBfm` is a singleton that uses **cocotb** to communicate with the TinyALU.  The BFM exposes three coroutines to the user: `send_op()`, `get_cmd()`, and `get_result()`.

The singleton uses the `cocotb.top` variable to get the handle to the DUT.  This is the handle that we normally pass to a `cocotb.test()` coroutine.

The `TinyAluBfm` is defined in `tinyalu_utils.py` and imported into our testbench.
# The `pyuvm` testbench

The `testbench.py` contains the entire UVM testbench and connects to the TinyALU through a `TinyAluBfm` object defined in `tinyalu_utils.py`.  We'll examine the `testbench.py` file and enough of the **cocotb** test too run the simlation

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
## The AluTest classes

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
        self.env = AluEnv("env", self)

    def end_of_elaboration_phase(self):
        self.test_all = TestAllSeq.create("test_all")

    async def run_phase(self):
        self.raise_objection()
        await self.test_all.start()
        self.drop_objection()
```
We extend the `AluTest` class to create a parallel version of the test and a Fibonacci program. You can find these sequences in `testbench.py`
```
class ParallelTest(AluTest):
    def build_phase(self):
        uvm_factory().set_type_override_by_type(TestAllSeq, TestAllForkSeq)
        super().build_phase()


class FibonacciTest(AluTest):
    def build_phase(self):
        ConfigDB().set(None, "*", "DISABLE_COVERAGE_ERRORS", True)
        uvm_factory().set_type_override_by_type(TestAllSeq, FibonacciSeq)
        return super().build_phase()


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
        self.seqr = uvm_sequencer("seqr", self)
        ConfigDB().set(None, "*", "SEQR", self.seqr)
        self.driver = Driver.create("driver", self)
        self.cmd_mon = Monitor("cmd_mon", self, "get_cmd")
        self.coverage = Coverage("coverage", self)
        self.scoreboard = Scoreboard("scoreboard", self)

    def connect_phase(self):
        self.driver.seq_item_port.connect(self.seqr.seq_item_export)
        self.cmd_mon.ap.connect(self.scoreboard.cmd_export)
        self.cmd_mon.ap.connect(self.coverage.analysis_export)
        self.driver.ap.connect(self.scoreboard.result_export)
```
## The Monitor
The `Monitor` extends `uvm_component`. Takes the name of a `CocotProxy` method name as an argument.  It uses the name to find the method in the proxy and then calls the method. You cannot do this in SystemVerilog as there is no introspection.

The `Monitor` creates an analysis port and writes the data it gets into the analysis port.

Notice in the `run_phase()` we use the `await` keyword to wait for the `get_cmd` coroutine.  Unlike SystemVerilog, Python makes it clear when you are calling a time-consuming task vs a function. Also notice that the `run_phase()` has the `async` keyword to designate that it is a coroutine. (A task in SystemVerilog.)
```python
class Monitor(uvm_component):
    def __init__(self, name, parent, method_name):
        super().__init__(name, parent)
        self.method_name = method_name

    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)
        self.bfm = TinyAluBfm()
        self.get_method = getattr(self.bfm, self.method_name)

    async def run_phase(self):
        while True:
            datum = await self.get_method()
            self.logger.debug(f"MONITORED {datum}")
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
                                      f"= 0x{actual_result:04x} "
                                      f"expected 0x{predicted_result:04x}")

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

    def report_phase(self):
        try:
            disable_errors = ConfigDB().get(
                self, "", "DISABLE_COVERAGE_ERRORS")
        except UVMConfigItemNotFound:
            disable_errors = False
        if not disable_errors:
            if len(set(Ops) - self.cvg) > 0:
                self.logger.error(
                    f"Functional coverage error. Missed: {set(Ops)-self.cvg}")
                assert False
            else:
                self.logger.info("Covered all operations")
                assert True
```

## Driver

The `Driver` extends `uvm_driver` and so it works with sequences and sequence items.

The `connect_phase()` gets the proxy from the `ConfigDB()` and the `run_phase()` uses it to get items and process them by calling `send_op`.  We use `while True` because we do this forever. **cocotb** will shut down the `run_phase` coroutine at the end of simulation.

```python
class Driver(uvm_driver):
    def build_phase(self):
        self.ap = uvm_analysis_port("ap", self)

    def start_of_simulation_phase(self):
        self.bfm = TinyAluBfm()

    async def launch_tb(self):
        await self.bfm.reset()
        self.bfm.start_bfms()

    async def run_phase(self):
        await self.launch_tb()
        while True:
            cmd = await self.seq_item_port.get_next_item()
            await self.bfm.send_op(cmd.A, cmd.B, cmd.op)
            result = await self.bfm.get_result()
            self.ap.write(result)
            cmd.result = result
            self.seq_item_port.item_done()

```
## The ALU Sequence
The ALU Sequence creates sequence items, randomizes them and sends them to the `Driver`. It inherits `start_item` and `finish_item` from `uvm_sequence`.

It is clear that `start_item` and `finish_item` block because we call them using the `await` keyword.  `start_item` waits for it's turn to use the sequencer, and `finish_item` sends the sequence_item to the driver and returns when the driver calls `item_done()`

```python
class TestAllSeq(uvm_sequence):

    async def body(self):
        seqr = ConfigDB().get(None, "", "SEQR")
        random = RandomSeq("random")
        max = MaxSeq("max")
        await random.start(seqr)
        await max.start(seqr)

```
This virtual sequence launches two other sequences: `RandomSeq` and `MaxSeq`. `RandomSeq` randomizes the operands.
```python
class RandomSeq(uvm_sequence):
    async def body(self):
        for op in list(Ops):
            cmd_tr = AluSeqItem("cmd_tr", None, None, op)
            await self.start_item(cmd_tr)
            cmd_tr.randomize_operands()
            await self.finish_item(cmd_tr)
```
`MaxSeq` sets the operands to `0xff`:
```python
class MaxSeq(uvm_sequence):
    async def body(self):
        for op in list(Ops):
            cmd_tr = AluSeqItem("cmd_tr", 0xff, 0xff, op)
            await self.start_item(cmd_tr)
            await self.finish_item(cmd_tr)
```

## ALU Sequence Item
The `AluSeqItem` contains the TinyALU commands.  It has two operands and an operation.

The SystemVerilog `uvm_sequence_item` class uses `convert2string()` to convert the item to a string and `do_compare()` to compare the item to another item.  We do not use these in **pyuvm** because Python has magic methods that do these functions.

`__eq__()`—This does the same thing as `do_compare()` It returns `True` if the items are equal.  This method works with the `==` operator.

`__str__()`—This does the same thing as `convert2string()`.  It returns a string version of the item. The `print` function calls this method automatically.

```python
class AluSeqItem(uvm_sequence_item):

    def __init__(self, name, aa, bb, op):
        super().__init__(name)
        self.A = aa
        self.B = bb
        self.op = Ops(op)

    def randomize_operands(self):
        self.A = random.randint(0, 255)
        self.B = random.randint(0, 255)

    def randomize(self):
        self.randomize_operands()
        self.op = random.choice(list(Ops))

    def __eq__(self, other):
        same = self.A == other.A and self.B == other.B and self.op == other.op
        return same

    def __str__(self):
        return f"{self.get_name()} : A: 0x{self.A:02x} \
        OP: {self.op.name} ({self.op.value}) B: 0x{self.B:02x}"

```

Now that we've got the UVM testbench we can call it from a **cocotb** test.
# The Cocotb Tests

**cocotb** finds functions identified with the `@cocotb.test()` decorator and launches them as coroutines.  Our test does the following:

Here we see several tests in a single Python file.
```python
@cocotb.test()
async def alu_test(_):
    """Test ALU with random and max values"""
    await uvm_root().run_test("AluTest")


@cocotb.test()
async def parallel_alu_test(_):
    """Test ALU random and max forked"""
    await uvm_root().run_test("ParallelTest")


@cocotb.test()
async def fibonacci_sim(_):
    """Run Fibonacci program"""
    await uvm_root().run_test("FibonacciTest")
```



# Contributing

You can contribute to `pyuvm` by forking this repository and submitting pull requests.

The repository runs all needed tests using `tox`.  The test runs
`flake8` and fails if that linter finds any issues.  Visual Studio Code
can be set up to automatically check `flake8` issues.  The repository
ignores F403 and F405 issues from `flake8`.

There are three sets of `pytest` tests that test features that
don't use coroutines.  The rest of the tests are in `tests/cocotb_tests`
and need a simulator to run.


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


