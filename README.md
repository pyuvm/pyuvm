**pyuvm** is the Universal Verification Methodology implemented in Python instead of SystemVerilog



# Description

**pyuvm** implements the most often-used parts of the UVM while taking advantage of the fact that Python does not have strict typing and does not require parameterized classes. The project refactors pieces of the UVM that were either overly complicated due to typing or legacy code.

The code is based in the IEEE 1800.2 specification and most classes and methods have the specification references in the comments.

The following sections have been implemented:

|Section|Name|Description|
|-------|----|-----------|
|5|Base Classes|uvm_object does not capture transaction timing information|
|6|Reporting Classes|Leverages logging, controlled using UVM hierarchy|
|8|Factory Classes|All uvm_void classes automatically registered|
|9|Phasing|Simplified to only common phases. Supports objection system|
|12|UVM TLM Interfaces|Fully implemented|
|13|Predefined Component Classes|Implements uvm_component with hierarchy, uvm_root singleton,run_test(), simplified ConfigDB, uvm_driver, etc|
|14 &  15|Sequences, sequencer, sequence_item|Refactored sequencer functionality leveraging Python language capabilities. Simpler and more direct implementation|


## Installation

You can install `pyuvm` with `pip`

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

# Usage

Testbenches written in the SystemVerilog UVM usually import the package like this:

```SystemVerilog
import uvm_pkg::*;
```

This gives you access to the class names without needing a path.  To get 
similar behavior with `pyuvm` us the `from` import syntax.

```Python
from pyuvm import *
```

**pyuvm** names the UVM classes as they are named in the specification. Therefore we use underscore naming as is done in SystemVerilog and not camel-casing.

We will use this test from the `examples/tinyalu` directory to discuss usage:

```python
class PythonAluTest(uvm_test):
    def build_phase(self):
        proxy = PythonProxy("proxy", self, "PROXY")
        self.env = AluEnv.create("env", self)

    def run_phase(self):
        self.raise_objection()
        seqr = ConfigDB().get(self, "", "SEQR")
        seq = AluSeq("seq")
        self.logger.info("Launching sequence")
        seq.start(seqr)
        time.sleep(1)
        self.drop_objection()
```

* We define a class that extends `uvm_test`

* There is no `uvm_component_utils()` macro. **pyuvm** automatically registers classes that extend `uvm_void` with the factory.

* The phases do not have a `phase` variable. Phasing has been refactored to support only the *common phases* as described in the specification. 

* We create the environment using the `create()` method and the factory. Notice that `create()` is now a simple class method. There is no typing-driven incantation.

* `raise_objection()` is now a `uvm_component` method. There is no longer a `phase` variable.

* The `ConfigDB()` singleton acts the same way as the `uvm_config_db` interface in the SystemVerilog UVM. **pyuvm** refactored away the `uvm_resource_db` as there are no issues with classes to manage.

* **pyuvm** leverages the Python logging system and does not implement the UVM reporting system. Every descendent of `uvm_report_object` has a `logger` data member.

* Sequences work as they do in the SystemVerilog UVM.

* We use the Python `time` module to wait for the last sequence to end.

* The TLM FIFOS use the `drop_objection()` to end all the threads waiting on blocking functions such as `get()`

## Connecting To a Simulator with **cocotb**

The examples in this repository use [cocotb](https://github.com/cocotb/cocotb) to write the BFMs and proxies that connect to a variety of simulators.

Here is an example of launching a 

```python
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge
import cocotb
from tinyalu_uvm import *

# Snipped implementation of Proxy function and BFMS

def run_uvm_test(test_name):
    root = uvm_root()
    root.run_test(test_name)

@cocotb.test()
async def test_alu(dut):
    clock = Clock(dut.clk, 2, units="us")
    cocotb.fork(clock.start())
    proxy = CocotbProxy(dut, "PROXY")
    await proxy.reset()
    cocotb.fork(proxy.driver_bfm())
    cocotb.fork(proxy.cmd_mon_bfm())
    cocotb.fork(proxy.result_mon_bfm())
    await FallingEdge(dut.clk)
    test_thread = threading.Thread(target=run_uvm_test, args=("CocotbAluTest",), name="run_test")
    test_thread.start()
    await proxy.done.wait()
    await FallingEdge(dut.clk)

```

We see the following above:

* We imported **pyuvm** into `tinyalu_uvm` using `*` so we can import all of `tinyalu_uvm.py` into here.

* `run_uvm_test()` gets the `uvm_root()` singleton and calls `run_test()` with the test name as we do in the SV UVM.

* **cocotb** owns the test and connects to the DUT. It gives us the `dut` object that gives us access to the DUT.

* We start the clock and create the `CocotbProxy`.  The class automatically stores itself in the `ConfigDB()` using the `"PROXY"` label. 

* The proxy resets the design.

* The proxy defines the three BFMs that talk to the DUT. These are all coroutines and we launch them in their own threads.

* Wait for the falling edge of the clock to let the BFMs get going. 

* Now we create a thread that uses `run_uvm_test()` to launch our **pyuvm** testbench.

* Launch the UVM thread.

* The **pyuvm** test uses the `final_phase()` method to notify us when the test is completed.

* We want one more clock to let the thread finish.


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


