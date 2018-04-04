'''
The UVM Specification has a detailed section on phasing, designed with the intention
of allowing users to define their own phases.

However, nobody writes user-defined phases, and in fact they are discouraged.

Therefore we are going to simply implement the standard UVM phases using a list and a simple
class that uses a string to call the correct function.
'''