import time


class Stim:
    def __init__(self, max, dut, bfm):
        self.max = max
        self.bfm = bfm

    def numb_gen_test(self):
        for ii in range(self.max):
            self.bfm.send_num(ii)
        time.sleep(5)
        self.bfm.done.set()
