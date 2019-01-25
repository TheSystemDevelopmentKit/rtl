#RTL class 
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

class verilog_iofile(thesdk):
    def __init__(self,parent=None,**kwargs):
        if parent==None:
            self.print_log(type='F', msg="Parent of Verilog input file not given")
        try:  
            rndpart=os.path.basename(tempfile.mkstemp()[1])
            self.name=kwargs.get('name') 
            self.file=parent.vlogsimpath +'/' + self.name + '_' + rndpart +'.txt'
        except:
            self.print_log(type='F', msg="Verilog IO file definition failed")

        self.data=kwargs.get('data',[])
        self.simparam=kwargs.get('param','-g g_file_' + kwargs.get('name') + '=' + self.file)
        self.datatype=kwargs.get('datatype',int)
        self.dir=kwargs.get('dir','out')        #Files are output files by default, and direction is 
                                                # changed to 'in' when written 
        self.iotype=kwargs.get('iotype','data') # The file is a data file by default 
                                                # Option data,ctrl
        self.hasheader=kwargs.get('hasheader',False) # Headers False by default. 
                                                     # Do not generate things just to remove them in the next step
        if hasattr(parent,'preserve_iofiles'):
            self.preserve=parent.preserve_iofiles
        else:
            self.preserve=False

        #TODO: Needs a check to eliminate duplicate entries to iofiles
        if hasattr(parent,'iofiles'):
            self.print_log(type='O',msg="Attribute iofiles has been replaced by iofile_bundle")

        if hasattr(parent,'iofile_bundle'):
            parent.iofile_bundle.new(name=self.name,val=self)

    @property
    def verilog_stat(self):
        if not hasattr(self,'_verilog_stat'):
            self._verilog_stat='status_%s' %(self.name)
        return self._verilog_stat

    @verilog_stat.setter
    def verilog_stat(self,value):
        self._verilog_stat=value

    #Timestamp integers for control files
    @property
    def verilog_ctstamp(self):
        if not hasattr(self,'_verilog_ctstamp'):
            self._verilog_ctstamp='ctstamp_%s' %(self.name)
        return self._verilog_ctstamp
    @property
    def verilog_ptstamp(self):
        if not hasattr(self,'_verilog_ptstamp'):
            self._verilog_ptstamp='ptstamp_%s' %(self.name)
        return self._verilog_ptstamp
    @property
    def verilog_tdiff(self):
        if not hasattr(self,'_verilog_diff'):
            self._verilog_tdiff='tdiff_%s' %(self.name)
        return self._verilog_tdiff
    

    @property
    def verilog_statdef(self):
        if self.iotype=='data':
            self._verilog_statdef='integer %s, %s;\n' %(self.verilog_stat, self.verilog_fptr)
            print(self._verilog_statdef)
        elif self.iotype=='ctrl':
            self._verilog_statdef='integer %s, %s, %s, %s, %s;\n' %(self.verilog_stat, 
                    self.verilog_fptr, self.verilog_ctstamp, self.verilog_ptstamp, 
                    self.verilog_tdiff)
            for connector in self.verilog_connectors:
                self._verilog_statdef=self._verilog_statdef+'integer buffer_%s;\n' %(connector.name)
        return self._verilog_statdef

    @property
    def verilog_fptr(self):
        self._verilog_fptr='f_%s' %(self.name)
        return self._verilog_fptr
    
    @verilog_fptr.setter
    def verilog_fptr(self,value):
        self._verilog_fptr=value

    @property
    def verilog_fptrdef(self):
        self._verilog_fptrdef='integer %s;\n' %(self.verilog_fptr)
        return self._verilog_fptrdef

    @property
    def verilog_fopen(self):
        if self.dir=='in':
            self._verilog_fopen='initial %s = $fopen(g_file_%s,\"r\");\n' %(self.verilog_fptr,self.name)
        if self.dir=='out':
            self._verilog_fopen='initial %s = $fopen(g_file_%s,\"w\");\n' %(self.verilog_fptr,self.name)
        return self._verilog_fopen

    @property
    def verilog_fclose(self):
        self._verilog_fclose='$fclose(%s);\n' %(self.verilog_fptr)
        return self._verilog_fclose
    
    @property
    def verilog_connectors(self):
        if not hasattr(self,'_verilog_connectors'):
            self._verilog_connectors=[]
        return self._verilog_connectors

    @verilog_connectors.setter
    def verilog_connectors(self,value):
        #Ordered list.
        self._verilog_connectors=value
        

    @property 
    def verilog_io_condition(self):
        if not hasattr(self,'_verilog_io_condition'):
            first=True
            for connector in self.verilog_connectors:
                if first:
                    self._verilog_io_condition='~$isunknown(%s)' %(connector.name)
                    first=False
                else:
                    self._verilog_io_condition='%s \n&& ~$isunknown(%s)' %(self._verilog_io_condition,connector.name)
        return self._verilog_io_condition

    @verilog_io_condition.setter
    def verilog_io_condition(self,value):
        self._verilog_io_condition=value

    @property
    def verilog_io(self):
        first=True
        if self.iotype=='data':
            if self.dir=='out':
                self._verilog_io='%s = $fwrite(%s, ' %(self.verilog_stat, self.verilog_fptr)
            elif self.dir=='in':
                self._verilog_io='%s = $fscanf(%s, ' %(self.verilog_stat, self.verilog_fptr)
            for connector in self.verilog_connectors:
                if first:
                    iolines='    %s' %(connector.name)
                    format='\"%s' %(connector.ioformat)
                    first=False
                else:
                    iolines='%s,\n    %s' %(iolines,connector.name)
                    format='%s\\t%s' %(format,connector.ioformat)
            format=format+'\",\n'
            self._verilog_io=self._verilog_io+format+iolines+'\n);'
        elif self.iotype=='ctrl':
            print(self.name)
            if self.dir=='out':
                self.print_log(type='F', msg='Output writing for control files not supported')
            elif self.dir=='in':
                self._verilog_io='\nwhile(!$feof(%s)) begin\n    ' %(self.verilog_fptr)
                self._verilog_io=self._verilog_io+'%s = %s-%s;\n    #diff begin \n     ' %(self.verilog_tdiff,
                        self.verilog_ctstamp, self.verilog_ptstamp)    
                #Every conntrol file requires status, diff, current_timestamp and past timestamp
                self._verilog_io=self._verilog_io+'%s = %s;\n    ' %(self.verilog_ptstamp, self.verilog_ctstamp)
                for connector in self.verilog_connectors:
                    self._verilog_io=self._verilog_io+'%s = buffer_%s;\n    ' %(connector.name,connector.name)
                first=True            
                self._verilog_io=self._verilog_io+'%s = $fscanf(%s, ' %(self.verilog_stat,self.verilog_fptr)
            for connector in self.verilog_connectors:
                if first:
                    iolines='    buffer_%s' %(connector.name)
                    format='\"%s' %(connector.ioformat)
                    first=False
                else:
                    iolines='%s,\n    buffer_%s' %(iolines,connector.name)
                    format='%s\\t%s' %(format,connector.ioformat)
            format=format+'\",\n'
            self._verilog_io=self._verilog_io+format+iolines+'\n);\nend'
        return self._verilog_io

    @property
    def verilog_condio(self):
        first=True
        if self.dir=='out':
            self._verilog_io='$fwrite(%s, ' %(self.verilog_fptr)
        elif self.dir=='in':
            self._verilog_io='%s = $fscanf(%s, ' %(self.verilog_stat,self.verilog_fptr)
        for connector in self.verilog_connectors:
            if first:
                iolines='    %s' %(connector.name)
                format='\"%s' %(connector.ioformat)
                first=False
            else:
                iolines='%s,\n    %s' %(iolines,connector.name)
                format='%s\\t%s' %(format,connector.ioformat)
        format=format+'\",\n'
        self._verilog_io=self._verilog_io+format+iolines+'\n);'
        return self._verilog_io


    #default is the data file
    def write(self,**kwargs):
        self.dir='in'  # Only input files are written
        #Parse the rows to split complex numbers
        data=kwargs.get('data',self.data)
        datatype=kwargs.get('dtype',self.datatype)
        iotype=kwargs.get('iotype',self.iotype)
        header_line = []
        parsed=[]
        if iotype=='data':
            for i in range(data.shape[1]):
                if i==0:
                   if np.iscomplex(data[0,i]) or np.iscomplexobj(data[0,i]) :
                       parsed=np.r_['1',np.real(data[:,i]).reshape(-1,1),np.imag(data[:,i].reshape(-1,1))]
                       header_line.append('%s_%s_Real' %(self.name,i))
                       header_line.append('%s_%s_Imag' %(self.name,i))
                   else:
                       parsed=np.r_['1',data[:,i].reshape(-1,1)]
                       header_line.append('%s_%s' %(self.name,i))
                else:
                   if np.iscomplex(data[0,i]) or np.iscomplexobj(data[0,i]) :
                       parsed=np.r_['1',parsed,np.real(data[:,i]).reshape(-1,1),np.imag(data[:,i].reshape(-1,1))]
                       header_line.append('%s_%s_Real' %(self.name,i))
                       header_line.append('%s_%s_Imag' %(self.name,i))
                   else:
                       parsed=np.r_['1',parsed,data[:,i].reshape(-1,1)]
                       header_line.append('%s_%s' %(self.name,i))

            df=pd.DataFrame(parsed,dtype=datatype)
            if self.hasheader:
                df.to_csv(path_or_buf=self.file,sep="\t",index=False,header=header_line)
            else:
                df.to_csv(path_or_buf=self.file,sep="\t",index=False,header=False)
        elif iotype=='ctrl':
            for i in range(data.shape[1]):
                if i==0:
                   if np.iscomplex(data[0,i]) or np.iscomplexobj(data[0,i]) :
                       self.print_log(type='F', msg='Timestamp can not be complex.')
                   else:
                       parsed=np.r_['1',data[:,i].reshape(-1,1)]
                       header_line.append('Timestamp')
                else:
                   if np.iscomplex(data[0,i]) or np.iscomplexobj(data[0,i]) :
                       parsed=np.r_['1',parsed,np.real(data[:,i]).reshape(-1,1),np.imag(data[:,i].reshape(-1,1))]
                       header_line.append('%s_%s_Real' %(self.name,i))
                       header_line.append('%s_%s_Imag' %(self.name,i))
                   else:
                       parsed=np.r_['1',parsed,data[:,i].reshape(-1,1)]
                       header_line.append('%s_%s' %(self.name,i))

            df=pd.DataFrame(parsed,dtype=datatype)
            if self.hasheader:
                df.to_csv(path_or_buf=self.file,sep="\t",index=False,header=header_line)
            else:
                df.to_csv(path_or_buf=self.file,sep="\t",index=False,header=False)
        time.sleep(10)
        
    def read(self,**kwargs):
        fid=open(self.file,'r')
        datatype=kwargs.get('dtype',self.datatype)
        readd = pd.read_csv(fid,dtype=object,sep='\t',header=None)
        self.data=readd.values
        fid.close()

    def remove(self):
        if self.preserve:
            self.print_log(type="I", msg="Preserve_value is %s" %(self.preserve))
            self.print_log(type="I", msg="Preserving file %s" %(self.file))
        else:
            try:
                os.remove(self.file)
            except:
                pass

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
        self.print_log(type='I',msg='Command def_verilog() is obsoleted. It does nothing. \nWill be removed in future releases')

    @property
    def vlogcmd(self):
        submission=self.verilog_submission
        if not hasattr(self, '_vlogcmd'):
            vloglibcmd =  'vlib ' +  self.vlogworkpath + ' && sleep 2'
            vloglibmapcmd = 'vmap work ' + self.vlogworkpath
            vlogmodulesstring=' '.join([ self.vlogsrcpath + '/'+ str(param) for param in self.vlogmodulefiles])
            vlogcompcmd = ( 'vlog -work work ' + self.vlogsrc + ' ' +
                           + self.vlogtbsrc + ' ' + vlogmodulesstring )

            gstring=' '.join([ ('-g ' + str(param) +'='+ str(val)) for param,val in iter(self.vlogparameters.items()) ])

            fileparams=''
            for name, file in self.iofile_bundle.Members.items():
                fileparams=fileparams+' '+file.simparam

            if not self.interactive_verilog:
                vlogsimcmd = ( 'vsim -64 -batch -t 1ps -voptargs=+acc ' + fileparams + ' ' + gstring
                          +' work.tb_' + self.name  + ' -do "run -all; quit;"')
            else:
                submission="" #Local execution
                vlogsimcmd = ( 'vsim -64 -t 1ps -novopt ' + fileparams + ' ' + gstring
                          +' work.tb_' + self.name)

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

