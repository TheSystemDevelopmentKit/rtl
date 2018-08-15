# RTL class 
# Provides verilog-related properties and methods for other classes TheSDK
#
# Adding this class as a superclass enforces the definitions for verilog in the
# subclasses
##############################################################################
# Last modification by Marko Kosunen, marko.kosunen@aalto.fi, 15.09.2018 19:33
import os
import sys
if not (os.path.abspath('../../thesdk') in sys.path):
    sys.path.append(os.path.abspath('../../thesdk'))
import subprocess
import shlex
from abc import * 
from thesdk import *

class verilog(thesdk,metaclass=abc.ABCMeta):
    #These need to be converted to abstact properties
    def __init__(self):
        self.model           =[]
        self._vlogcmd        =[]
        self._name           =[]
        self._entitypath     =[] 
        self._vlogsrcpath    =[]
        self._vlogsimpath    =[]
        self._vlogworkpath   =[]
        self._vlogmodulefiles =list([])
        self._vlogparameters =dict([])
        self._infile         =[]
        self._outfile        =[]
    
    @property
    def preserve_iofiles(self):
        if hasattr(self,'_preserve_iofiles'):
            return self._preserve_iofiles
        else:
            return 'False'
    @preserve_iofiles.setter
    def preserve_iofiles(self,value):
        self._preserve_iofiles=value

    def def_verilog(self):
        if not hasattr(self, '_vlogparameters'):
            self._vlogparameters =dict([])
        if not hasattr(self, '_vlogmodulefiles'):
            self._vlogmodulefiles =list([])

        self._name=os.path.splitext(os.path.basename(self._classfile))[0]
        self._entitypath= os.path.dirname(os.path.dirname(self._classfile))

        if (self.model is 'sv'):
            self._vlogsrcpath  =  self._entitypath + '/' + self.model 
        if not (os.path.exists(self._entitypath+'/Simulations')):
            os.mkdir(self._entitypath + '/Simulations')
        
        self._vlogsimpath  = self._entitypath +'/Simulations/verilogsim'

        if not (os.path.exists(self._vlogsimpath)):
            os.mkdir(self._vlogsimpath)
        self._vlogworkpath    =  self._vlogsimpath +'/work'

    def get_vlogcmd(self):
        submission = ' bsub -K '  
        vloglibcmd =  'vlib ' +  self._vlogworkpath + ' && sleep 2'
        vloglibmapcmd = 'vmap work ' + self._vlogworkpath
        if (self.model is 'sv'):
            vlogmodulesstring=' '.join([ self._vlogsrcpath + '/'+ str(param) for param in self._vlogmodulefiles])
            vlogcompcmd = ( 'vlog -work work ' + self._vlogsrcpath + '/' + self._name + '.sv '
                           + self._vlogsrcpath + '/tb_' + self._name +'.sv' + ' ' + vlogmodulesstring )
            gstring=' '.join([ ('-g ' + str(param) +'='+ str(val)) for param,val in iter(self._vlogparameters.items()) ])
            vlogsimcmd = ( 'vsim -64 -batch -t 1ps -voptargs=+acc -g g_infile=' + self._infile
                          + ' -g g_outfile=' + self._outfile + ' ' + gstring 
                          +' work.tb_' + self._name  + ' -do "run -all; quit;"')

            
            vlogcmd =  submission + vloglibcmd  +  ' && ' + vloglibmapcmd + ' && ' + vlogcompcmd +  ' && ' + vlogsimcmd
        else:
            vlogcmd=[]
        return vlogcmd

    def run_verilog(self):
        self._vlogcmd=self.get_vlogcmd()
        filetimeout=30 #File appearance timeout in seconds
        count=0
        while not os.path.isfile(self._infile):
            count +=1
            if count >5:
                self.print_log({'type':'F', 'msg':"Verilog infile writing timeout"})
            time.sleep(int(filetimeout/5))
        try:
            if not self.preserve_iofiles:
                os.remove(self._outfile)
        except:
            pass
        self.print_log({'type':'I', 'msg':"Running external command %s\n" %(self._vlogcmd) })
        subprocess.check_output(shlex.split(self._vlogcmd));
        
        count=0
        while not os.path.isfile(self._outfile):
            count +=1
            if count >5:
                self.print_log({'type':'F', 'msg':"Verilog outfile timeout"})
            time.sleep(int(filetimeout/5))
        if not self.preserve_iofiles:
            os.remove(self._infile)


    #This must be in every subclass file. Works also with __init__.py files
    #@property
    #@abstractmethod
    #def _classfile(self):
    #    pass
    #    #return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

