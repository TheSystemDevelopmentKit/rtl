"""
=========
Testbench
=========

Verilog testbench utility mmodule for TheSyDeKick. Contains attributes annd methods to import DUT as `verilog_module` 
instance, parse its IO and parameter definitions and construct a structured testbench with clock and file IO.

Utilizes logging method from thesdk.
Extendsd `verilog_module` with additional properties.

Initially written by Marko Kosunen 20190108, marko.kosunen@aalto.fi

"""
import os
import sys
import subprocess
import shlex
from abc import * 
from thesdk import *
from rtl import *
from rtl.connector import verilog_connector
from rtl.connector import verilog_connector_bundle
from rtl.connector import intend 
from rtl.module import verilog_module
from rtl.entity import vhdl_entity

import numpy as np
import pandas as pd
from functools import reduce
import textwrap
## Code injection should be possible
## at least between blocks
## Default structure during initialization?

class testbench(verilog_module):
    ''' Testbench class. Extends `verilog_module`

    '''

    @property
    def _classfile(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

    def __init__(self, parent=None, **kwargs):
        '''Parameters
           ----------
           parent: object, None (mandatory to define). TheSyDeKick parent entity object for this testbench.
           **kwargs :
              None

        '''

        if parent==None:
            self.print_log(type='F', msg="Parent of Verilog testbench not given")
        else:
            self.parent=parent
        try:  
            # The proper files are determined in rtl based on simulation model
            self._file = self.parent.simtb
            self._dutfile = self.parent.simdut
        except:
            self.print_log(type='F', msg="Verilog Testbench file definition failed")
        
        #The methods for these are derived from verilog_module
        self._name=''
        self._parameters=Bundle()
        self.connectors=verilog_connector_bundle()
        self.iofiles=Bundle()
        self.content_parameters={'c_Ts': ('integer','1/(g_Rs*1e-12)')} # Dict of name: (type,value)
        self.assignment_matchlist=[]
        
    @property
    def file(self):
        '''Path to the testbench file

        Default: `self.parent.vlogsrcpath + '/tb_' + self.parent.name + '.sv'`


        '''
        if not hasattr(self,'_file'):
            self._file=None
        return self._file

    @file.setter
    def file(self,value):
            self._file=value

    @property
    def dut_instance(self):
        '''RTL module parsed from the verilog or VHDL file of the parent depending on `parent.model`

        '''
        if not hasattr(self,'_dut_instance'):
            if self.parent.model in ['sv', 'icarus']:
                self._dut_instance=verilog_module(**{'file':self._dutfile})
            elif self.parent.model=='vhdl':
                self._dut_instance=vhdl_entity(**{'file':self._dutfile})
        return self._dut_instance

    
    #We should not need this, but it is wise to enable override
    @dut_instance.setter
    def dut_instance(self,value):
        self._dut_instance=value

    @property
    def verilog_instances(self):
        '''Verilog instances Bundle to be added to tesbench
        
        Todo 
        Need to handle VHDL instance too.

        '''
        if not hasattr(self,'_verilog_instances'):
            self._verilog_instances=Bundle()
        return self._verilog_instances

    def verilog_instance_add(self,**kwargs):
        '''Add verilog instance to the Bundle fro a file

        Parameters
        ----------
        **kwargs:
           name : str
             name of the module
           file :
               File defining the module

        '''
        # TODO: need to handle vhdl instances too
        name=kwargs.get('name')
        file=kwargs.get('file')
        self.verilog_instances.Members[name]=verilog_module(file=file,instname=name)
        # Addc connectors from the imported instance 
        self.connectors.update(bundle=self.verilog_instances.Members[name].io_signals.Members)
    
    @property
    def parameter_definitions(self):
        '''Parameter  and variable definition strins of the testbench

        '''
        definitions='//Parameter definitions\n'
        for name, val in self.content_parameters.items():
                definitions+='parameter '+ val[0]+' '+name+'='+ val[1]+';\n'
        return definitions
    
    @property
    def connector_definitions(self):
        '''Verilog register and wire definition strings

        '''
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
        '''Wire assingment strings

        '''
        matchlist=kwargs.get('matchlist',self.assignment_matchlist)
        assigns='\n//Assignments\n'
        for match in matchlist:
            assigns=assigns+self.connectors.assign(match=match)
        return intend(text=assigns,level=kwargs.get('level',0))
     
    @property
    def iofile_definitions(self):
        '''IOfile definition strings

        '''
        iofile_defs='//Variables for the io_files\n'
        for name, val in self.iofiles.Members.items():
            iofile_defs=iofile_defs+val.verilog_statdef
            iofile_defs=iofile_defs+val.verilog_fopen
        iofile_defs=iofile_defs+'\n'
        return iofile_defs 

    @property
    def clock_definition(self):
        '''Clock definition string

        Todo
        Create append mechanism to add more clocks.

        '''
        clockdef='//Master clock is omnipresent\nalways #(c_Ts/2.0) clock = !clock;'
        return clockdef

    @property
    def iofile_close(self):
        '''File close procedure for all IO files.

        '''
        iofile_close='\n//Close the io_files\n'
        for name, val in self.iofiles.Members.items():
            iofile_close=iofile_close+val.verilog_fclose
        iofile_close=iofile_close+'\n'
        return iofile_close 

    @property
    def misccmd(self):
        """String
        
        Miscellaneous command string corresponding to self.rtlmisc -list in
        the parent entity.
        """
        if not hasattr(self,'_misccmd'):
            self._misccmd="// Manual commands\n"
            mcmd = self.parent.rtlmisc
            for cmd in mcmd:
                self._misccmd += cmd + "\n"
        return self._misccmd
    
    @misccmd.setter
    def misccmd(self,value):
        self._misccmd=value
    @misccmd.deleter
    def misccmd(self,value):
        self._misccmd=None
   
    # This method 
    def define_testbench(self):
        '''Defines the tb connectivity, creates reset and clock, and initializes them to zero

        '''
        # Dut is creted automaticaly, if verilog file for it exists
        self.connectors.update(bundle=self.dut_instance.io_signals.Members)
        #Assign verilog simulation parameters to testbench
        self.parameters=self.parent.rtlparameters

        # Create clock if nonexistent and reset it
        if 'clock' not in self.dut_instance.ios.Members:
            self.connectors.Members['clock']=verilog_connector(
                    name='clock',cls='reg', init='\'b0')
        elif self.connectors.Members['clock'].init=='':
            self.connectors.Members['clock'].init='\'b0'

        # Create reset if nonexistent and reset it
        if 'reset' not in self.dut_instance.ios.Members:
            self.connectors.Members['reset']=verilog_connector(
                    name='reset',cls='reg', init='\'b0')
        elif self.connectors.Members['reset'].init=='':
            self.connectors.Members['reset'].init='\'b0'

        ## Start initializations
        #Init the signals connected to the dut input to zero
        for name, val in self.dut_instance.ios.Members.items():
            if val.cls=='input':
                val.connect.init='\'b0'
    
    # Automate this bsed in dir
    def connect_inputs(self):
        '''Define connections to DUT inputs.

        '''
        # Create TB connectors from the control file
        # See controller.py
        for ioname,val in self.parent.IOS.Members.items():
            if val.iotype is not 'file':
                self.parent.iofile_bundle.Members[ioname].verilog_connectors=\
                        self.connectors.list(names=val.ionames)
                if val.dir is 'in': 
                    # Data must be properly shaped
                    self.parent.iofile_bundle.Members[ioname].Data=self.parent.IOS.Members[ioname].Data
            elif val.iotype is 'file': #If the type is file, the Data is a bundle
                for bname,bval in val.Data.Members.items():
                    if val.dir is 'in': 
                        # Adoption transfers parenthood of the files to this instance
                        self.IOS.Members[ioname].Data.Members[bname].adopt(parent=self)
                    for connector in bval.verilog_connectors:
                        self.tb.connectors.Members[connector.name]=connector
                        # Connect them to DUT
                        try: 
                            self.dut.ios.Members[connector.name].connect=connector
                        except:
                            pass
        # Copy iofile simulation parameters to testbench
        for name, val in self.iofile_bundle.Members.items():
            self.tb.parameters.Members.update(val.rtlparam)
        # Define the iofiles of the testbench. '
        # Needed for creating file io routines 
        self.tb.iofiles=self.iofile_bundle

    def generate_contents(self):
        ''' This is the method to generate testbench contents. Override if needed
            Contents of the testbench is constructed from attributes in the 
            following order ::
            
                self.parameter_definitions
                self.connector_definitions
                self.assignments()
                self.iofile_definitions
                sefl.misccmd
                self.dut_instance.instance
                self.verilog_instance_members.items().instance (for all members)
                self.connectors.verilog_inits()
                self.iofiles.Members.items().verilog_io (for all members)
                self.iofile.close (for all members)

             Addtional code may be currently injected by appending desired 
             strings (Verilog sytax) to the relevant string attributes.

        '''
    # Start the testbench contents
        contents="""
//timescale 1ps this should probably be a global model parameter
"""+self.parameter_definitions+\
self.connector_definitions+\
self.assignments() +\
self.iofile_definitions+\
self.misccmd+\
"""
//DUT definition
"""+\
self.dut_instance.instance

        for inst, module in self.verilog_instances.Members.items():
            contents+=module.instance

        contents+=self.clock_definition
        contents+="""

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

if __name__=="__main__":
    pass
