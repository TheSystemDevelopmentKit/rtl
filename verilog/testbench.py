# Written by Marko Kosunen 20190108
import os
import sys
import subprocess
import shlex
from abc import * 
from thesdk import *
from verilog import *
from verilog.connector import verilog_connector
from verilog.connector import verilog_connector_bundle
from verilog.connector import intend 
from verilog.module import verilog_module
#from verilog.instance import verilog_instance

import numpy as np
import pandas as pd
from functools import reduce
import textwrap
## Some guidelines:
## DUT is parsed from the verilog file.
## Simparams are parsed to header from the parent
## All io's are read from a file? (Is this good)
## Code injection should be possible
## at least between blocks
## Default structure during initialization?

# Utilizes logging method from thesdk
# Is extendsd verilog module with some additional properties
class testbench(verilog_module):
    @property
    def _classfile(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

    def __init__(self, parent=None, **kwargs):
        if parent==None:
            self.print_log(type='F', msg="Parent of Verilog testbench not given")
        else:
            self.parent=parent
        try:  
            self.file=self.parent.vlogsrcpath + '/tb_' + self.parent.name + '_test.sv'
            self._dutfile=self.parent.vlogsrcpath + '/' + self.parent.name + '.sv'
        except:
            self.print_log(type='F', msg="Verilog Testbench file definition failed")
        
        #The methods for these are derived from verilog_module
        self._name=''
        self._parameters=Bundle()
        self.connectors=verilog_connector_bundle()
        self.iofiles=Bundle()
        self.content_parameters={'c_Ts': ('integer','1/(g_Rs*1e-12)')} # Dict of name: (type,value)
        

    @property
    def dut_instance(self):
        if not hasattr(self,'_dut_instance'):
            self._dut_instance=verilog_module(**{'file':self._dutfile})
        return self._dut_instance

    #We should not need this, but it is wise to enable override
    @dut_instance.setter
    def dut_instance(self,value):
        self._dut_instance=value
    
    @property
    def parameter_definitions(self):
        # Registers first
        definitions='//Parameter definitions\n'
        for name, val in self.content_parameters.items():
                definitions+='parameter '+ val[0]+' '+name+'='+ val[1]+';\n'
        return definitions
    
    @property
    def connector_definitions(self):
        # Registers first
        definitions='//Register definitions\n'
        for name, val in self.connectors.Members.items():
            if val.cls=='reg':
                definitions=definitions+val.definition

        definitions=definitions+'\n//Wire definitions\n'
        for name, val in self.connectors.Members.items():
            if val.cls=='wire':
                definitions=definitions+val.definition
        return definitions

    def assignments(self,**kwargs):
        matchlist=kwargs.get('matchlist',[])
        assigns='\n//Assignments\n'
        for match in matchlist:
            assigns=assigns+self.connectors.assign(match=match)
        return intend(text=assigns,level=kwargs.get('level',0))
     
    @property
    def iofile_definitions(self):
        iofile_defs='//Variables for the io_files\n'
        for name, val in self.iofiles.Members.items():
            iofile_defs=iofile_defs+val.verilog_statdef
            iofile_defs=iofile_defs+val.verilog_fopen
        iofile_defs=iofile_defs+'\n'
        return iofile_defs 

    @property
    def iofile_close(self):
        iofile_close='\n//Close the io_files\n'
        for name, val in self.iofiles.Members.items():
            iofile_close=iofile_close+val.verilog_fclose
        iofile_close=iofile_close+'\n'
        return iofile_close 

# This is the method to generate testbench contents. override if needed
    def generate_contents(self):
    # Start the testbench contents
        contents="""
//timescale 1ps this should probably be a global model parameter
"""+self.parameter_definitions+\
self.connector_definitions+\
self.iofile_definitions+\
"""

//DUT definition
"""+\
self.dut_instance.instance+\
"""

//Master clock is omnipresent
always #(c_Ts/2.0) clock = !clock;
//io_out
        """
        for key, member in self.iofiles.Members.items():
            if member.dir=='out':
                contents+=member.verilog_io
        contents+="""

//Execution with parallel fork-join and sequential begin-end sections
initial #0 begin
fork
""" + \
self.connectors.verilog_inits(level=1)+\
"""

    // Sequences enabled by initdone
    $display("Ready to read"); 
    """

        for key, member in self.iofiles.Members.items():
            if member.dir=='in':
                contents+=member.verilog_io

        contents+='\njoin\n'+self.iofile_close+'\n$finish;\nend\n'
        self.contents=contents

# This might be an overkill, but it makes it possible to have
# section attributes
#class section(thesdk):
#    def __init__(self,parent=None,**kwargs):
#        if parent==None:
#            self.print_log(type='F', msg="Parent of Verilog section not given")
#        self.name=kwargs.get('name')

if __name__=="__main__":
    pass
