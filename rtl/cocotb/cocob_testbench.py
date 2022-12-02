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
from rtl.connector import rtl_connector
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
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

    def define_testbench(self):
        '''Defines the tb connectivity, creates reset and clock, and initializes them to zero

        '''
        # Dut is creted automaticaly, if verilog file for it exists
        self.connectors.update(bundle=self.dut_instance.io_signals.Members)
        #Assign verilog simulation parameters to testbench
        self.parameters=self.parent.rtlparameters

        # Create clock if nonexistent and reset it
        if 'clock' not in self.dut_instance.ios.Members:
            self.connectors.Members['clock']=rtl_connector(lang='sv',
                    name='clock',cls='reg', init='\'b0')
        elif self.connectors.Members['clock'].init=='':
            self.connectors.Members['clock'].init='\'b0'

        # Create reset if nonexistent and reset it
        if 'reset' not in self.dut_instance.ios.Members:
            self.connectors.Members['reset']=rtl_connector(lang='sv',
                    name='reset',cls='reg', init='\'b0')
        elif self.connectors.Members['reset'].init=='':
            self.connectors.Members['reset'].init='\'b0'

        ## Start initializations
        #Init the signals connected to the dut input to zero
        for name, val in self.dut_instance.ios.Members.items():
            if val.cls=='input':
                val.connect.init='\'b0'

    @cocotb.test
    def entity_test(self, dut_entity):
        parameters = self.parameters.Members
        registers = self.connectors.Members
        print(parameters)
        print(registers)

        # Master clock must be present
        clock = dut_entity.clock
        print("POST COCOTB RUN")

