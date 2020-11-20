from s05_base_classes import uvm_transaction
from s13_predefined_component_classes import uvm_component
import error_classes
# 14 Sequence Classes
#
# 14.1.1
# uvm_sequence_item class declaration
class uvm_sequence_item(uvm_transaction):
    """
    The base class for user-defined sequence items and also the base class for the
    uvm_sequence class.  Provides the base functionality for object, both
    sequence items and sequences to operate in the sequence mechanism
    """

    # 14.1.2 Common fields

    # 14.1.2.1 new (or init)
    def __init__(self, name = "uvm_sequence_item"):
        super().__init__(name)
        self.__use_sequence_info = False # 14.1.2.3 says defaults to False
        self.__sequence_id = None
        self.__sequencer = None
        self.__parent_sequence = None
        self.__depth = None
    # 14.1.2.2
    # Whereas Python would normally implement set/get with the @property
    # decorator, we will implement these functions to match
    # the specification
    # :param parent_seq: Parent sequence
    # :param sequencer: The sequence for this sequence
    # :return:
    def set_item_context(self, parent_seq, sequencer = None):
        """
        Specifies the sequence and sequencer execution context for this sequence item

        :param parent_seq: The parent sequence
        :param sequencer: The sequencer. Default is None
        """
        # Protected variables
        self.__parent_sequence = parent_seq
        self.__sequencer = sequencer

    # 14.1.2.3 get
    def get_use_sequence_info(self):
        """
        return the status of the use_sequence_info bit
        False unless set to True
        :return: True or False
        """
        return self.__use_sequence_info

    # 14.1.2.3
    def set_use_sequence_info(self, value):
        """
        Not implemented.  Always False for now.
        :param value: bool
        :return: None
        """
        raise error_classes.UVMNotImplemented("set_use_sequence_info Not implemented at this time. Always False.")

    # Not in the spec but needed

    def set_sequence_id(self, id):
        """
        Sets the sequence id for further reference. id is None if never called
        :param id: integer
        """
        self.__sequence_id = id

    def get_sequence_id(self):
        """
        Returns the current sequence id
        :return: id: None if it has never been set
        """
        return self.__sequence_id

    # 14.1.2.4
    def set_id_info(self, item):
        """
        Copies the interfase sequence id as well as the transaction id from the
        referenced item into the calling item.

        :param item: The item supplying the ids
        """
        assert (isinstance(item, uvm_sequence_item)), "set_id_info needs a sequence item"
        self.set_transaction_id(item.get_transaction_id())
        self.set_sequence_id(item.get_sequence_id())

    # 14.1.2.5
    def get_sequencer(self):
        """
        :return: A handle to the item's sequencer as set by set_sequencer
        """
        return self.__sequencer

    # 14.1.2.6
    # Notice that we don't check the type. This is because uvm_sequencer_base
    # gets defined in 15 and it would require some convolution to define it
    # before using it here.   We'll rely upon duck typing.
    def set_sequencer(self, sequencer):
        self.__sequencer = sequencer

    # 14.1.2.7
    def get_parent_sequence(self):
        """
        :return: The parent sequence
        """
        return self.__parent_sequence

    # 14.1.2.8
    def set_parent_sequence(self, parent):
        """
        Specifies the parent sequence of this item

        :param parent: uvm_sequence_base
        """
        self.__parent_sequence = parent

    # 14.1.2.9
    def get_depth(self):
        """
        Returns the value set by the most recent set_depth() call. Or, if set_depth has
        not been called, 1 + the number of recursive calls to get_parent_sequence without
        returning None.

        :return: depth of sequence
        """
        if self.__depth is not None:
            return self.__depth

        depth = 1
        parent = self.get_parent_sequence()
        while parent is not None:
            depth += 1
            parent = parent.get_parent_sequence()

    # 14.2.1.10
    def set_depth(self, depth):
        """
        The depth of any sequence is calculated automatically, however you can override
        that calculation by manually setting the depth with this method.

        :param depth: an integer
        """
        assert (isinstance(depth, int)), "Depth must be an integer."
        self.__depth = depth

    # 14.1.2.11
    def is_item(self):
        """
        Use isinstance(<seq>, uvm_sequence) to test for this. There is no need for this call
        """
        raise error_classes.UsePythonMethod ("Use isinstance(<seq>, uvm_sequence) instead of is_item()")

    # utility function
    # Since multiple methods want to use the list of sequences
    # well create a private utility that returns a list
    # that we can manipulate.

    def __get_sequence_path_list(self):
        path_list = [self]
        parent = self.get_parent_sequence()

        while parent is not None:
            parent = parent.get_parent_sequence()
            path_list.insert(0, parent)

        return path_list[1:] # Get rid of the None at [0].

    # 14.1.2.12
    def get_root_sequence_name(self):
        """
        Provides the name of the topmost parent sequence

        :return: Name of top parent sequence (str)
        """
        root_name = self.get_root_sequence().get_name()
        return root_name



    # 14.1.2.13
    def get_root_sequence(self):
        """
        Provides a reference to  root sequence (the top-most parent sequence)

        :return: root sequence
        """
        pl = self.__get_sequence_path_list()
        return pl[0]

    # 14.1.2.14
    def get_sequence_path(self):
        """
        Provides a string of names of each sequence in the full hierarchical path.
        A dot is used as the separator between each sequence.

        :return: sequence path
        """
        seq_list = self.__get_sequence_path_list()
        name_list = [seq.get_name() for seq in seq_list]
        path = ".".join(name_list)
        return path

