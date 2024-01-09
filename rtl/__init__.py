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

from rtl.connector import indent, rtl_connector_bundle, verilog_connector_bundle
from rtl.testbench import testbench as vtb
from rtl.rtl_iofile import rtl_iofile as rtl_iofile
from rtl.sv.sv import sv as sv
from rtl.vhdl.vhdl import vhdl as vhdl
from rtl.icarus.icarus import icarus as icarus
from rtl.questasim.questasim import questasim as questasim
from rtl.ghdl.ghdl import ghdl as ghdl

class rtl(questasim,icarus,ghdl,vhdl,sv,thesdk,metaclass=abc.ABCMeta):
    """Adding this class as a superclass enforces the definitions
    for rtl simulations in the subclasses.

    """

    def __init__(self):
        pass

    @property
    def lang(self):
        """ str : Language of the testbench to support multilanguage simulators.
        Default vhdl | sv (default)
        """
        if not hasattr(self,'_lang'):
            self._lang = 'sv'
        if self.model == 'icarus' and self._lang != 'sv':
            self.print_log(t='I', msg='Only verilog supported by Icarus')
            self._lang = 'sv'
        elif self.model == 'ghdl' and self._lang != 'vhdl':
            self.print_log(t='I', msg='Only VHDL supported by GHDL')
            self._lang = 'vhdl'
        return self._lang
    @lang.setter
    def lang(self,value):
        self._lang = value

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
    def lsf_submission(self):
        """
        Defines submission prefix from thesdk.GLOBALS['LSFSUBMISSION'].
        [ ToDo ] Transfer definition to thesdk entity.

        Usually something like 'bsub -K'

        """
        if not hasattr(self, '_lsf_submission'):
            if self.has_lsf:
                self._lsf_submission=thesdk.GLOBALS['LSFSUBMISSION']+' '
            else:
                self._lsf_submission=''
        return self._lsf_submission

    @property
    def rtl_timescale(self):
        """
        Defines the rtl timescal. This is the time unit shown by the simulator
        and used in testbench delays. Default '1ps'

        """
        if not hasattr(self, '_rtl_timescale'):
            self._rtl_timescale = '1ps'
        return self._rtl_timescale
    @rtl_timescale.setter
    def rtl_timescale(self,val):
            self._rtl_timescale = val

    @property
    def rtl_timeunit(self):
        """
        Defines rtl time unit. OBSOLETE: use rtl_timescale.
        """
        if not hasattr(self, '_rtl_timeunit'):
            self.print_log(type='O', msg='Use `rtl_timescale` and `rtl_timeprecision` instead')
            self._rtl_timeunit = '1 ps'
        return self._rtl_timeunit
    @rtl_timeunit.setter
    def rtl_timeunit(self, val):
        self.print_log(type='O', msg='Use `rtl_timescale` and `rtl_timeprecision` instead')
        self._rtl_timeunit = val

    @property
    def rtl_timeprecision(self):
        """
        Defines rtl time precision. This is the smallest time step representable in simulation.
        This should be less than equal to ``rtl_timeunit``. Default '1 ps'. 

        """
        if not hasattr(self, '_rtl_timeprecision'):
            self._rtl_timeprecision = self.rtl_timescale
        return self._rtl_timeprecision
    @rtl_timeprecision.setter
    def rtl_timeprecision(self, val):
        self._rtl_timeprecision = val


    @property
    def add_tb_timescale(self):
        """Bool : Defines if timescale directive is added to testbench. Can
        be used in cases where submodules have timescale directives, and
        you wish to control that from the testbench toplevel. Effective only for 
        self.lang = 'sv'

        Default: False
        """
        if not hasattr(self,'_add_tb_timescale'):
            self._add_tb_timescale = False
        return self._add_tb_timescale
    @add_tb_timescale.setter
    def add_tb_timescale(self,val):
        self._add_tb_timescale = val
        
    @property
    def name(self):
        ''' Name of the entity
            Extracted from the _classfile attribute

        '''
        if not hasattr(self, '_name'):
            self._name=os.path.splitext(os.path.basename(self._classfile))[0]
        return self._name

    @property
    def rtlmisc(self):
        """List<String>

        List of manual commands to be pasted to the testbench. The strings are
        pasted to their own lines (no linebreaks needed), and the syntax is
        unchanged.

        Example: creating a custom clock::

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
            if self.model == 'icarus':
                self._simdut = self.icarus_simdut
            elif self.model == 'sv':
                self._simdut = self.questasim_simdut
            elif self.model == 'vhdl':
                self._simdut = self.questasim_simdut
            elif self.model == 'ghdl':
                self._simdut = self.ghdl_simdut
            else:
                self.print_log(type='F', msg='Unsupported model %s' % self.model)
        return self._simdut

    @property
    def simtb(self):
        ''' Testbench source file in simulations directory.

        This file and it's format is dependent on the language(s)
        supported by the simulator. Currently we have support only for verilog testbenches.

        '''
        if not hasattr(self, '_simtb'):
            if self.model == 'icarus':
                self._simtb = self.icarus_simtb
            elif self.model == 'sv' or self.model=='vhdl':
                self._simtb = self.questasim_simtb
            elif self.model == 'ghdl':
                self._simtb = self.ghdl_simtb
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
        during the simulation invocation.

        Example:
        {'name' : (type,value) }

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
    def vloglibfilemodules(self):
        '''List of verilog modules to be compiled in addition to DUT
        provided in a file given by the 'VLOGLIBFILE' global variable in TheSDK.config
        '''
        if not hasattr(self, '_vloglibfilemodules'):
            try:
                libfile = thesdk.GLOBALS['VLOGLIBFILE']
                if libfile == '':
                    raise ValueError
                else:
                    self._vloglibfilemodules = list()
                    if libfile == '':
                        self.print_log(type='W',msg='Global TheSDK variable VLOGLIBFILE not set.')
                    else:
                        self.print_log(type='I',msg='Using VLOGLIBFILE: %s' % libfile)
                        try:
                            with open(libfile, 'r') as fd:
                                modulefiles = [line.strip() for line in fd.readlines()]
                                self._vloglibfilemodules.extend(modulefiles)
                        except Exception as e:
                            self.print_log(type='F',msg='Could not read verilog module files from VLOGLIBFILE:\n\t%s' % e)
            except:
                 self._vloglibfilemodules = []
        return self._vloglibfilemodules
    @vloglibfilemodules.setter
    def vloglibfilemodules(self,value):
            self._vloglibfilemodules = value
    @vloglibfilemodules.deleter
    def vloglibfilemodules(self):
            self._vloglibfilemodules = None

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
    def vhdllibfileentities(self):
        '''List of VHDL entities to be compiled in addition to DUT
        provided in a file given by the 'VHDLLIBFILE' global variable in TheSDK.config
        '''
        if not hasattr(self, '_vhdllibfileentities'):
            try:
                libfile = thesdk.GLOBALS['VHDLLIBFILE']
                if libfile == '':
                    raise ValueError
                else:
                    self._vhdllibfileentities = list()
                    if libfile == '':
                        self.print_log(type='W',msg='Global TheSDK variable VHDLLIBFILE not set.')
                    else:
                        self.print_log(type='I',msg='Using VHDLLIBFILE: %s' % libfile)
                        try:
                            with open(libfile, 'r') as fd:
                                modulefiles = [line.strip() for line in fd.readlines()]
                                self._vhdllibfileentities.extend(modulefiles)
                        except Exception as e:
                            self.print_log(type='F',msg='Could not read verilog module files from VHDLLIBFILE:\n\t%s' % e)
            except:
                 self._vhdllibfileentities = []
        return self._vhdllibfileentities

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
    def simulator_control_contents(self):
        ''' Content of the simulator rtl control file.

        If this property is set, a new controlfile is written to the simulation
        path. This takes precedence over the file pointed by
        `simulator_controlfile`.

        For example, the contents can be defined in the top testbench as::

            self.simulator_control_contents="""
            # Path format for signals in entities :
            /top/sub/clock
            """

        '''
        if not hasattr(self, '_simulator_control_contents'):
            self._simulator_control_contents = ''
        return self._simulator_control_contents

    @simulator_control_contents.setter
    def simulator_control_contents(self,value):
        self._simulator_control_contents = value

    @property
    def simulator_controlfile(self):
        ''' Path to simulator control file.

        Different simulators use different ways to control the simulation. In simulators
        with integrated waveform viewer, there is only one control,file e.g 'dofile' and
        Questasim . Other option, for example used with GHDL is to control the simulator with
        '--read-wave-opt=<file>'. This property provides a method to set that filepath. It is mapped
        to an argument of a proper option with the simulator specific class.

        The content of the file can be defined in `simulator_control_contents`. If the
        content is not set in 'simulator_control_contents` -property, the control file
        read from this file path. Default is set in simulator specific property for each simulator.
        '''
        if self.model == 'icarus':
            (controlfiledir, controlfile, generatedcontrolfile ) = self.icarus_controlfilepaths
        elif self.model == 'sv':
            (controlfiledir, controlfile, generatedcontrolfile ) = self.questasim_controlfilepaths
        elif self.model == 'vhdl':
            (controlfiledir, controlfile, generatedcontrolfile ) = self.questasim_controlfilepaths
        elif self.model == 'ghdl':
            (controlfiledir, controlfile, generatedcontrolfile ) = self.ghdl_controlfilepaths
        else:
            self.print_log(type='F', msg='Unsupported model %s' % self.model)


        if not hasattr(self, '_simulator_controlfile'):
            if not os.path.exists(controlfiledir):
                self.print_log(type='I',msg='Creating %s' % controlfiledir)
                os.makedirs(controlfiledir)
            # Simulator control contents always overrdes the file 
            if self.simulator_control_contents != '':
                # Give a warning if default/custom path contains a do-file already
                if os.path.isfile(controlfile):
                    self.print_log(type='W',msg='Simulator control file %s ignored and simulator_control_contents used instead.' % controlfile)
                # Write simulator_control_contents to a temporary file
                self.print_log(type='I',msg='Writing simulator_control_contents to file %s' % generatedcontrolfile)
                with open(generatedcontrolfile,'w') as fileptr:
                    fileptr.write(self.simulator_control_contents)
                    self._simulator_controlfile = generatedcontrolfile
            # Use default control file location
            else:
                if os.path.isfile(controlfile):
                    self._simulator_controlfile = controlfile
                else:
                    self._simulator_controlfile = ''
        else:
            self._simulator_controlfile = controlfile
        return self._simulator_controlfile
    @simulator_controlfile.setter
    def simulator_controlfile(self,value):
        self._simulator_controlfile = value

    @property
    def interactive_controlfile(self):
        ''' Path to interactive rtl control file used in interactive simulations.

        The content of the file can be defined in `interactive_control_contents`. If the
        content is not set in `interactive_control` -property, the do-file is
        read from this file path. Default path is
        `./interactive_control_files/modelsim/dofile.do`.
        '''
        if self.model == 'icarus':
            (dofiledir, dofile, obsoletedofile, generateddofile) = self.icarus_dofilepaths
        elif self.model == 'sv':
            (dofiledir, dofile, obsoletedofile, generateddofile) = self.questasim_dofilepaths
        elif self.model == 'vhdl':
            (dofiledir, dofile, obsoletedofile, generateddofile) = self.questasim_dofilepaths
        elif self.model == 'ghdl':
            (dofiledir, dofile, obsoletedofile, generateddofile) = self.ghdl_dofilepaths
        else:
            self.print_log(type='F', msg='Unsupported model %s' % self.model)
        
        if not hasattr(self, '_interactive_controlfile'):
            # No contents or path given -> use default path (or obsolete path)
            if os.path.exists(obsoletedofile):
                self.print_log(type='O',msg='Found obsoleted do-file in %s' % obsoletedofile)
                self.print_log(type='O',msg='To fix the obsolete warning:')
                self.print_log(type='O',msg='Move the obsoleted file %s to the default path %s' % (obsoletedofile,dofile))
                self.print_log(type='O',msg='Or, set a custom do-file path to self.interactive_controlfile.')
                self.print_log(type='O',msg='Or, define the do-file contents in self.interactive_control_contents in your testbench.')
                self.print_log(type='O',msg='Using the obsoleted file for now.')
                self._interactive_controlfile = obsoletedofile
            else:
                # Use default do-file location if it exists
                if os.path.isfile(dofile):
                    self._interactive_controlfile = dofile

            if not os.path.exists(dofiledir):
                self.print_log(type='I',msg='Creating %s' % dofiledir)
                os.makedirs(dofiledir)
            # Property interactive_control_contents already given and new temporary
            # file not yet created -> create new file and use that
            if self.interactive_control_contents != '':
                # Give a warning if default/custom path contains a do-file already
                if os.path.isfile(dofile):
                    self.print_log(type='W',msg='Interactive control file %s ignored and interactive_control_contents used instead.' % dofile)
                # Write interactive_control_contents to a temporary file
                self.print_log(type='I',msg='Writing interactive_control_contents to file %s' % generateddofile)
                with open(generateddofile,'w') as dofileptr:
                    dofileptr.write(self.interactive_control_contents)
                    self._interactive_controlfile = generateddofile

            if not hasattr(self,'_interactive_controlfile'):
                    self._interactive_controlfile = ''

        return self._interactive_controlfile
    @interactive_controlfile.setter
    def interactive_controlfile(self,value):
        self._interactive_controlfile = value

    @property
    def rtlcmd(self):
        '''Command used for simulation invocation
           Compiled from various parameters. See source for details.

        '''
        if not hasattr(self, '_rtlcmd'):
            if self.model == 'icarus':
                return self.icarus_rtlcmd
            elif self.model=='sv':
                return self.questasim_rtlcmd
            elif self.model=='vhdl':
                return self.questasim_rtlcmd
            elif self.model=='ghdl':
                return self.ghdl_rtlcmd
            else:
                self.print_log(type='F', msg='Model %s not supported' %(self.model))
        return self._rtlcmd

    # Just to give the freedom to set this if needed
    @rtlcmd.setter
    def rtlcmd(self,value):
        self._rtlcmd=value
    @rtlcmd.deleter
    def rtlcmd(self):
        self._rtlcmd=None

    def create_connectors(self):
        '''Creates connector definitions from
           1) From a iofile that is provided in the Data
           attribute of an IO.
           2) IOS of the verilog DUT

        '''
        #currently only sv connectors are supported
        self.sv_create_connectors()

    def connect_inputs(self):
        '''Assigns all IOS.Members[name].Data to
           self.iofile_bundle.Members[ioname].Data

        '''
        for ioname,io in self.IOS.Members.items():
            if ioname in self.iofile_bundle.Members:
                val=self.iofile_bundle.Members[ioname]
                # File type inputs are driven by the file.Data, not the input field
                if not isinstance(self.IOS.Members[val.name].Data,rtl_iofile) \
                        and val.dir == 'in':
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
                    if val.dir == 'out':
                        if ((val.datatype == 'sint' ) or (val.datatype == 'scomplex')):
                            self.tb.connectors.Members[assocname].type='signed'
                    self.tb.connectors.Members[assocname].ioformat=val.ioformat
            else:
                self.print_log(type='F',
                    msg='List of associated ionames not defined for IO %s\n. Provide it as list of strings' %(ioname))

    def copy_or_relink(self,**kwargs):
        ''' If the source is a symlink, create the target as a link to original target.
        otherwise, copy the file.

        Parameters
        ----------
        src : str
            Path to source file
        dst : str
            Path to destination file.
        '''
        src=kwargs.get('src')
        dst=kwargs.get('dst')
        if os.path.islink(src):
            if not os.path.islink(dst):
                os.symlink(os.path.join(os.path.dirname(src), os.readlink(src)), dst)
            else:
                os.remove(dst)
                os.symlink(os.path.join(os.path.dirname(src), os.readlink(src)), dst)
        else:
            shutil.copyfile(src, dst, follow_symlinks=False)

    def copy_rtl_sources(self):
        ''' Copy rtl sources to self.rtlsimpath

        '''
        # I think these should not be model dependent MK
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
                self.copy_or_relink(src=self.vlogsrc,dst=self.simdut)
            # vlogsrc doesn't exist, simdut exists (externally generated) => use externally generated simdut
            elif not vlogsrc_exists and simdut_exists:
                self.print_log(type='I', msg='Using externally generated source for DUT: %s' % self.simdut)
            # if both sources are present throw a fatal error (multiple conflicting source files)
            else:
                self.print_log(type='W', msg="Both model 'sv' source %s and generated source %s exist. Using %s."
                        % (self.vlogsrc, self.simdut, self.simdut))

            # copy other verilog files
            for modfile in self.vlogmodulefiles+self.vloglibfilemodules:
                srcfile = os.path.join(self.vlogsrcpath, modfile)
                dstfile = os.path.join(self.rtlsimpath, modfile)
                if os.path.isfile(dstfile):
                    self.print_log(type='I', msg='Using externally generated source: %s' % modfile)
                else:
                    self.print_log(type='I', msg='Copying %s to %s' % (srcfile, dstfile))
                    self.copy_or_relink(src=srcfile,dst=dstfile)

            # copy additional VHDL files
            for entfile in self.vhdlentityfiles:
                srcfile = os.path.join(self.vhdlsrcpath, entfile)
                dstfile = os.path.join(self.rtlsimpath, entfile)
                if os.path.isfile(dstfile):
                    self.print_log(type='I', msg='Using externally generated source: %s' % entfile)
                else:
                    self.print_log(type='I', msg='Copying %s to %s' % (srcfile, dstfile))
                    self.copy_or_relink(src=srcfile,dst=dstfile)

        # nothing generates vhdl so simply copy all files to rtlsimpath
        elif self.model == 'vhdl' or self.model == 'ghdl':
            vhdlsrc_exists = os.path.isfile(self.vhdlsrc)   # verilog source present in self.entitypath/sv
            simdut_exists = os.path.isfile(self.simdut)     # verilog source generated to self.rtlsimpath

            if not vhdlsrc_exists and not simdut_exists:
                self.print_log(type='F', msg="Missing vhdl source for 'vhdl' model at: %s" % self.vlogsrc)
            # vhdlsrc exists, simdut doesn't exist => copy vhdlsrc to simdut
            elif vhdlsrc_exists and not simdut_exists:
                self.print_log(type='I', msg='Copying %s to %s' % (self.vhdlsrc, self.simdut))
                self.copy_or_relink(src=self.vhdlsrc,dst=self.simdut)
            # vhdlsrc doesn't exist, simdut exists (externally generated) => use externally generated simdut
            elif not vhdlsrc_exists and simdut_exists:
                self.print_log(type='I', msg='Using externally generated source for DUT: %s' % self.simdut)
            # if both sources are present throw a fatal error (multiple conflicting source files)
            else:
                self.print_log(type='W', msg="Both model 'sv' source %s and generated source %s exist. Using %s."
                        % (self.vhdlsrc, self.simdut, self.simdut))

            # copy other verilog files
            for modfile in self.vlogmodulefiles:
                srcfile = os.path.join(self.vlogsrcpath, modfile)
                dstfile = os.path.join(self.rtlsimpath, modfile)
                if os.path.isfile(dstfile):
                    self.print_log(type='I', msg='Using externally generated source: %s' % modfile)
                else:
                    self.print_log(type='I', msg='Copying %s to %s' % (srcfile, dstfile))
                    self.copy_or_relink(src=srcfile,dst=dstfile)

            # copy additional VHDL files
            for entfile in self.vhdlentityfiles:
                srcfile = os.path.join(self.vhdlsrcpath, entfile)
                dstfile = os.path.join(self.rtlsimpath, entfile)
                if os.path.isfile(dstfile):
                    self.print_log(type='I', msg='Using externally generated source: %s' % entfile)
                else:
                    self.print_log(type='I', msg='Copying %s to %s' % (srcfile, dstfile))
                    self.copy_or_relink(src=srcfile,dst=dstfile)

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


    @property
    def assignment_matchlist(self):
        '''List, which signals are connected in assignment stage during testbench generation
        Should be a list of strings, where a string is the signal name
        '''
        if not hasattr(self, '_assignment_matchlist'):
            self._assignment_matchlist = []
        return self._assignment_matchlist
    @assignment_matchlist.setter
    def assignment_matchlist(self, matchlist):
        self._assignment_matchlist = matchlist

    @property
    def custom_connectors(self):
        '''Custom connectors to be added to the testbench
        Should be a e.g. a rtl_connector_bundle
        '''
        if not hasattr(self, '_custom_connectors'):
            self._custom_connectors = rtl_connector_bundle()
        return self._custom_connectors
    @custom_connectors.setter
    def custom_connectors(self, bundle):
        self._custom_connectors = bundle

    def add_connectors(self):
        '''Adds custom connectors to the testbench.
        Also connects rtl matchlist to testbench matchlist.
        Custom connectors should be saved in self.custom_connectors
        Matchlist for these connectors should be saved in self.assignment_matchlist
        '''
        self.tb.connectors.update(bundle=self.custom_connectors.Members)
        self.tb.assignment_matchlist += self.assignment_matchlist

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
            self.tb=vtb(parent=self,lang=self.lang)
            self.tb.define_testbench()
            self.add_connectors()
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

