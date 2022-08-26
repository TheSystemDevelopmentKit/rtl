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

    # These need to be converted to abstact properties
    def __init__(self):
        pass

    @property
    def preserve_rtlfiles(self):  
        """True | False (default)

        If True, do not delete testbench and copy of DUT after simulations. Useful for
        debugging testbench generation.
        
        """
        if not hasattr(self,'_preserve_rtlfiles'):
            self._preserve_rtlfiles=False
        return self._preserve_rtlfiles
    @preserve_rtlfiles.setter
    def preserve_rtlfiles(self,value):
        self._preserve_rtlfiles=value

    @property
    def interactive_rtl(self):
        """ True | False (default)
        
        Launch simulator in local machine with GUI."""

        if not hasattr(self,'_interactive_rtl'):
            self._interactive_rtl = False
        return self._interactive_rtl
    @interactive_rtl.setter
    def interactive_rtl(self,value):
        self._interactive_rtl=value
    
    @property 
    def verilog_submission(self):
        """
        Defines verilog submission prefix from thesdk.GLOBALS['LSFSUBMISSION']

        Usually something like 'bsub -K'
        """
        if not hasattr(self, '_verilog_submission'):
            if self.has_lsf:
                self._verilog_submission=thesdk.GLOBALS['LSFSUBMISSION']+' '
            else:
                self._verilog_submission=''
        return self._verilog_submission

    @property
    def rtl_timescale(self):
        """
        Defines the rtl timescale. Default '1ps'

        """
        if not hasattr(self, '_rtl_timescale'):
            self._rtl_timescale = '1ps'
        return self._rtl_timescale
    @rtl_timescale.setter
    def rtl_timescale(self,val):
            self._rtl_timescale = val

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
            -------
                self.entitypath/sv


        '''
        if not hasattr(self, '_vlogsrcpath'):
            self._vlogsrcpath  =  self.entitypath + '/sv'
        return self._vlogsrcpath
    #No setter, no deleter.

    @property
    def vlogsrc(self):
        '''Verilog source file
           self.vlogsrcpath/self.name.sv

           Returns
           -------
               self.vlogsrcpath + '/' + self.name + self.vlogext

        '''
        if not hasattr(self, '_vlogsrc'):
            #_classfile is an abstract property that must be defined in the class.
            self._vlogsrc=self.vlogsrcpath + '/' + self.name + self.vlogext
        return self._vlogsrc

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
    def vlogext(self):
        ''' File extension for verilog files

            Default is '.sv', but this can be overridden to support, e.g.
            generators like Chisel that always use the '.v' prefix.

        '''
        if not hasattr(self, '_vlogext'):
            self._vlogext = '.sv'
        return self._vlogext
    @vlogext.setter
    def vlogext(self, value):
        self._vlogext = value

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
    def rtlsimpath(self):
        '''HDL source directory for rtl simulations
           self.simpath + '/rtl'

           Returns
           -------
               self.simpath + '/rtl'
        '''
        if not hasattr(self, '_rtlsimpath'):
            self._rtlsimpath = os.path.join(self.simpath, 'rtl')
            try:
                if not os.path.exists(self._rtlsimpath):
                    self.print_log(type='I', msg='Creating %s' % self._rtlsimpath)
                    os.makedirs(self._rtlsimpath)
            except:
                self.print_log(type='E', msg='Failed to create %s' % self.rtlsimpath)
        return self._rtlsimpath

    def delete_rtlsimpath(self):
        ''' Deletes all files in rtlsimpath

        '''
        if os.path.exists(self.rtlsimpath):
            try:
                for target in os.listdir(self.rtlsimpath):
                    targetpath = '%s/%s' % (self.rtlsimpath,target)
                    if self.preserve_rtlfiles:
                        self.print_log(type='I',msg='Preserving %s' % targetpath)
                    else:
                        if os.path.isdir(targetpath):
                            shutil.rmtree(targetpath)
                        else:
                            os.remove(targetpath)
                        self.print_log(type='I',msg='Removing %s' % targetpath)
            except:
                self.print_log(type='W',msg='Could not remove %s' % targetpath)

            if not self.preserve_rtlfiles:
                try:
                    shutil.rmtree(self.rtlsimpath)
                    self.print_log(type='I',msg='Removing %s' % self.rtlsimpath)
                except:
                    self.print_log(type='W',msg='Could not remove %s' %self.rtlsimpath)

    @property
    def simdut(self):
        ''' Source file for Device Under Test in simulations directory

            Returns
            -------
                self.rtlsimpath + self.name + self.vlogext for 'sv' model
                self.rtlsimpath + self.name + '.vhd' for 'vhdl' model
        '''
        if not hasattr(self, '_simdut'):
            extension = None
            if self.model in ['sv', 'icarus']:
                extension = self.vlogext
            elif self.model == 'vhdl':
                extension = '.vhd'
            else:
                self.print_log(type='F', msg='Unsupported model %s' % self.model)
            self._simdut = os.path.join(self.rtlsimpath, self.name+extension)
        return self._simdut

    @property
    def simtb(self):
        ''' Verilog testbench source file in simulations directory

        '''
        if not hasattr(self, '_simtb'):
            #_classfile is an abstract property that must be defined in the class.
            self._simtb=self.rtlsimpath + '/tb_' + self.name + '.sv'
        return self._simtb

    @property
    def rtlworkpath(self):
        '''Work library directory for rtl compilations
           self.simpath +'/work'

           Returns
           -------
               self.simpath +'/work'

        '''
        if not hasattr(self, '_rtlworkpath'):
            self._rtlworkpath = self.simpath +'/work'
        return self._rtlworkpath

    def delete_rtlworkpath(self):
        ''' Deletes compilation directory
            Not a deleter decorator, because does not delete
            the property.

        '''
        if os.path.exists(self.rtlworkpath):
            try:
                shutil.rmtree(self.rtlworkpath)
                self.print_log(type='D',msg='Removing %s' % self.rtlworkpath)
            except:
                self.print_log(type='W',msg='Could not remove %s' %self.rtlworkpath)

    @property
    def rtlparameters(self): 
        '''Dictionary of parameters passed to the simulator 
        during the simulation invocation

        '''
        if not hasattr(self, '_rtlparameters'):
            self._rtlparameters = dict()
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
        '''List of VHDL entity files to be compiled in addition to DUT

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
        read from this file path. Default path is
        `./interactive_control_files/modelsim/dofile.do`.
        '''
        if self.model == 'icarus':
            dofiledir = '%s/interactive_control_files/gtkwave' % self.entitypath
            dofilepath = '%s/general.tcl' % dofiledir
            obsoletepath = '%s/Simulations/rtlsim/general.tcl' % self.entitypath
            newdofilepath = '%s/general.tcl' % self.simpath
        else:    
            dofiledir = '%s/interactive_control_files/modelsim' % self.entitypath
            dofilepath = '%s/dofile.do' % dofiledir
            obsoletepath = '%s/Simulations/rtlsim/dofile.do' % self.entitypath
            newdofilepath = '%s/dofile.do' % self.simpath
        if not os.path.exists(dofiledir):
            self.print_log(type='I',msg='Creating %s' % dofiledir)
            os.makedirs(dofiledir)
        # Property interactive_control_contents already given and new temporary
        # file not yet created -> create new file and use that
        if self.interactive_control_contents != '' and not os.path.isfile(newdofilepath):
            # Check if a custom file path was given
            if hasattr(self, '_interactive_controlfile'):
                dofilepath = self._interactive_controlfile
            # Give a warning if default/custom path contains a do-file already
            if os.path.isfile(dofilepath):
                self.print_log(type='W',msg='Interactive control file %s ignored and interactive_control_contents used instead.' % dofilepath)
            # Write interactive_control_contents to a temporary file
            self.print_log(type='I',msg='Writing interactive_control_contents to file %s' % newdofilepath)
            with open(newdofilepath,'w') as dofile:
                dofile.write(self.interactive_control_contents)
            self._interactive_controlfile = newdofilepath
        # No contents or path given -> use default path (or obsolete path)
        elif not hasattr(self, '_interactive_controlfile'):
            # Nag about obsolete stuff
            if os.path.exists(obsoletepath):
                self.print_log(type='O',msg='Found obsoleted do-file in %s' % obsoletepath)
                self.print_log(type='O',msg='To fix the obsolete warning:')
                self.print_log(type='O',msg='Move the obsoleted file %s to the default path %s' % (obsoletepath,dofilepath))
                self.print_log(type='O',msg='Or, set a custom do-file path to self.interactive_controlfile.')
                self.print_log(type='O',msg='Or, define the do-file contents in self.interactive_control_contents in your testbench.')
                self.print_log(type='O',msg='Using the obsoleted file for now.')
                self._interactive_controlfile = obsoletepath
            else:
                # Use default do-file location
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
        if self.model == 'icarus':
            os.mkdir(self.rtlworkpath)
        else:
            rtllibcmd =  'vlib ' +  self.rtlworkpath
            rtllibmapcmd = 'vmap work ' + self.rtlworkpath

        vlogmodulesstring=' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vlogmodulefiles])

        vhdlmodulesstring=' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vhdlentityfiles])

        if self.model=='sv':
            vlogcompcmd = ( 'vlog -sv -work work ' + vlogmodulesstring 
                    + ' ' + self.simdut + ' ' + self.simtb )
        elif self.model=='vhdl':
            vlogcompcmd = ( 'vlog -sv -work work ' + vlogmodulesstring 
                    + ' ' + self.simtb )
        elif self.model=='icarus':
            vlogcompcmd = ( 'iverilog -Wall -v -g2012 -o ' + self.rtlworkpath + '/' + self.name + vlogmodulesstring
    	            + ' ' + self.simdut + ' ' + self.simtb )

        vhdlcompcmd = ( 'vcom -work work ' + ' ' +
                       vhdlmodulesstring + ' ' + self.vhdlsrc )
        
        gstring=' '.join([ ('-g ' + str(param) +'='+ str(val)) 
            for param,val in iter(self.rtlparameters.items()) ])

        fileparams=''
        for name, file in self.iofile_bundle.Members.items():
            fileparams+=' '+file.simparam

        if not self.interactive_rtl:
            if self.model == 'icarus':
                rtlsimcmd = ('vvp -v ' + self.rtlworkpath + '/' + self.name + fileparams + ' ' + gstring)
            else:
                dostring=' -do "run -all; quit;"'
                rtlsimcmd = ( 'vsim -64 -batch -t ' + self.rtl_timescale + ' -voptargs=+acc ' 
                        + fileparams + ' ' + gstring
                        +' work.tb_' + self.name  
                        + dostring)
        else:
            dofile=self.interactive_controlfile
            if os.path.isfile(dofile):
                dostring=' -do "'+dofile+'"'
                self.print_log(type='I',msg='Using interactive control file %s' % dofile)
            else:
                dostring=''
                self.print_log(type='I',msg='No interactive control file set.')
            submission="" #Local execution
            if self.model == 'icarus':
                rtlsimcmd = ('vvp -v ' + self.rtlworkpath + '/' + self.name
                        + ' && gtkwave -S' + dofile + ' ' + self.name + '_dump.vcd')
            else:
                rtlsimcmd = ( 'vsim -64 -t ' + self.rtl_timescale + ' -novopt ' + fileparams 
                        + ' ' + gstring +' work.tb_' + self.name + dostring)

        if self.model=='sv':
            self._rtlcmd =  rtllibcmd  +\
                    ' && ' + rtllibmapcmd +\
                    ' && ' + vlogcompcmd +\
                    ' && sync ' + self.rtlworkpath +\
                    ' && ' + submission +\
                    rtlsimcmd
        elif self.model=='vhdl':
            self._rtlcmd =  rtllibcmd  +\
                    ' && ' + rtllibmapcmd +\
                    ' && ' + vhdlcompcmd +\
                    ' && ' + vlogcompcmd +\
                    ' && sync ' + self.rtlworkpath +\
                    ' && ' + submission +\
                    rtlsimcmd
        if self.model=='icarus':
            self._rtlcmd =  vlogcompcmd +\
                    ' && sync ' + self.rtlworkpath +\
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
        the bus is signed or not.
        Prior to writing output file, the type of the 
        connecting wire defines how the bus values are interpreted.

         '''
        for ioname,val in self.iofile_bundle.Members.items():
            if val.ionames:
                for assocname in val.ionames:
                    if val.dir is 'out':
                        if ((val.datatype is 'sint' ) or (val.datatype is 'scomplex')):
                            self.tb.connectors.Members[assocname].type='signed'
                    self.tb.connectors.Members[assocname].ioformat=val.ioformat
            else:
                self.print_log(type='F', 
                    msg='List of associated ionames not defined for IO %s\n. Provide it as list of strings' %(ioname))

    def copy_rtl_sources(self):
        ''' Copy rtl sources to self.rtlsimpath

        '''
        self.print_log(type='I', msg='Copying rtl sources to %s' % self.rtlsimpath)
        if self.model in ['sv', 'icarus']:
            # copy dut source
            vlogsrc_exists = os.path.isfile(self.vlogsrc)   # verilog source present in self.entitypath/sv
            simdut_exists = os.path.isfile(self.simdut)     # verilog source generated to self.rtlsimpath
            # if neither exist throw an fatal error (missing dut source)
            if not vlogsrc_exists and not simdut_exists:
                self.print_log(type='F', msg="Missing verilog source for 'sv' model at: %s" % self.vlogsrc)
            # vlogsrc exists, simdut doesn't exist => copy vlogsrc to simdut
            elif vlogsrc_exists and not simdut_exists:
                self.print_log(type='I', msg='Copying %s to %s' % (self.vlogsrc, self.simdut))
                shutil.copyfile(self.vlogsrc, self.simdut)
            # vlogsrc doesn't exist, simdut exists (externally generated) => use externally generated simdut
            elif not vlogsrc_exists and simdut_exists:
                self.print_log(type='I', msg='Using externally generated source for DUT: %s' % self.simdut)
            # if both sources are present throw a fatal error (multiple conflicting source files)
            else:
                self.print_log(type='W', msg="Both model 'sv' source %s and generated source %s exist. Using %s."
                        % (self.vlogsrc, self.simdut, self.simdut))

            # copy other verilog files
            for modfile in self.vlogmodulefiles:
                srcfile = os.path.join(self.vlogsrcpath, modfile)
                dstfile = os.path.join(self.rtlsimpath, modfile)
                if os.path.isfile(dstfile):
                    self.print_log(type='I', msg='Using externally generated source: %s' % modfile)
                else:
                    self.print_log(type='I', msg='Copying %s to %s' % (srcfile, dstfile))
                    shutil.copyfile(srcfile, dstfile)

        # nothing generates vhdl so simply copy all files to rtlsimpath
        elif self.model == 'vhdl':
            shutil.copy(self.vhdlsrc, self.rtlsimpath)
            for entfile in self.vhdlentityfiles:
                srcfile = os.path.join(self.vhdlsrcpath, entfile)
                dstfile = os.path.join(self.rtlsimpath, entfile)
                if os.path.isfile(dstfile):
                    self.print_log(type='I', msg='Using externally generated source: %s' % entfile)
                else:
                    self.print_log(type='I', msg='Copying %s to %s' % (srcfile, dstfile))
                    shutil.copyfile(srcfile, dstfile)

        # flush cached writes to disk
        output = subprocess.check_output("sync %s" % self.rtlsimpath, shell=True)
        output = output.decode('utf-8')
        if len(output) != 0:
            print(output)

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

        output = subprocess.check_output(self._rtlcmd, shell=True);
        self.print_log(type='I', msg='Simulator output:\n'+output.decode('utf-8'))

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
        '''1) Copies rtl sources to a temporary simulation directory
           2) Creates a testbench
           3) Defines the contens of the testbench
           4) Creates connectors
           5) Connects inputs
           6) Defines IO conditions
           7) Defines IO formats in testbench
           8) Generates testbench contents
           9) Exports the testbench to file
           10) Writes input files
           11) Executes the simulation
           12) Read outputfiles 
           13) Connects the outputs
           14) Cleans up the intermediate files

           You should overload this method while creating the simulation 
           and debugging the testbench.

        '''
        if self.load_state != '': 
            # Loading a previously stored state
            self._read_state()
        else:
            self.copy_rtl_sources()
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
            self.delete_iofile_bundle()
            self.delete_rtlworkpath()
            self.delete_rtlsimpath()


    #This writes all infile
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
        '''Connects the ouput data from files to corresponding output IOs

        '''
        for name, val in self.iofile_bundle.Members.items():
            if val.dir=='out':
                self.IOS.Members[name].Data=self.iofile_bundle.Members[name].Data
              
