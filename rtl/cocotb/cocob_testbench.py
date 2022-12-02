"""
=========
Cocotb Testbench
=========

Cocotb Testbench utility module for TheSyDeKick. 

Initially written by Aleksi Korsman 20221202, aleksi.korsman@aalto.fi
"""
import os
import sys
import cocotb
from cocotb.clock import Clock
from cocotb.queue import Queue
from rtl.testbench_common import testbench_common
from thesdk import *

class cocotb_entity:
    """
    Translates cocotb sigals to TheSyDeKick IOS
    """

    def __init__(self, sdk_entity: thesdk, in_queue: Queue = None, out_queue: Queue = None):
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.entity = sdk_entity

    async def connect_ios(self):
        input_dict = Bundle()
        for key in self.entity.IOS.Members.keys():
            # Connect all IOS to cocotb signals
            # HOWTO: provide path for the signal?
            pass

    async def run(self):
        while True:
            new_inputs = await self.in_queue.get()
            self.entity.IOS.Members.update(new_inputs.Members)
            self.entity.run()
            await self.out_queue.put(self.entity.IOS.Members)

class cocotb_testbench(testbench_common):
    pass