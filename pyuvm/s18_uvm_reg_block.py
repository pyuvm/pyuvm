from pyuvm import uvm_object


# 18.1.1 Class declaration
class uvm_reg_block(uvm_object):

    # 18.1.2.1
    # TODO Fix signature
    def __init__(self, name=""):
        super().__init__(name)
        self._regs = []

    # 18.1.3.7
    # TODO Fix signature
    def get_registers(self):
        return self._regs

    def _add_register(self, reg):
        self._regs.append(reg)