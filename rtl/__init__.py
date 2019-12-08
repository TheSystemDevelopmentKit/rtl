"""
=======
RTL
=======
Simulation interface package for The System Development Kit 

Provides utilities to import verilog modules and VHDL entities to 
python environment and sutomatically generate testbenches for the 
most common simulation cases.

Initially written by Marko Kosunen, 2017
"""
import os
import sys
import subprocess
import shlex
from abc import * 
from thesdk import *
import numpy as np
import pandas as pd
from functools import reduce

from rtl.connector import intend
from rtl.testbench import testbench as vtb
from rtl.rtl_iofile import rtl_iofile as rtl_iofile

class rtl(thesdk,metaclass=abc.ABCMeta):
    """Adding this class as a superclass enforces the definitions 
    for rtl simulations in the subclasses.
    
    """

    #These need to be converted to abstact properties
    def __init__(self):
        pass

    @property
    def preserve_iofiles(self):  
        """True | False (default)

        If True, do not delete file IO files after 
        simulations. Useful for debugging the file IO"""

        if hasattr(self,'_preserve_iofiles'):
            return self._preserve_iofiles
        else:
            self._preserve_iofiles=False
        return self._preserve_iofiles

    @preserve_iofiles.setter
    def preserve_iofiles(self,value):
        self._preserve_iofiles=value

    @property
    def interactive_rtl(self):
        """ True | False (default)
        
        Launch simulator in local machine with GUI."""

        if hasattr(self,'_interactive_rtl'):
            return self._interactive_rtl
        else:
            self._interactive_rtl=False
        return self._interactive_rtl

    @interactive_rtl.setter
    def interactive_rtl(self,value):
        self._interactive_rtl=value
    
    @property
    def iofile_bundle(self):
        """ 
        Property of type thesdk.Bundle.
        This property utilises iofile class to maintain list of IO-files
        that  are automatically handled by simulator specific commands
        when verilog.rtl_iofile.rtl_iofile(name='<filename>,...) is used to define an IO-file, created file object is automatically
        appended to this Bundle property as a member. Accessible with self.iofile_bundle.Members['<filename>']
        """
        if not hasattr(self,'_iofile_bundle'):
            self._iofile_bundle=Bundle()
        return self._iofile_bundle

    @iofile_bundle.setter
    def iofile_bundle(self,value):
        self._iofile_bundle=value

    @iofile_bundle.deleter
    def iofile_bundle(self):
        for name, val in self.iofile_bundle.Members.items():
            if val.preserve:
                self.print_log(type="I", msg="Preserve_value is %s" %(val.preserve))
                self.print_log(type="I", msg="Preserving file %s" %(val.file))
            else:
                val.remove()
        #self._iofile_bundle=None

    @property 
    def verilog_submission(self):
        """
        Defines verilog submioddion prefix from thesdk.GLOBALS['LSFSUBMISSION']

        Usually something like 'bsub -K'
        """
        if not hasattr(self, '_verilog_submission'):
            try:
                self._verilog_submission=thesdk.GLOBALS['LSFSUBMISSION']+' '
            except:
                self.print_log(type='W',msg='Variable thesdk.GLOBALS incorrectly defined. _verilog_submission defaults to empty string and simulation is ran in localhost.')
                self._verilog_submission=''

        if hasattr(self,'_interactive_rtl'):
            return self._verilog_submission

        return self._verilog_submission

    @property
    def name(self):
        if not hasattr(self, '_name'):
            #_classfile is an abstract property that must be defined in the class.
            self._name=os.path.splitext(os.path.basename(self._classfile))[0]
        return self._name
    #No setter, no deleter.

    #@property
    #def entitypath(self):
    #    if not hasattr(self, '_entitypath'):
    #        #_classfile is an abstract property that must be defined in the class.
    #        self._entitypath= os.path.dirname(os.path.dirname(self._classfile))
    #    return self._entitypath
    ##No setter, no deleter.

    @property
    def vlogsrcpath(self):
        if not hasattr(self, '_vlogsrcpath'):
            #_classfile is an abstract property that must be defined in the class.
            self._vlogsrcpath  =  self.entitypath + '/sv'
        return self._vlogsrcpath
    #No setter, no deleter.

    @property
    def vhdlsrcpath(self):
        if not hasattr(self, '_vhdlsrcpath'):
            #_classfile is an abstract property that must be defined in the class.
            self._vhdlsrcpath  =  self.entitypath + '/vhdl'
        return self._vhdlsrcpath

    @property
    def vlogsrc(self):
        if not hasattr(self, '_vlogsrc'):
            #_classfile is an abstract property that must be defined in the class.
            self._vlogsrc=self.vlogsrcpath + '/' + self.name + '.sv'
        return self._vlogsrc

    @property
    def vhdlsrc(self):
        if not hasattr(self, '_vhdlsrc'):
            #_classfile is an abstract property that must be defined in the class.
            self._vhdlsrc=self.vhdlsrcpath + '/' + self.name + '.vhd'
        return self._vhdlsrc

    @property
    def vlogtbsrc(self):
        if not hasattr(self, '_vlogtbsrc'):
            #_classfile is an abstract property that must be defined in the class.
            self._vlogtbsrc=self.vlogsrcpath + '/tb_' + self.name + '.sv'
        return self._vlogtbsrc

    #@property
    #def rtlsimpath(self):
    #    if not hasattr(self, '_rtlsimpath'):
    #        #_classfile is an abstract property that must be defined in the class.
    #        if not (os.path.exists(self.entitypath+'/Simulations')):
    #            os.mkdir(self.entitypath + '/Simulations')
    #    self._rtlsimpath  = self.entitypath +'/Simulations/rtlsim'
    #    if not (os.path.exists(self._rtlsimpath)):
    #        os.mkdir(self._rtlsimpath)
    #    return self._rtlsimpath
    ##No setter, no deleter.

    @property
    def rtlworkpath(self):
        if not hasattr(self, '_rtlworkpath'):
            self._rtlworkpath    =  self.simpath +'/work'
        return self._rtlworkpath

    @property
    def rtlparameters(self): 
        if not hasattr(self, '_rtlparameters'):
            self._rtlparameters =dict([])
        return self._rtlparameters
    @rtlparameters.setter
    def rtlparameters(self,value): 
            self._rtlparameters = value
    @rtlparameters.deleter
    def rtlparameters(self): 
            self._rtlparameters = None

    @property
    def vlogmodulefiles(self):
        if not hasattr(self, '_vlogmodulefiles'):
            self._vlogmodulefiles =list([])
        return self._vlogmodulefiles
    @vlogmodulefiles.setter
    def vlogmodulefiles(self,value): 
            self._vlogmodulefiles = value
    @vlogmodulefiles.deleter
    def vlogmodulefiles(self): 
            self._vlogmodulefiles = None 

    @property
    def vhdlentityfiles(self):
        if not hasattr(self, '_vlogmodulefiles'):
            self._vlogmodulefiles =list([])
        return self._vlogmodulefiles
    @vhdlentityfiles.setter
    def vhdlentityfiles(self,value): 
            self._vhdlentityfiles = value
    @vhdlentityfiles.deleter
    def vhdlentityfiles(self): 
            self._vhdlentityfiles = None 

    @property
    def rtlcmd(self):
        submission=self.verilog_submission
        rtllibcmd =  'vlib ' +  self.rtlworkpath + ' && sleep 2'
        rtllibmapcmd = 'vmap work ' + self.rtlworkpath

        vlogmodulesstring=' '.join([ self.vlogsrcpath + '/'+ 
            str(param) for param in self.vlogmodulefiles])

        vhdlmodulesstring=' '.join([ self.vlogsrcpath + '/'+ 
            str(param) for param in self.vhdlentityfiles])

        vlogcompcmd = ( 'vlog -sv -work work ' + self.vlogsrc + ' ' +
                       self.vlogtbsrc + ' ' + vlogmodulesstring )
        vhdlcompcmd = ( 'vcom -work work ' + self.vhdlsrc + ' ' +
                       vhdlmodulesstring )
        
        gstring=' '.join([ ('-g ' + str(param) +'='+ str(val)) 
            for param,val in iter(self.rtlparameters.items()) ])

        fileparams=''
        for name, file in self.iofile_bundle.Members.items():
            fileparams+=' '+file.simparam

        if not self.interactive_rtl:
            dostring=' -do "run -all; quit;"'
            rtlsimcmd = ( 'vsim -64 -batch -t 1ps -voptargs=+acc ' 
                    + fileparams + ' ' + gstring
                    +' work.tb_' + self.name  
                    + dostring)
        else:
            dofile=self.simpath+'/dofile.do'
            if os.path.isfile(dofile):
                dostring=' -do "'+dofile+'"'
            else:
                dostring=''
            submission="" #Local execution
            rtlsimcmd = ( 'vsim -64 -t 1ps -novopt ' + fileparams 
                    + ' ' + gstring +' work.tb_' + self.name + dostring)

        if self.model=='sv':
            self._rtlcmd =  rtllibcmd  +\
                    ' && ' + rtllibmapcmd +\
                    ' && ' + vlogcompcmd +\
                    ' && ' + submission +\
                    rtlsimcmd
        elif self.model=='vhdl':
            self._rtlcmd =  rtllibcmd  +\
                    ' && ' + rtllibmapcmd +\
                    ' && ' + vhdlcompcmd +\
                    ' && ' + vlogcompcmd +\
                    ' && ' + submission +\
                    rtlsimcmd

        return self._rtlcmd

    # Just to give the freedom to set this if needed
    @rtlcmd.setter
    def rtlcmd(self,value):
        self._rtlcmd=value
    @rtlcmd.deleter
    def rtlcmd(self):
        self._rtlcmd=None
    
    def create_connectors(self):
        # Create TB connectors from the control file
        # See controller.py
        for ioname,io in self.IOS.Members.items():
            # If input is a file, adopt it
            if isinstance(io.Data,rtl_iofile): 
                if io.Data.name is not ioname:
                    self.print_log(type='I', 
                            msg='Unifying file %s name to ioname %s' %(io.Data.name,ioname))
                    io.Data.name=ioname
                io.Data.adopt(parent=self)
                self.tb.parameters.Members.update(io.Data.rtlparam)

                for connector in io.Data.verilog_connectors:
                    self.tb.connectors.Members[connector.name]=connector
                    # Connect them to DUT
                    try: 
                        self.dut.ios.Members[connector.name].connect=connector
                    except:
                        pass
            # If input is not a file, look for corresponding file definition
            elif ioname in self.iofile_bundle.Members:
                val=self.iofile_bundle.Members[ioname]
                self.iofile_bundle.Members[ioname].verilog_connectors=\
                        self.tb.connectors.list(names=val.ionames)
                self.tb.parameters.Members.update(val.rtlparam)
        # Define the iofiles of the testbench. '
        # Needed for creating file io routines 
        self.tb.iofiles=self.iofile_bundle
               
    def connect_inputs(self):
        for ioname,io in self.IOS.Members.items():
            if ioname in self.iofile_bundle.Members:
                val=self.iofile_bundle.Members[ioname]
                # File type inputs are driven by the file.Data, not the input field
                if not isinstance(self.IOS.Members[val.name].Data,rtl_iofile) \
                        and val.dir is 'in':
                    # Data must be properly shaped
                    self.iofile_bundle.Members[ioname].Data=self.IOS.Members[ioname].Data

    # Define if the signals are signed or not
    # Can these be deducted?
    def format_ios(self):
        # Verilog module does not contain information if the bus is signed or not
        # Prior to writing output file, the type of the connecting wire defines
        # how the bus values are interpreted. 
        for ioname,val in self.iofile_bundle.Members.items():
            if val.dir is 'out' \
                    and ((val.datatype is 'sint' ) or (val.datatype is 'scomplex')):
                if val.ionames:
                    for assocname in val.ionames:
                        self.tb.connectors.Members[assocname].type='signed'
                        self.tb.connectors.Members[assocname].ioformat=val.ioformat
                else:
                    self.print_log(type='F', 
                        msg='List of associated ionames no defined for IO %s\n. Provide it as list of strings' %(ioname))
            elif val.dir is 'in':
                if val.ionames:
                    for assocname in val.ionames:
                        self.tb.connectors.Members[assocname].ioformat=val.ioformat
                else:
                    self.print_log(type='F', 
                        msg='List of associated ionames no defined for IO %s\n. Provide it as list of strings' %(ioname))


    def execute_rtl_sim(self):
        filetimeout=60 #File appearance timeout in seconds
        count=0
        files_ok=False
        while not files_ok:
            count +=1
            if count >5:
                self.print_log(type='F', msg='Verilog infile writing timeout')
            for name, file in self.iofile_bundle.Members.items(): 
                if file.dir=='in':
                    files_ok=True
                    files_ok=files_ok and os.path.isfile(file.file)
            time.sleep(int(filetimeout/5))

        #Remove existing output files before execution
        for name, file in self.iofile_bundle.Members.items(): 
            if file.dir=='out':
                try:
                    #Still keep the file in the infiles list
                    os.remove(file.name)
                except:
                    pass

        self.print_log(type='I', msg="Running external command %s\n" %(self.rtlcmd) )

        if self.interactive_rtl:
            self.print_log(type='I', msg="""
                Running RTL simulation in interactive mode.
                Add the probes in the simulation as you wish.
                To finish the simulation, run the simulation to end and exit.""")

        subprocess.check_output(self.rtlcmd, shell=True);

        count=0
        files_ok=False
        while not files_ok:
            count +=1
            if count >5:
                self.print_log(type='F', msg="Verilog outfile timeout")
            time.sleep(int(filetimeout/5))
            for name, file in self.iofile_bundle.Members.items(): 
                if file.dir=='out':
                    files_ok=True
                    files_ok=files_ok and os.path.isfile(file.file)
    
    def run_rtl(self):
        self.tb=vtb(self)             
        self.tb.define_testbench()    
        self.create_connectors()
        self.connect_inputs()         

        if hasattr(self,'define_io_conditions'):
            self.define_io_conditions()   # Local, this is dependent on how you
                                          # control the simulation
                                          # i.e. when you want to read an write your IO's
        self.format_ios()             
        self.tb.generate_contents() 
        self.tb.export(force=True)
        self.write_infile()           
        self.execute_rtl_sim()            
        self.read_outfile()           
        self.connect_outputs()         


    #This writes all infile
    def write_infile(self):
        for name, val in self.iofile_bundle.Members.items():
            if val.dir=='in':
                self.iofile_bundle.Members[name].write()
    
    #This reads all outfiles
    def read_outfile(self):
        for name, val in self.iofile_bundle.Members.items():
            if val.dir=='out':
                 self.iofile_bundle.Members[name].read()

    def connect_outputs(self):
        for name, val in self.iofile_bundle.Members.items():
            if val.dir=='out':
                self.IOS.Members[name].Data=self.iofile_bundle.Members[name].Data
              



