# Overview

The Universal Verification Methodology (UVM) grew out of the Open Verification
Methodology (OVM) which grew out of the Advanced Verification Methdology (AVM)
which leveraged the SystemVerilog programming language.

Though this long lineage suggests that the UVM must be implemented in 
SystemVerilog, this is not the case. The UVM is a class library, and a class
library can be implemented in any object oriented programming language.

`pyuvm` implements the UVM using Python.  Creating testbenches using Python
has several advantages over SystemVerilog:

* The Python ecosystem is larger than the SystemVerilog ecosystem.  More 
developers understand Python than SystemVerilog, and Python has a long tradition
of being the language of choice for large-scale object oriented projects.

* Python is object-oriented, even more so than SystemVerilog, and so it is 
easier to deliver functions such as overridable factories in Python than
SystemVerilog.

* Python runs without a simulator, and so is faster than SystemVerilog.

* Python forces the testbench developer to separate simulated and timed
RTL code from testbench code.  This means that testbenches written with
Python support accelerated testbenches with little, if any, modification.

While Python is an excellent testbench development language, the UVM is an 
excellent Verification Library. Implementing the UVM using Python gives us
the best of both worlds.

# Pythonizing the UVM

Much of the UVM specification in IEEE-1800.2-2017 is driven by elements of
the SystemVerilog programming language.  Blindly implementing all that is in
the UVM specification is not only impossible (there are no parameters in Class
declarations, for example) but also unwise.

Many elements of Python make it much easier to create testbench code using
Python than SystemVerilog.  For example there are no arcane issues of typing, and
Python already has common tools for logging and interprocess communication.

Rather than try to mimic the UVM completely, this implementation delivers the
functionality of the UVM even if this changes the details of delivering the 
functionalty.  This section examines some differences that we'll see in 
this implementation.

## Static Typing vs. Duck Typing

SystemVerilog is a statically typed language, you declare variables to be of 
a certain type in the source code before using them.  It is also a relatively 
weakly typed languaged (relative to VHDL).  You can declare a variable to be
a `short int` and another to be an `integer` and still add them with no problem.

Python using Duck Typing, which is form of dynamic typing.  Duck typing says 
that if something looks like a duck, and acts like a duck, then we'll consider it
a duck.  That means we don't declare a variable to be of type `duck`, instead we 
call `duck.quack()` and see if we get an exception.

The UVM can be difficult to write because of its static typing. A lot of energy
goes into parameterizing classes to get the behavior you want, that problem
goes away in Python.  Instead, you see runtime errors if you mess up the typing.


## Exception Handling

Unlike SystemVerilog, Python provides the ability to raise and catch exceptions. 
While a SystemVerilog programmer needs to check to be sure that an action will
work before attempting it, a Python programmer is more likely to try the action
and catch an exception if it arises.

Uncaught exceptions rise through the call stack and eventually cause the Python
to dump out the stack trace information and exit. Catching exceptions keeps the
program from terminating. 

### `pyuvm` Exceptions

`pyuvm` implements the following exceptions:

* `UVMNotImplemented`---This means that a function call defined in the IEEE UVM 
specification has not been implemented in `pyuvm`. This could be because the code
simply hasn't been written yet, or that we did not implement this feature in
`pyuvm`.  For example the `get_type()` method has not been implemented since
Python's language capabilities make the `uvm_object_wrapper` class unecessary.   

# Differences between SystemVerilog UVM and `pyuvm`

The topics outline above lead to differences between the way `pyuvm` implements
behaviors vs. how SystemVerilog does it.  This section highlights these differences.

## Underscore Naming

While most Python programs use camel casing to define classes, `pyuvm` using underscore
naming to match the IEEE specification.  `uvm_object` is named `uvm_object` not `UvmObject`.


## Decorators and Accessor Functions

SystemVerilog allows you to `protect` a variable in a class and make it 
accessible to class users only through accessor function.  For example
`uvm_object` has `get_name()` and `set_name()` methods to access the 
name variable.  

Python implements a similar behavior using the `@property` decorator. For
example `uvm_object` implements name behavior like this:

```Python
@property
def name(self):
   return self__name

@name.setter
def name(self, name):
   assert(isinstance(name, str))
   self.obj_name = name   
```

A user refers to `obj.name` regardless of whether it is being read or written.
The double underscore before then variable (`__name`) means that we treat the 
variable as a protected variable.

Generally speaking, `pyuvm` replaces all methods starting with `set_` and `get_`
with properties, removing the prefix. This does not apply if the `set_` or `get_`
prefix is not defining functionality that works like a property.

## `uvm_object_wrapper` and Factories

SystemVerilog has relatively poor class manipulation mechanisms.  Most of
the class information has already been determined at compile time and dynamically
creating objects of different classes, or overriding one class with another, requires
considerable gymnastics.

Python, on the other hand easily handles classes.  Classes are objects just like
everything else in the language.

As a result, `pyuvm` does not need  certain UVM features 
such as the `uvm_object_wrapper` class.   

# Python Instead of UVM in a Simulator
The UVM defines methods that make up for SystemVerilog's relative
immaturity relative to Python.  For example, the UVM defines
a `convert2string()` method which is the same as Python's `__str__()`
method.  

We raise the `UsePythonMethod` exception whenever we implement a 
UVM method that can be replaced by a Python method.  This section highlights areas
where Python has made parts of the UVM unecessary.

There are also elements of the UVM that assume we are running in a simulator.

## `uvm_transaction GUI Support`

The `uvm_transaction` class contains methods that support capturing the 
simulation time so it can be displayed in a GUI.  Since we are not running
in the simulator, we implement none of these methods.  

## `uvm_policy` Class

The `uvm_policy` Classes provide functionality that is built into 
Python with the `setattr` and `getattr` methods. 

There are no field macros and thus no need to implement this class.

## `uvm_port_base` Class

Python uses the `Queue` class to implement everything done by the
port/export system in the UVM. Therefore we do not implement the
`uvm_port_base` or any of its extensions.

## `uvm_time` Class

`pyuvm` does not run in the simulator, and thus does not use time. We do not
implement the `uvm_time` class. 

## Reporting Classes
We will not

## Sychronization Classes
We will not recreate the Python `threading` package in pyuvm
