"""
Cocotb is a mixin class used to provide simulator specific
properties and methods for RTL class

Initially written by Aleksi Korsman 20221202
"""

from thesdk import *
import cocotb_test.simulator

class cocotb(thesdk,metaclass=abc.ABCMeta):
    
    def run_cocotb(self):

        verilog_sources = [self.simdut] + \
            [os.path.join(self.rtlsimpath, file) for file in self.vlogmodulefiles]
        vhdl_sources = \
            [os.path.join(self.rtlsimpath, file) for file in self.vhdlentityfiles]


        if self.model == 'sv':
            sim = 'questa'
        else:
            sim = 'icarus'

        os.environ["SIM"] = sim
        print("PRE COCOTB RUN")
        print(os.path.dirname(os.path.realpath(__file__)))
        # Run cocotb simulation
        # Running with Questa requires at least cocotb_test 0.2.2
        cocotb_test.simulator.run(
            verilog_sources=verilog_sources,
            vhdl_sources=vhdl_sources,
            work_dir=os.path.dirname(os.path.realpath(__file__)),
            toplevel=self.name,
            module="cocotb_testbench",
            toplevel_lang='verilog',
            force_compile=True,
            vhdl_compile_args=self.vhdlcompargs,
            verilog_compile_args=self.vlogcompargs,
            waves=True
        )