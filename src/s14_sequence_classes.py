from s05_base_classes import uvm_transaction
# 14 Sequence Classes
#


class uvm_sequence_item(uvm_transaction):
    """
    14.1.1
    uvm_sequence_item class declaration
    """
    def __init__(self, name = "uvm_sequence_item"):
        """
        14.1.2.1
        Set new default name to match
        :param name:
        """
        super().__init__(name)
        self.__use_sequence_info = False # 14.1.2.3 says defaults to False

    def set_item_context(self, parent_seq, sequencer = None):
        """
        14.1.2.2
        Whereas Python would normally implement set/get with the @property
        decorator, we will implement these functions to match
        the specification
        :param parent_seq: Parent sequence
        :param sequencer: The sequence for this sequence
        :return:
        """
        # Protected variables
        self.__parent_seq = parent_seq
        self.__sequencer = sequencer

    def get_use_sequence_info(self):
        """
        14.1.2.3
        :return: boolean
        """
        return self.__use_sequence_info

    def set_use_sequence_info(self, value):
        """
        14.1.2.3
        :param value: bool
        :return: None
        """
        assert(isinstance(value, bool)), "use_sequence_info can only be set to True or False"
        self.__use_sequence_info = value




