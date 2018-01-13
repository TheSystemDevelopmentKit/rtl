# RTL class 
# Provides verilog-related properties and methods for other classes TheSDK
#
# Adding this class as a superclass enforces the definitions for verilog in the
# subclasses
##############################################################################
# Last modification by Marko Kosunen, marko.kosunen@aalto.fi, 12.01.2018 20:40
import os
import subprocess
import shlex
from thesdk import *

class verilog(thesdk):
    #Subclass of TheSDK for logging method
    #These need to be converted to abstact properties
    def __init__(self):
        self.model           =[]
        self.classfile       =[]
        self._vlogcmd        =[]
        self._name           =[]
        self._entitypath     =[] 
        self._vlogsrcpath    =[]
        self._vlogsimpath    =[]
        self._vlogworkpath   =[]
        self._vlogparameters =dict([])
        self._infile         =[]
        self._outfile        =[]
        #To define the verilog model and simulation paths

    def def_verilog(self): 
        self._name=os.path.splitext(os.path.basename(self._classfile))[0]
        self._entitypath= os.path.dirname(os.path.dirname(self._classfile))

        if (self.model is 'sv'):
            self._vlogsrcpath  =  self._entitypath + '/' + self.model 
            self._rtlsrcpath  =  self._entitypath + '/' + self.model 
        if not (os.path.exists(self._entitypath+'/Simulations')):
            os.mkdir(self._entitypath + '/Simulations')
        
        self._vlogsimpath  = self._entitypath +'/Simulations/verilogsim'

        if not (os.path.exists(self._vlogsimpath)):
            os.mkdir(self._vlogsimpath)
        self._vlogworkpath    =  self._vlogsimpath +'/work'

    def get_vlogcmd(self):
        #the could be gathered to verilog class in some way but they are now here for clarity
        submission = ' bsub -K '  
        vloglibcmd =  'vlib ' +  self._vlogworkpath + ' && sleep 2'
        vloglibmapcmd = 'vmap work ' + self._vlogworkpath
        if (self.model is 'sv'):
            vlogcompcmd = ( 'vlog -work work ' + self._vlogsrcpath + '/' + self._name + '.sv '
                           + self._vlogsrcpath + '/tb_' + self._name +'.sv')
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
        while not os.path.isfile(self._infile):
            self.print_log({'type':'I', 'msg':"Wait infile to appear"})
            time.sleep(5)
        try:
            os.remove(self._outfile)
        except:
            pass
        self.print_log({'type':'I', 'msg':"Running external command %s\n" %(self._vlogcmd) })
        subprocess.call(shlex.split(self._vlogcmd));
        
        while not os.path.isfile(self._outfile):
            self.print_log({'type':'I', 'msg':"Wait outfile to appear"})
            time.sleep(5)
        os.remove(self._infile)
        #This must be in every subclass file. Works also with __init__.py files
        #self._classfile=os.path.dirname(os.path.realpath(__file__)) + "/"+__name__


