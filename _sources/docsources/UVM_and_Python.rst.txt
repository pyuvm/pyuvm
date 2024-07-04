UVM and Python
==============

The Universal Verification Methodology (UVM) grew out of the Open Verification
Methodology (OVM) which grew out of the Advanced Verification Methdology (AVM)
which leveraged the SystemVerilog programming language.

Though this long lineage suggests that the UVM must be implemented in 
SystemVerilog, this is not the case. The UVM is a class library, and a class
library can be implemented in any object oriented programming language.

**pyuvm** implements the UVM using Python.  Creating testbenches using Python
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

Pythonizing the UVM
-------------------

Much of the UVM specification in IEEE-1800.2-2017 is driven by elements of
the SystemVerilog programming language.  Blindly implementing all that is in
the UVM specification is not only impossible (there are no parameters in Class
declarations, for example), but also unwise.

Many elements of Python make it much easier to create testbench code using
Python than SystemVerilog.  For example, there are no arcane issues of typing, and
Python readily provides generic tools for logging and interprocess communication.

Rather than attempting to mimic the UVM completely, this implementation focuses on delivering the
functionality of the UVM, even if this changes the details of how functionality is 
delivered.  This section examines some differences between 
the implementations.

Static Typing vs. Duck Typing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

SystemVerilog is a statically typed language. You declare variables to be of 
a certain type in the source code before using them.  It is a relatively 
weakly typed languaged (relative to VHDL).  You can declare a variable to be
a ``short int`` and another to be an ``integer`` and still add them with no problem.

Python using Duck Typing, which is form of dynamic typing.  Duck typing says 
that if something looks like a duck, and acts like a duck, then we'll consider it
a duck.  That means we don't declare a variable to be of type ``duck``, instead we 
call ``duck.quack()`` and see if we get an exception.

The UVM can be difficult to write because of its static typing. A lot of energy
goes into parameterizing classes to get the behavior you want, that problem
goes away in Python.  Instead, you see runtime errors if you mess up the typing.


Exception Handling
^^^^^^^^^^^^^^^^^^

Unlike SystemVerilog, Python provides the ability to raise and catch exceptions. 
While a SystemVerilog programmer needs to check to be sure that an action will
work before attempting it, a Python programmer is more likely to try the action
and catch an exception if it arises.

Uncaught exceptions rise through the call stack and eventually cause the Python
to dump out the stack trace information and exit. Catching exceptions keeps the
program from terminating. 

**pyuvm** Exceptions
^^^^^^^^^^^^^^^^^^^^

Review the documentation for the ``error_classes`` module to see the Exceptions defined in **pyuvm**.


Coding differences between SystemVerilog UVM and **pyuvm**
----------------------------------------------------------

The topics outline above lead to differences between the way **pyuvm** implements
behaviors vs. how SystemVerilog does it.  This section highlights these differences.

Underscore Naming
^^^^^^^^^^^^^^^^^

Python programs use camel casing to define classes, but **pyuvm** uses underscore
naming to match the IEEE specification.  ``uvm_object`` is named ``uvm_object`` not ``UvmObject``.


Decorators and Accessor Functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

SystemVerilog UVM sets and gets variable values using accessor functions such 
as ``set_name()`` and ``get_name``. Python implements similar functionality using
the ``@property`` decorator.  

While **pyuvm** could have changed all the accessor functions to properties, it implements
the IEEE 1800.2 spec and keeps the accessor functions.

``uvm_object_wrapper`` and Factories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

SystemVerilog has relatively poor class manipulation mechanisms.  Most of
the class information has already been determined at compile time and dynamically
creating objects of different classes, or overriding one class with another, requires
considerable gymnastics.

Python, on the other hand easily handles classes.  Classes are objects just like
everything else in the language.

As a result, **pyuvm** does not need the macros we use in SystemVerilog to 
register classes with the factory.  It does not have `uvm_object_utils` or `uvm_component_utils` 
macros.  It registers all classes that extend ``uvm_void`` with the factory.


Using Python functionality instead of UVM functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The UVM defines methods that make up for SystemVerilog's relative
immaturity relative to Python.  For example ``uvm_object`` defines 
a `get_type()` method to get the type of an object.  Python has a ``type()`` 
function that does the same thing for all objects.

Therefore, **pyuvm** raises ``UsePythonMethod`` if you call ``get_type()``.

``uvm_policy`` Class
^^^^^^^^^^^^^^^^^^^^^^

The ``uvm_policy`` Classes provide functionality that is built into 
Python with the ``setattr`` and ``getattr`` methods. 

There are no field macros and thus no need to implement this class.

Reporting Classes
^^^^^^^^^^^^^^^^^

We use Python logging instead of the UVM reporting system.

