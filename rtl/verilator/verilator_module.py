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
        self._verilator_instance=self._verilator_instance+(';\n')
        return self._verilator_instance

    @property
    def definition(self):
        '''Verilator modules are defined through header file inclusion.

        '''
        if not hasattr(self,'_definition'):
            self._definition = '// Include verilated module headers of %s.\n' %(self.name) 
            self._definition += '#include V%s.h\n' %(self.name) 
            self._definition += "#include V%s___024unit.h\n" %(self.name)
        return self._definition


if __name__=="__main__":
    pass
