
# Why Python?
## `pyuvm`: An IEEE 1800.2 Implementation
# Why Consider Python
 While the Universal Verification Methodology (UVM) continues to dominate the industry for both ASIC and FPGA verification projects, achieving greater than 50% usage in both industry segments, there remains a substantial portion of the verification community for whom UVM is not a viable option.
There are many reasons for this situation, starting with a lack of knowledge of – and resistance to learning – SystemVerilog, for either design or for verification. Especially in the military/aerospace (mil/aero) segments, the pervasive use of VHDL makes it difficult for a SystemVerilog-based solution, such as UVM, to achieve any significant market penetration.

It could be argued (and in fact is has been) that it would be in their best interests to “bite the bullet” and move to SystemVerilog in order to take advantage of the unique capabilities of the language for verification, particularly constrained-random data generation and functional coverage. While there have been some attempts to mimic these capabilities through open-source VHDL libraries, the best that has been achieved is to approximate the structured component-based approach of UVM to improve modularity and reuse for VHDL users, but any attempt at constrained-random coverage-driven verification has been rudimentary at best.

Of course, this kind of institutional inertia has always existed. This is the very reason that SystemVerilog was created as a strict superset of Verilog, to at least make it seem like it was not a new language, even though it introduced many powerful programming features, most notably Object-Oriented Programming. Clearly, the success of SystemVerilog and UVM has proven the utility of this approach. But what comes next?

Mil/Aero companies are currently on a college hiring spree. For all the success that SystemVerilog and VHDL have had in the industry, there are precious few colleges where they are taught, meaning that today’s new engineers often do not enter “real life” with a working knowledge of the major languages used by our industry. Instead, this growing cohort prefers newer languages like Python and others. 

