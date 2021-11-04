"""
===========
RTL package
===========
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
import shutil

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
            self._preserve_iofiles = False
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
        ''' Name of the entity
            Extracted from the _classfile attribute

        '''
        if not hasattr(self, '_name'):
            #_classfile is an abstract property that must be defined in the class.
            self._name=os.path.splitext(os.path.basename(self._classfile))[0]
        return self._name
    @property
    def rtlmisc(self): 
        """List<String>

        List of manual commands to be pasted to the testbench. The strings are
        pasted to their own lines (no linebreaks needed), and the syntax is
        unchanged.

        Example: creating a custm clock::

            self.rtlmisc = []
            self.rtlmisc.append('reg clock2;')
            self.rtlmisc.append('initial clock2=\'b0;')
            self.rtlmisc.append('always #(c_Ts2/2.0) clock2 = !clock2;')
        """
        if not hasattr(self, '_rtlmisc'):
            self._rtlmisc = []
        return self._rtlmisc
    @rtlmisc.setter
    def rtlmisc(self,value): 
            self._rtlmisc = value

    @property
    def vlogsrcpath(self):
        ''' Search path for the verilogfiles
            self.entitypath/sv

            Returns
            _______
                self.entitypath/sv


        '''
        if not hasattr(self, '_vlogsrcpath'):
            #_classfile is an abstract property that must be defined in the class.
            self._vlogsrcpath  =  self.entitypath + '/sv'
        return self._vlogsrcpath
    #No setter, no deleter.

    @property
    def vhdlsrcpath(self):
        ''' VHDL search path
            self.entitypath/vhdl

            Returns
            -------
                self.entitypath/vhdl


        '''
        if not hasattr(self, '_vhdlsrcpath'):
            #_classfile is an abstract property that must be defined in the class.
            self._vhdlsrcpath  =  self.entitypath + '/vhdl'
        return self._vhdlsrcpath

    @property
    def vlogsrc(self):
        '''Verilog source file
           self.vlogsrcpath/self.name.sv'

           Returns
           -------
               self.vlogsrcpath + '/' + self.name + '.sv'

        '''
        if not hasattr(self, '_vlogsrc'):
            #_classfile is an abstract property that must be defined in the class.
            self._vlogsrc=self.vlogsrcpath + '/' + self.name + '.sv'
        return self._vlogsrc

    @property
    def vhdlsrc(self):
        '''VHDL source file
           self.vhdlsrcpath/self.name.sv'

           Returns
           -------
               self.vhdlsrcpath + '/' + self.name + '.vhd'

        '''
        if not hasattr(self, '_vhdlsrc'):
            #_classfile is an abstract property that must be defined in the class.
            self._vhdlsrc=self.vhdlsrcpath + '/' + self.name + '.vhd'
        return self._vhdlsrc

    @property
    def vlogtbsrc(self):
        '''Verilog testbench source file

        '''
        if not hasattr(self, '_vlogtbsrc'):
            #_classfile is an abstract property that must be defined in the class.
            self._vlogtbsrc=self.vlogsrcpath + '/tb_' + self.name + '.sv'
        return self._vlogtbsrc

    @property
    def rtlworkpath(self):
        '''Work library directory for rtl compilations
           self.simpath +'/work'

           Returns
           -------
               self.simpath +'/work'

        '''
        if not hasattr(self, '_rtlworkpath'):
            self._rtlworkpath    =  self.simpath +'/work'
        return self._rtlworkpath

    @property
    def rtlparameters(self): 
        '''Dictionary of parameters passed to the simulator 
        during the simulation invocation

        '''
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
        '''List of verilog modules to be compiled in addition of DUT

        '''
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
        '''List of VHDL entity files to be compiled in addiotion to DUT

        '''
        if not hasattr(self, '_vhdlentityfiles'):
            self._vhdlentityfiles =list([])
        return self._vhdlentityfiles
    @vhdlentityfiles.setter
    def vhdlentityfiles(self,value): 
            self._vhdlentityfiles = value
    @vhdlentityfiles.deleter
    def vhdlentityfiles(self): 
            self._vhdlentityfiles = None 

    @property
    def interactive_control_contents(self):
        ''' Content of the interactive rtl control file (.do -file).

        If this property is set, a new dofile gets written to the simulation
        path. This takes precedence over the file pointed by
        `interactive_controlfile`.

        For example, the contents can be defined in the top testbench as::

            self.interactive_control_contents="""
                add wave -position insertpoint \\
                sim/:tb_inverter:A \\
                sim/:tb_inverter:clock \\
                sim/:tb_inverter:Z
                run -all
                wave zoom full
            """
        
        '''
        if not hasattr(self, '_interactive_control_contents'):
            self._interactive_control_contents = ''
        return self._interactive_control_contents
    @interactive_control_contents.setter
    def interactive_control_contents(self,value): 
        self._interactive_control_contents = value

    @property
    def interactive_controlfile(self):
        ''' Path to interactive rtl control file (.do -file).

        The content of the file can be defined in `interactive_control`. If the
        content is not set in `interactive_control` -property, the do-file is
        read from this file path. Default path is `./dofile.do`.
        '''
        if not hasattr(self, '_interactive_controlfile'):
            obsoletepath = '%s/Simulations/rtlsim/dofile.do' % self.entitypath
            dofilepath = '%s/dofile.do' % self.entitypath
            if os.path.exists(obsoletepath):
                self.print_log(type='O',msg='Found obsoleted do-file in %s' % obsoletepath)
                self.print_log(type='O',msg='To fix the obsolete warning:')
                self.print_log(type='O',msg='Move the obsoleted file %s to the default path %s' % (obsoletepath,dofilepath))
                self.print_log(type='O',msg='Or, set a custom do-file path to self.interactive_controlfile.')
                self.print_log(type='O',msg='Or, define the do-file contents in self.interactive_control_contents in your testbench.')
                self.print_log(type='O',msg='Using the obsoleted file for now.')
                dofilepath = obsoletepath
            elif self.interactive_control_contents != '':
                dofilepath = '%s/dofile.do' % self.simpath
                self.print_log(type='I',msg='Writing interactive_control_contents to file %s' % dofilepath)
                with open(dofilepath,'w') as dofile:
                    dofile.write(self.interactive_control_contents)
            elif os.path.isfile(dofilepath):
                self.print_log(type='I',msg='Using existing control file %s' % dofilepath)
            self._interactive_controlfile = dofilepath
        return self._interactive_controlfile
    @interactive_controlfile.setter
    def interactive_controlfile(self,value): 
        self._interactive_controlfile = value

    @property
    def rtlcmd(self):
        '''Command used for simulation invocation
           Compiled from various parameters. See source for details.

        '''
        submission=self.verilog_submission
        rtllibcmd =  'vlib ' +  self.rtlworkpath + ' && sleep 2'
        rtllibmapcmd = 'vmap work ' + self.rtlworkpath

        vlogmodulesstring=' '.join([ self.vlogsrcpath + '/'+ 
            str(param) for param in self.vlogmodulefiles])

        vhdlmodulesstring=' '.join([ self.vhdlsrcpath + '/'+ 
            str(param) for param in self.vhdlentityfiles])

        if self.model=='sv':
            vlogcompcmd = ( 'vlog -sv -work work ' + vlogmodulesstring 
                    + ' ' + self.vlogsrc + ' ' + self.vlogtbsrc )
        elif self.model=='vhdl':
            vlogcompcmd = ( 'vlog -sv -work work ' + vlogmodulesstring 
                    + ' ' + self.vlogtbsrc )

        vhdlcompcmd = ( 'vcom -work work ' + ' ' +
                       vhdlmodulesstring + ' ' + self.vhdlsrc )
        
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
            dofile=self.interactive_controlfile
            if os.path.isfile(dofile):
                dostring=' -do "'+dofile+'"'
                self.print_log(type='D',msg='Using interactive control file %s' % dofile)
            else:
                dostring=''
                self.print_log(type='D',msg='No interactive control file set.')
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
        '''Cretes verilog connector definitions from 
           1) From a iofile that is provided in the Data 
           attribute of an IO.
           2) IOS of the verilog DUT

        '''
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
                for name in val.ionames:
                    # [TODO] Sanity check, only floating inputs make sense.
                    if not name in self.tb.connectors.Members.keys():
                        self.print_log(type='I', 
                                msg='Creating non-existent IO connector %s for testbench' %(name))
                        self.tb.connectors.new(name=name, cls='reg')
                self.iofile_bundle.Members[ioname].verilog_connectors=\
                        self.tb.connectors.list(names=val.ionames)
                self.tb.parameters.Members.update(val.rtlparam)
        # Define the iofiles of the testbench. '
        # Needed for creating file io routines 
        self.tb.iofiles=self.iofile_bundle
               
    def connect_inputs(self):
        '''Assigns all IOS.Members[name].Data to
           self.iofile_bundle.Members[ioname].Data

        '''
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
        '''Verilog module does not contain information if 
        the bus is signed or not
        Prior to writing output file, the type of the 
        connecting wire defines how the bus values are interpreted.

         '''
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
        '''Runs the rtl simulation in external simulator

        '''
        filetimeout=60 #File appearance timeout in seconds
        count=0
        files_ok=False
        while not files_ok:
            count +=1
            if count >filetimeout:
                self.print_log(type='F', msg='Verilog infile writing timeout')
            for name, file in self.iofile_bundle.Members.items(): 
                if file.dir=='in':
                    files_ok=True
                    files_ok=files_ok and os.path.isfile(file.file)
            time.sleep(int(1)) #Wait for one second

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

        subprocess.check_output(self._rtlcmd, shell=True);

        count=0
        files_ok=False
        while not files_ok:
            count +=1
            if count >filetimeout:
                self.print_log(type='F', msg="Verilog outfile timeout")
            time.sleep(int(1))
            for name, file in self.iofile_bundle.Members.items(): 
                if file.dir=='out':
                    files_ok=True
                    files_ok=files_ok and os.path.isfile(file.file)
    
    def run_rtl(self):
        '''1) Creates testbench
           2) Defines the contens of the testbench
           3) Creates connectors
           4) Connects inputs
           5) Defines IO conditions
           6) Defines IO formats in testbench
           7) Generates testbench contents
           8) Exports the testbench to file
           9) Writes input files
           10) Executes the simulation
           11) Read outputfiles 
           12) Connects the outputs

           You should overload this method while creating the simulation 
           and debugging the testbench.

        '''
        if self.load_state != '': 
            # Loading a previously stored state
            self._read_state()
        else:
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
            # Save entity state
            if self.save_state:
                self._write_state()
            # Clean simulation results
            if not self.preserve_iofiles:
                del(self.iofile_bundle)

    #This writes all infiles
    def write_infile(self):
        ''' Writes the input files

        '''
        for name, val in self.iofile_bundle.Members.items():
            if val.dir=='in':
                self.iofile_bundle.Members[name].write()
    
    #This reads all outfiles
    def read_outfile(self):
        '''Reads the oputput files

        '''
        for name, val in self.iofile_bundle.Members.items():
            if val.dir=='out':
                 self.iofile_bundle.Members[name].read()

    def connect_outputs(self):
        '''Connects the ouput data from files to corresponding 
        output IOs

        '''
        for name, val in self.iofile_bundle.Members.items():
            if val.dir=='out':
                self.IOS.Members[name].Data=self.iofile_bundle.Members[name].Data
              
