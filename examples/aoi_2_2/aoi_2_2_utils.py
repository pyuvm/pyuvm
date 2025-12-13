import logging

import cocotb
from cocotb.queue import Queue, QueueEmpty
from cocotb.triggers import Timer

from pyuvm import Singleton

logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def aoi_prediction(a, b, c, d, error=False):
    """
    Python model of the AOI_2_2 (AND-OR-INVERT) gate
    Logic: Y = ~((A & B) | (C & D))

    Args:
        a, b, c, d: Input bits (0 or 1)
        error: If True, invert the result to simulate errors

    Returns:
        Predicted output Y (0 or 1)
    """
    result = int(not ((a & b) | (c & d)))

    if error:
        result = 1 - result  # Invert for error injection

    return result


class AoiBfm(metaclass=Singleton):
    """
    Bus Functional Model for AOI_2_2 module
    Handles communication with the DUT (Device Under Test)
    """

    def __init__(self):
        self.dut = cocotb.top
        self.input_queue = Queue(maxsize=1)
        self.cmd_mon_queue = Queue(maxsize=0)
        self.result_mon_queue = Queue(maxsize=0)

    async def send_inputs(self, a, b, c, d):
        """
        Send input values to the DUT

        Args:
            a, b, c, d: Input bits (0 or 1)
        """
        input_tuple = (a, b, c, d)
        await self.input_queue.put(input_tuple)

    async def get_cmd(self):
        """Get monitored command (inputs) from the queue"""
        cmd = await self.cmd_mon_queue.get()
        return cmd

    async def get_result(self):
        """Get monitored result (output) from the queue"""
        result = await self.result_mon_queue.get()
        return result

    async def driver_bfm(self):
        """
        Driver BFM: Applies inputs to the DUT
        Runs continuously, waiting for items in the input queue
        """
        self.dut.SWT.value = 0

        while True:
            try:
                (a, b, c, d) = self.input_queue.get_nowait()

                # Combine inputs into 4-bit switch value: SWT[3:0] = {d, c, b, a}
                swt_value = (d << 3) | (c << 2) | (b << 1) | a
                self.dut.SWT.value = swt_value

                # Wait for combinational logic to settle
                await Timer(2, units="ns")

            except QueueEmpty:
                await Timer(1, units="ns")

    async def cmd_mon_bfm(self):
        """
        Command Monitor BFM: Monitors input changes and logs them
        """
        prev_swt = -1

        while True:
            await Timer(1, units="ns")
            current_swt = int(self.dut.SWT.value)

            if current_swt != prev_swt:
                # Extract individual bits
                a = current_swt & 0x1
                b = (current_swt >> 1) & 0x1
                c = (current_swt >> 2) & 0x1
                d = (current_swt >> 3) & 0x1

                cmd_tuple = (a, b, c, d)
                self.cmd_mon_queue.put_nowait(cmd_tuple)
                prev_swt = current_swt

    async def result_mon_bfm(self):
        """
        Result Monitor BFM: Monitors output from 7-segment display
        Decodes the 7-segment value to determine the output Y
        """
        prev_swt = -1

        while True:
            await Timer(1, units="ns")
            current_swt = int(self.dut.SWT.value)

            if current_swt != prev_swt:
                # Wait for output to settle
                await Timer(1, units="ns")

                # Decode 7-segment display to get Y value
                seg_value = int(self.dut.SEG.value)

                # SEG = 0b1000000 (0x40) means Y=0 (displaying '0')
                # SEG = 0b1111001 (0x79) means Y=1 (displaying '1')
                if seg_value in {64, 64}:
                    result = 0
                elif seg_value in {121, 121}:
                    result = 1
                else:
                    # Handle unexpected values
                    logger.warning(f"Unexpected 7-segment value: 0x{seg_value:02x}")
                    result = 0

                self.result_mon_queue.put_nowait(result)
                prev_swt = current_swt

    def start_bfm(self):
        """Start all BFM coroutines"""
        cocotb.start_soon(self.driver_bfm())
        cocotb.start_soon(self.cmd_mon_bfm())
        cocotb.start_soon(self.result_mon_bfm())