As we know, the sheer volume of legacy design code and “back-end” tool flows based on SystemVerilog and VHDL means that these language will continue to dominate the design side of the equation for the foreseeable future. But there is evidence that new languages for verification could be viable, given the proper tool support in simulation and emulation. Efforts such as CocoTB prove that even basic attempts to write verification environments in Python can attract interest. But for a Python-based solution to really be viable, it would need to provide all of the functionality from SystemVerilog and UVM.
# What’s Different About Python?
To see the difference between Python and SystemVerilog and VHDL one has to indulge in a bit of language history. The engineers who created the first programming languages were augmenting assembly language programming, and thus could not get away from the notion that different data types took a different number of bits.
They devised language types to ensure that programs allotted the correct number of bytes for the given type (thus we have `int` and `longint`) or that several data could be sent as a block of bits (thus we have `struct`)
Compilers checked that programmers were transferring data between like types with varying degrees of strictness with the ALGOL-based languages such as Ada, and VHDL taking a hard line, and the CPL based languages such as C and SystemVerilog allowing flexibility between types.
There are two assumptions that go into all these languages:
* Programmers are, at core, transferring bits between variables that have been correctly sized.
* Programmers must ask the language’s permission before transferring data between variables, otherwise bits could get overwritten.
Python is different in two ways:
* Python programmers are, at core, transferring handles to objects. The handles are all the same size and so they always transfer properly.
* Programmers ask forgiveness instead of permission.  Programmers can read any member from an object, and if the  member doesn’t exist Python raises a runtime exception.
We will see below how asking forgiveness instead of permission makes it easier to write and maintain testbenches.
## Parameters: The Bane of Programming
One can think of languages as either manipulating bits (C, Verilog) or manipulating objects (Simula, Python). However one can also imagine a bit-manipulating language that wants to manipulate objects. For example, inspired by Simula Bjarne Stroustrup created *C with Classes* which became C\+\+.[^1]
The problem here was that the classes were stored as bits and the compiler needed to keep track of the size of all the data members in a class.  This created problems of reuse when you had a class, say a FIFO, that could be used to store `int` or `shortint` or `char`.  How do you write one set of code for all FIFOS when you don’t know the size of the data being stored?  You create typing parameters that provide the size of the data in the FIFO. 
SystemVerilog ran into the same problem when classes were introduced to Verilog.  A class, such as a `uvm_tlm_fifo` needs a parameter to provide the type being run through the FIFO, and each parameterized class becomes a different type. This makes for convoluted class diagrams and lots of syntax errors.
As we’ll see, life is much easier in Python since all variables hold instances of objects.  This, combined with asking forgiveness instead of permission makes it much easier to write testbench code in Python.
## Class Instances Everywhere
*Everything* in Python is an instance of an object. Consider the number `5`.  The `type()` method returns the type of an object and so we can do this at a python command line:
```text
>>> type(5)
<class 'int'>
```
The example above shows that the number `5` is an instance of the `class int`.  Yet we can also see that `int` is also an object.
```text
>>> type(int)
<class 'type'>
```
So we see that `int` is of class `type`.  The `type` class is the default root class for all classes in a Python program. Though, we’ll see below that we can change this for our benefit.
# Just Enough Python
In this section we’ll cover just enough Python to be able to talk about how IEEE 1800.2 was implemented in Python. One of the advantages of Python is that is comes with an enormous ecosystem of training classes, websites, and books that delve deeply into the language.[^2]
## Defining Classes
The `class` statement defines a new class, but unlike SystemVerilog or C, Python executes the `class` statement rather than compiling it. When we execute the `class` statement it creates a new class object and stores it in the script’s list of classes for later use.
Here is a simple example:
```text
class Animal():
...     def __init__(self, name):
...         self.name = name
... 
...     def say_name(self):
...         print(self.name)
... 
...     def make_sound(self):
...         print("generic sound")
... 
aa = Animal(4433)
aa.say_name()
4433
aa.make_sound()
generic sound
```
The above example demonstrates common elements of class declaration. The first thing we notice is the infamous Python indenting. Python uses indenting instead of `begin/end` or `{/}` to signify blocks. Whether one likes this is largely personal taste, but there it is.
The `def __init__(self, name):` overrides the `__init__` method and demonstrates the double underscore convention for methods that exist in all classes.  The `__init__` method does the initialization one usually does in `new()` in SystemVerilog.  There are many such methods including `__str__`  and `__eq__` that server the UVM roles of `convert2string()` and `compare()`.  
The `__init__` above requires that we provide a name for the animal. You can also see that we’re not doing any type checking on the name. In the cold and bureaucratic world of this program the animal stored in `aa` received only a number.
## Inheritance
Classes can inherit attributes from other classes and override methods from the base class.  For example:
```text
class Lion(Animal):
...     def make_sound(self):
...         print("Lion roar")
... 
ll = Lion('Stanley')
ll.make_sound()
Lion roar
ll.say_name()
Stanley
```
We see here that we’ve overridden `Animal` to create a `Lion`.  We’ve only overridden the `make_sound()` method, so we inherited `__init__` and `say_name()`. 
When we call `make_sound()` Python looks for the `make_sound()` method in the `Lion` class, finds it, and executes it. When we call `say_name()` Python does not find the method in `Lion` and so it searches `Animal`. Finding the method there, it executes it.
### Multiple Inheritance
Unlike SystemVerilog, Python provides multiple inheritance. This made it much easier to implement UVM in Python than SystemVerilog since SystemVerilog required us to create classes that mimicked multiple inheritance behavior.  There are no `_imp` classes in `pyuvm`.
Given that we have `Animal`, `Lion`, and `Tiger` we can create a `Liger`:
```text
 ... class Liger(Lion, Tiger):
...     ...
... 
... ll = Liger("Bitey")
... ll.say_name()
... ll.make_sound()
Bitey
Lion roar
```
The `Liger` inherits from both `Lion` and `Tiger`.  The `...` is Python’s way of defining a class that inherits all its methods.
You’ll notice that we’ve created the dreaded *Diamond of Death* in that `Lion` and `Tiger` both inherit from `Animal` and `Liger` inherits from `Lion` and `Tiger`. In a compiled language this is a problem since one can’t tell which `make_sound()` method to call.
But Python determines this dynamically.  As above it looks for `make_sound()` in `Liger` and, not finding it, it searches the parent classes in the order they appear in the declaration. That’s why it finds the `make_sound()` in `Lion`.  
We now have enough class definition information to examine `pyuvm.`
## Exceptions are the Rule
*Asking forgiveness instead of permission* is a key Python design philosophy.  Languages such as C and SystemVerilog take the opposite approach. They use typing to ensure that a programmer cannot accidentally mix types and overwrite bits. Even those languages use the *forgiveness* philosophy when issuing runtime errors such as trying to access an array with an index beyond its range.
Python comes with built-in exceptions [^3] that extend the `BaseException` base class. It throws exceptions when we try to execute an illegal action such as trying to pull a value out of an associative array that doesn’t exist:
```text
my_array = {}
my_array['one'] = 1
my_array['two'] = 2
my_array[3] = 3
print(my_array['three'])
Traceback (most recent call last):
  File "<input>", line 1, in <module>
KeyError: 'three'
```
In the above example we created an associative array (called a *dict* in Pythonese) and stored two values in it. Notice that the keys here can be of any type. Our bug was using `3` instead of `three`. 
The `KeyError` class extends `LookupError` which extends `Exception`. The error class tree becomes important when we want to catch exceptions.
Consider a case where we’re implementing a `uvm_pool`. The IEEE 1800.2 specification says that the pool `get()` method will return the value at the key, and if they key doesn’t exist, then initialize the location at `key` from the nonexistent Table 7-1. ++where is that table?++ We’ll use the Python universal object for emptiness `None` (not to be confused with SystemVerilog `null`, which is a null pointer.  `None` is an actual object named `None`) to do the initialization.
```text
from pyuvm import *
class uvm_pool(uvm_object):
    def __init__(self):
        self.pool = {}
    def get(self, key ):
        try:
            return self.pool[key]
        except KeyError
            self.pool[key] = None
```
The `try/except` block says to try the operation, and if the operation throws an exception of type `KeyError` we recover and set the pool’s location to `None`. 
If any other kind of exception were thrown the exception would go up the call stack. If nothing caught the exception with an `except` block, then it would print to the screen and terminate the program.
### The Joy of Duck Typing
Throughout this paper, we’ve often pointed out that Python allows us to implement the UVM without the complications created by constant type-checking and the parameterization it engenders.
We can write the code this way because of the Pythonic philosophy of *duck typing*. Duck typing says that, given an object, one says “If it walks like a duck and quacks like a duck, then it is a duck.”  So we see the following:
```text
class Canary(Animal):
...     def make_sound(self):
...         print("tweet")
... 
my_duck = Canary('Phil')
try:
...     my_duck.migrate()
... except AttributeError:
...     print ("Hey. That's not a duck")
...     
Hey. That's not a duck
```
Rather than declare `my_duck` to be of type `Duck` we say that any object that has the method `migrate()` must be a `Duck`.  Given a `Canary` object we tried to make it migrate and found out that it could not. 
This is not to say that you have to blindly try any object handed to you.  You can check an object’s type so as to handle an error in a meaningful way:
```text
class Duck(Animal):
...     def make_sound(self):
...         print('quack')
...     def migrate(self):
...         print('Gone south.')
... 
assert(isinstance(my_duck, Duck)), "You must provide a Duck."
Traceback (most recent call last):
  File "<input>", line 1, in <module>
AssertionError: You must provide a Duck.
```
The `assert` statement checks a condition (`isinstance()` in this case) and raises the `AssertionError` exception if the checked condition is false.
# Implementing UVM in Python
## Key base classes, SV vs Python
## Python simplifies UVM implementation
## The Dual-Top Testbench: The Proxy Approach
## A PyUVM example
# Conclusion
This approach literally provides the best of both worlds. Rather than reinventing the wheel, we build on all of the work that has gone in over the years to the development of the UVM, the most popular verification methodology in the industry, as well as existing constraint solvers and other capabilities provided by a simulator, but provide it to a new generation of engineers in a language with which they are already familiar.

[^1]:	[Wikipedia][1]

[^2]:	The \>\>\> in the examples is the prompt from the Python interpreter.  You see the interpreter when you type `python` on the command line.

[^3]:	[https://docs.python.org/3/library/exceptions.html#bltin-exceptions][2]

[1]:	https://en.wikipedia.org/wiki/C%2B%2B#History
[2]:	https://docs.python.org/3/library/exceptions.html#bltin-exceptions "Python Built-in Exceptions"