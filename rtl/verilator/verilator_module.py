"""
================
Verilator_module
================
This module handles verilog import as verilog_module does, but has additional definition for instance 


"""
import os
from thesdk import *
from rtl import *
from copy import deepcopy
from rtl.connector import *
from rtl.sv.verilog_module import verilog_module
from rtl.sv.verilog_module import verilog_module

class verilator_module(verilog_module):
    @property
    def verilator_instance(self):
        '''Instantiation string of the module/entity for use inside of verilator testbenches.

        '''
        self._verilator_instance='V'+self.name+'* top = new V'+self.name+'(contextp);'
        self._verilator_instance=self._vhdl_instance+(';\n')
        return self._verilator_instance



if __name__=="__main__":
    pass
