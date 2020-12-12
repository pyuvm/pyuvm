# Package Description
`pyuvm` is a Python implementation of the Universal Verification Methodology 

## Installation

You can install `pyuvm` with `pip`

```bash
% pip install pyuvm
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

Then you can run a simple test:

```
% python
>>> from pyuvm import *
>>> ff = uvm_object("ff")
>>> type(ff)
<class 's05_base_classes.uvm_object'>
>>> print(ff.get_name())
ff
```


