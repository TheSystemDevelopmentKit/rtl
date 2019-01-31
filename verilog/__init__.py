#Verilog class 
# Provides verilog-related properties and methods for other classes TheSDK
#
# Adding this class as a superclass enforces the definitions for verilog in the
# subclasses
##############################################################################
import os
import sys
import subprocess
import shlex
from abc import * 
from thesdk import *
import numpy as np
import pandas as pd
from functools import reduce
from verilog.connector import intend

from verilog.verilog_iofile import verilog_iofile as verilog_iofile

class verilog(thesdk,metaclass=abc.ABCMeta):
    #These need to be converted to abstact properties
    def __init__(self):
        self.model=[]

    @property
    @abstractmethod
    def _classfile(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__
    #This must be in every subclass file.
    #@property
    #def _classfile(self):
    #    return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

    @property
    def preserve_iofiles(self):
        if hasattr(self,'_preserve_iofiles'):
            return self._preserve_iofiles
        else:
            self._preserve_iofiles=False
        return self._preserve_iofiles

    @preserve_iofiles.setter
    def preserve_iofiles(self,value):
        self._preserve_iofiles=value

    @property
    def interactive_verilog(self):
        if hasattr(self,'_interactive_verilog'):
            return self._interactive_verilog
        else:
            self._interactive_verilog=False
        return self._interactive_verilog

    @interactive_verilog.setter
    def interactive_verilog(self,value):
        self._interactive_verilog=value
    
    # This property utilises vhdl_iofile class to maintain list of io-files
    # that  are automatically assigned to vhdlcmd
    @property
    def iofile_bundle(self):
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
        self._iofile_bundle=None

    @property 
    def verilog_submission(self):
        if not hasattr(self, '_verilog_submission'):
            try:
                self._verilog_submission=thesdk.GLOBALS['LSFSUBMISSION']+' '
            except:
                self.print_log(type='W',msg='Variable thesdk.GLOBALS incorrectly defined. _verilog_submission defaults to empty string and simulation is ran in localhost.')
                self._verilog_submission=''

        if hasattr(self,'_interactive_verilog'):
            return self._verilog_submission

        return self._verilog_submission

    @property
    def name(self):
        if not hasattr(self, '_name'):
            #_classfile is an abstract property that must be defined in the class.
            self._name=os.path.splitext(os.path.basename(self._classfile))[0]
        return self._name
    #No setter, no deleter.

    @property
    def entitypath(self):
        if not hasattr(self, '_entitypath'):
            #_classfile is an abstract property that must be defined in the class.
            self._entitypath= os.path.dirname(os.path.dirname(self._classfile))
        return self._entitypath
    #No setter, no deleter.

    @property
    def vlogsrcpath(self):
        if not hasattr(self, '_vlogsrcpath'):
            #_classfile is an abstract property that must be defined in the class.
            self._vlogsrcpath  =  self.entitypath + '/sv'
        return self._vlogsrcpath
    #No setter, no deleter.

    @property
    def vlogsrc(self):
        if not hasattr(self, '_vlogsrc'):
            #_classfile is an abstract property that must be defined in the class.
            self._vlogsrc=self.vlogsrcpath + '/' + self.name + '.sv'
        return self._vlogsrc
    @property
    def vlogtbsrc(self):
        if not hasattr(self, '_vlogtbsrc'):
            #_classfile is an abstract property that must be defined in the class.
            self._vlogtbsrc=self.vlogsrcpath + '/tb_' + self.name + '.sv'
        return self._vlogtbsrc

    @property
    def vlogsimpath(self):
        if not hasattr(self, '_vlogsimpath'):
            #_classfile is an abstract property that must be defined in the class.
            if not (os.path.exists(self.entitypath+'/Simulations')):
                os.mkdir(self.entitypath + '/Simulations')
        self._vlogsimpath  = self.entitypath +'/Simulations/verilogsim'
        if not (os.path.exists(self._vlogsimpath)):
            os.mkdir(self._vlogsimpath)
        return self._vlogsimpath
    #No setter, no deleter.

    @property
    def vlogworkpath(self):
        if not hasattr(self, '_vlogworkpath'):
            self._vlogworkpath    =  self.vlogsimpath +'/work'
        return self._vlogworkpath

    @property
    def vlogparameters(self): 
        if not hasattr(self, '_vlogparameters'):
            self._vlogparameters =dict([])
        return self._vlogparameters
    @vlogparameters.setter
    def vlogparameters(self,value): 
            self._vlogparameters = value
    @vlogparameters.deleter
    def vlogparameters(self): 
            self._vlogparameters = None

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

    #This is obsoleted
    def def_verilog(self):
        self.print_log(type='I', msg='Command def_verilog() is obsoleted. It does nothing. \nWill be removed in future releases')

    @property
    def vlogcmd(self):
        submission=self.verilog_submission
        if not hasattr(self, '_vlogcmd'):
            vloglibcmd =  'vlib ' +  self.vlogworkpath + ' && sleep 2'
            vloglibmapcmd = 'vmap work ' + self.vlogworkpath
            vlogmodulesstring=' '.join([ self.vlogsrcpath + '/'+ 
                str(param) for param in self.vlogmodulefiles])
            print(self.vlogsrc)
            print(self.vlogtbsrc)
            vlogcompcmd = ( 'vlog -work work ' + self.vlogsrc + ' ' +
                           self.vlogtbsrc + ' ' + vlogmodulesstring )
            
            gstring=' '.join([ ('-g ' + str(param) +'='+ str(val)) 
                for param,val in iter(self.vlogparameters.items()) ])

            fileparams=''
            for name, file in self.iofile_bundle.Members.items():
                fileparams+=' '+file.simparam

            if not self.interactive_verilog:
                vlogsimcmd = ( 'vsim -64 -batch -t 1ps -voptargs=+acc ' 
                        + fileparams + ' ' + gstring
                        +' work.tb_' + self.name  
                        + ' -do "run -all; quit;"')
            else:
                submission="" #Local execution
                vlogsimcmd = ( 'vsim -64 -t 1ps -novopt ' + fileparams 
                        + ' ' + gstring +' work.tb_' + self.name)

            self._vlogcmd =  vloglibcmd  +  ' && ' + vloglibmapcmd + ' && ' + vlogcompcmd +  ' && ' + submission + vlogsimcmd
        return self._vlogcmd
    # Just to give the freedom to set this if needed
    @vlogcmd.setter
    def vlogcmd(self,value):
        self._vlogcmd=value
    @vlogcmd.deleter
    def vlogcmd(self):
        self._vlogcmd=None

    def run_verilog(self):
        filetimeout=60 #File appearance timeout in seconds
        count=0
        files_ok=False
        while not files_ok:
            count +=1
            if count >5:
                self.print_log(type='F', msg="Verilog infile writing timeout")
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

        self.print_log(type='I', msg="Running external command %s\n" %(self.vlogcmd) )

        if self.interactive_verilog:
            self.print_log(type='I', msg="""Running verilog simulation in interactive mode.
                Add the probes in the simulation as you wish.
                To finish the simulation, run the simulation to end and exit.""")

        subprocess.check_output(self.vlogcmd, shell=True);

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

        #for name, file in self.iofile_bundle.Members.items(): 
        #    if file.dir=='in':
        #        try:
        #            file.remove()
        #        except:
        #            pass

