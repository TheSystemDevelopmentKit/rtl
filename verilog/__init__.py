# RTL class 
# Provides verilog-related properties and methods for other classes TheSDK
#
# Adding this class as a superclass enforces the definitions for verilog in the
# subclasses
##############################################################################
# Last modification by Marko Kosunen, marko.kosunen@aalto.fi, 15.09.2018 19:34
import os
import sys
import subprocess
import shlex
from abc import * 
from thesdk import *
import numpy as np
import pandas as pd

class verilog_iofile(thesdk):
    def __init__(self,parent=None,**kwargs):
        if parent==None:
            self.print_log({'type':'F', 'msg':"Parent of Verilog input file not given"})
        try:  
            rndpart=os.path.basename(tempfile.mkstemp()[1])
            self.name=parent._vlogsimpath +'/' + kwargs.get('file') + '_' + rndpart +'.txt'
        except:
            self.print_log({'type':'F', 'msg':"Verilog IO file definition failed"})

        self.data=kwargs.get('data',[])
        self.simparam=kwargs.get('param','-g g_file_' + kwargs.get('file') + '=' + self.name)
        self.datatype=kwargs.get('datatype',int)
        self.preserve=parent.preserve_iofiles

    def write(self,**kwargs):
        #Parse the rows to split complex numbers
        data=kwargs.get('data',self.data)
        datatype=kwargs.get('dtype',self.datatype)
        parsed=[]
        for i in range(data.shape[1]):
            if i==0:
               if np.iscomplex(data[0,i]) or np.iscomplexobj(data[0,i]) :
                   parsed=np.r_['1',np.real(data[:,i]).reshape(-1,1),np.imag(data[:,i].reshape(-1,1))]
               else:
                   parsed=np.r_['1',data[:,i].reshape(-1,1)]
            else:
               if np.iscomplex(data[0,i]) or np.iscomplexobj(data[0,i]) :
                   parsed=np.r_['1',parsed,np.real(data[:,i]).reshape(-1,1),np.imag(data[:,i].reshape(-1,1))]
               else:
                   parsed=np.r_['1',data[:,i].reshape(-1,1)]
                   parsed=np.r_['1',parsed,data[:,i].reshape(-1,1)]

        df=pd.DataFrame(parsed,dtype=datatype)
        df.to_csv(path_or_buf=self.name,sep="\t",index=False,header=False)

    def read(self,**kwargs):
        fid=open(self.name,'r')
        datatype=kwargs.get('dtype',self.datatype)
        readd = pd.read_csv(fid,dtype=object,sep='\t')
        self.data=readd.values
        fid.close()

    def remove(self):
        try:
            os.remove(self._infile)
        except:
            pass



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

