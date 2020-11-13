
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
### The `self` Variable
When we declare a class in SystemVerilog we declare class variables that SystemVerilog implicitly references as in C:
```SystemVerilog
class point;
  byte unsigned x;
  byte unsigned y;

  function new(byte unsigned X, byte unsigned Y);
      x = X
      this.y = Y
  endfunction
endclass
```
In the above code the `x = X` line does the same thing as the `this.y = Y` code. They both set the instance’s variable to the constructor argument.
Python does not use the implicit assignment.
```python
class Point:
	def __init__(self, X, Y):
       self.x = X
       self.y = Y
```
Unlike the implicit `this` in SystemVerilog, Python requires that we explicitly supply the `self` variable as the first variable in an instance method.  The calling mechanism hides this from us so we see when we instantiate a point:
```python
make_my_point = Point(10,3)
```
The above causes Python to create an instance of the `Point` class and call `__init__(self, X, Y)`, passing the newly created object as `self`. 
Methods that don’t have `self` as the first argument must be either class methods (which receive a first argument of `cls`) or static methods (which have no required first argument)
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
SystemVerilog is the boiled frog of languages. The frog didn’t notice the slow heating of the water as bandaid after bandaid, kludge after kludge, and syntax after syntax were piled on top of what was originally a simple RTL solution to create something that prompts dismay in anyone who looks into the pot without proper warning.
Given that, creating the object-oriented UVM on top of SystemVerilog was a heroic exercise in ingenuity. The developers cobbled together macros, static class members, parameterization, and a judicious combination of inheritance and composition to create  a powerful object-oriented verification methodology.
The result was a clearly-defined specification IEEE 1800.2, that lays out the steps needed to create the UVM in any object-oriented language.  While it is true that we can ignore some elements of the specification such as the `*_imp` classes in a language with multiple inheritance, overall the spec gives us an excellent roadmap.
In this section we’ll examine the way Python has made it easier to implement the UVM and how we’ve structured the `pyuvm` project.
## The `pyuvm` Project
The `pyuvm` package allows users to import all the UVM classes into a Python script:
```python
from pyuvm import *
import pytlm

class tinyalu_test(uvm_test):
```
The repository organizes the project by the sections in the IEEE 1800.2 specification. So `pyuvm.py` starts like this:
```python
from enum import Enum, auto
# Support Modules
from error_classes import *
from utility_classes import *
# Section 5
from s05_base_classes import *
# Section 6
from s06_reporting_classes import *
# Section 7
from s07_recording_classes import *
```
Unlike the SystemVerilog `import` statement which reads from a compiled library unit, the Python import executes the code in the imported file. For the most part these files contain `class` statements whose execution adds another class object to the collection available classes.
The work consists primarily of going through the specification and implementing what we see there:
```python
class uvm_object(utility_classes.uvm_void):
    """
    5.3.1
    """

    def __init__(self, name=''):
        """
        Implements behavior in new()
        5.3.2
        """
        # Private
        assert (isinstance(name, str)), f"{name} is not a string it is a {type(name)}"
        self.set_name(name)
        self.__logger = logging.getLogger(name)

    def get_name(self):
        """
        5.3.4.2
        """
        assert (self.__name != None), f"Internal error. {str(self)} has no name"
        return self.__name

    def set_name(self, name):
        """
        5.3.4.1
        """
        assert (isinstance(name, str)), f"Must set the name to a string"
        self.__name = name
```
Notice above that the code honors the type definitions in the specification by checking `name`’s type using an assertion.
Notice also that the `__name` variable denotes a `protected` variable as we are accustomed to in SystemVerilog. Python implements the `protected` status by mangling the variable name, changing `__name` to `Point__name`.  So one could still access the protected variable directly, but only a monster would do that.
### Docstrings
The strings in the triple quotes `"""` right after the function definition are *docstrings*. They appear in IDEs when you hover over the function call, or in automatically generated documentation.  It could be argued that they deserve more information than the IEEE 1800.2 section number.
### Python Properties
A Python-familiar reader may take offense to the existence of a`get_name` and `set_name` as Python has done away with the need for these sorts of accessors. More Pythonic code would look like this:
```python
@property
def name(self):
	return self.__name	

@name.setter
def name(self, name):
	self.__name = name
```
The `@property` string is a decorator that wraps these function calls in code that allows us to do this:
```python
my_object.name = "Foo"
print(my_object.name)
# which results in Foo being printed.
```
This is, of course, much cleaner than the accessor functions needed in the SystemVerilog UVM, and one could argue that these accessors should have been implemented in a more Pythonic way.  But, the goal here is to make `pyuvm` easy to use for existing UVM programmers, and changing basic elements of the specification would defeat that goal.
## Key base classes, SV vs Python
Much of the work of writing the UVM in Python is, as we saw above, writing simple functions that implement the specification. However there are some base classes which can take more advantage of Python’s capabilities.  This section shows how Python can make it easier to both write and use the UVM.
### The Factory
The SystemVerilog UVM’s implementation of the factory pattern is a heroic act of engineering akin to the Gilligan’s Island professor making a Geiger counter out of coconuts. Still it imposes some work on the programmer.
First there is the need to remember the ``\`uvm_*_utils`` macros.
```SystemVerilog
class my_component extends uvm_component;
`uvm_component_utils(my_component)
```
And then there is the creation incantation that allows a component to be overridden:
```SystemVerilog
    my_comp_h = my_component::type_id::create("my_comp_h",this);
```
This requires section 8.2.2 in the 1800.2’s *Factory classes* section which specifies a proxy type for all descendants of `uvm_object`:
```SystemVerilog
typedef my_component type_id
```
In addition there is a `uvm_component_registry` proxy class and other factory enabling tools. 
Here is how a user creates a component in `pyuvm`:
```python
class my_component(uvm_component):
...
```
`pyuvm` automatically adds any descendent of `uvm_void` to the factory.
We create a new object like this:
```python
my_comp_h = my_component.create("my_comp_h", self)
```
One can also sidestep the factory with a simple instantiation.
```python
my_comp_h = my_component("my_comp_h, self)
```
One can implement overrides using the `uvm_factory` singleton.
```python
factory = uvm_factory()
factory.set_type_override_by_type(my_component, overriding_component)
```
The factory also implements all the instance-based overrides.
### Implementing the Factory
The Python factory implementation takes advantage of the fact that the `class` statement is executed and not compiled.  This gives us an opportunity to control what it means to create a class object.
As we saw above, most types in Python are objects of type `type`.
```TeXt
type(int)
<class 'type'>
type(type)
<class 'type'>
```
We see that even the `type` class is an object of class `type`  But it is possible to make classes that are of a different type.  These are called *metatypes*. The `uvm_void` class is such a type:
```TeXt
type(uvm_void)
<class 'utility_classes.FactoryMeta'>
```
We specify this in its declaration:
```python
class uvm_void(metaclass=FactoryMeta):
    """
    5.2
    In pyuvm, we're using uvm_void() as a meteaclass so that all UVM classes can be stored in a factory.
	"""
```
This code means that the `uvm_void` class object and all class objects descended from it are of type `FactoryMeta`.  FactoryMeta registers all these classes with the factory:
```python
class FactoryMeta(type):
    """
    This is the metaclass that causes all uvm_void classes to register themselves
    """

    def __init__(cls, name, bases, clsdict):
        FactoryData().classes[cls.__name__] = cls
        super().__init__(name, bases, clsdict)

```
The code above says that when you execute a class statement to create a class object that extends `uvm_void`  that class object runs the above initialization code as is done with any other object.  Notice though that we have `cls` as the first variable rather than `self`. This is to remind us that we’re being passed a `class` object. (The name is otherwise meaningless.)
We store the class object in the `FactoryData`singleton’s associative array (`dict` in Python parlance) named `classes`.
The `FactoryMeta` class extends the `type` class, so we call `super().__init__` to ensure that all the work needed to set up a `type` gets done.
That is all there is to registering any `uvm_void` class with the factory.
The code above uses something I called a *singleton*. We’ll discuss singleton’s and their implementation below.
## The Dual-Top Testbench: The Proxy Approach
## A PyUVM example
# Conclusion
This approach literally provides the best of both worlds. Rather than reinventing the wheel, we build on all of the work that has gone in over the years to the development of the UVM, the most popular verification methodology in the industry, as well as existing constraint solvers and other capabilities provided by a simulator, but provide it to a new generation of engineers in a language with which they are already familiar.

[^1]:	[Wikipedia][1]

[^2]:	The \>\>\> in the examples is the prompt from the Python interpreter.  You see the interpreter when you type `python` on the command line.

[^3]:	[https://docs.python.org/3/library/exceptions.html#bltin-exceptions][2]

[1]:	https://en.wikipedia.org/wiki/C%2B%2B#History
[2]:	https://docs.python.org/3/library/exceptions.html#bltin-exceptions "Python Built-in Exceptions"