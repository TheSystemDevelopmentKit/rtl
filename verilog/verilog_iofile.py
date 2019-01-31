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
    def vlogparam(self):
        if not hasattr(self,'_vlogparam'):
            key=re.sub(r"-g ",'',self.simparam).split('=')[0]
            val=re.sub(r"-g ",'',self.simparam).split('=')[1]
            self._vlogparam={key:'\"%s\"'%(val)}
        return self._vlogparam
    
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
        elif self.iotype=='ctrl':
            self._verilog_statdef='integer %s, %s, %s, %s, %s;\n' %(self.verilog_stat, 
                    self.verilog_fptr, self.verilog_ctstamp, self.verilog_ptstamp, 
                    self.verilog_tdiff)
            self._verilog_statdef+='initial %s=0;\n' %(self.verilog_ctstamp) 
            self._verilog_statdef+='initial %s=0;\n' %(self.verilog_ptstamp) 
            for connector in self.verilog_connectors:
                self._verilog_statdef+='integer buffer_%s;\n' %(connector.name)
        return self._verilog_statdef

    @property
    def verilog_fptr(self):
        self._verilog_fptr='f_%s' %(self.name)
        return self._verilog_fptr
    
    @verilog_fptr.setter
    def verilog_fptr(self,value):
        self._verilog_fptr=value

    @property
    def verilog_fopen(self):
        if self.dir=='in':
            self._verilog_fopen='initial %s = $fopen(%s,\"r\");\n' %(self.verilog_fptr,next(iter(self.vlogparam)))
        if self.dir=='out':
            self._verilog_fopen='initial %s = $fopen(%s,\"w\");\n' %(self.verilog_fptr,next(iter(self.vlogparam)))
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
    def verilog_io(self,**kwargs):
        first=True
        if self.iotype=='data':
            if self.dir=='out':
                self._verilog_io='$fwrite(%s, ' %(self.verilog_fptr)
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
            format=format+'\\n\",\n'
            self._verilog_io=self._verilog_io+format+iolines+'\n);'

        #Control files are handled differently
        elif self.iotype=='ctrl':
            if self.dir=='out':
                self.print_log(type='F', msg='Output writing for control files not supported')
            elif self.dir=='in':
                self._verilog_io='\nwhile(!$feof(%s)) begin\n    ' %(self.verilog_fptr)
                self._verilog_io+='%s = %s-%s;\n    #%s begin\n    ' %(self.verilog_tdiff,
                        self.verilog_ctstamp, self.verilog_ptstamp,self.verilog_tdiff)    
                #Every conntrol file requires status, diff, current_timestamp and past timestamp
                self._verilog_io+='    %s = %s;\n    ' %(self.verilog_ptstamp,
                        self.verilog_ctstamp)
                for connector in self.verilog_connectors:
                    self._verilog_io+='    %s = buffer_%s;\n    ' %(connector.name,connector.name)

                self._verilog_io+='    %s = $fscanf(%s, ' %(self.verilog_stat,self.verilog_fptr)

            iolines='            %s' %(self.verilog_ctstamp) #The first column is timestap
            format='\"%d'
            for connector in self.verilog_connectors:
                    iolines='%s,\n            buffer_%s' %(iolines,connector.name)
                    format='%s\\t%s' %(format,connector.ioformat)
            format=format+'\\n\",\n'
            self._verilog_io+=format+iolines+'\n        );\n    end\nend\n'
            #Repeat the last assignment outside the loop
            self._verilog_io+='%s = %s-%s;\n#%s begin\n' %(self.verilog_tdiff,
                    self.verilog_ctstamp, self.verilog_ptstamp,self.verilog_tdiff)    
            #Every conntrol file requires status, diff, current_timestamp and past timestamp
            self._verilog_io+='    %s = %s;\n' %(self.verilog_ptstamp,
                    self.verilog_ctstamp)
            for connector in self.verilog_connectors:
                self._verilog_io+='    %s = buffer_%s;\n' %(connector.name,connector.name)
            self._verilog_io+='end\n'
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
        format+='\",\n'
        self._verilog_io+=format+iolines+'\n);'
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
                       parsed=np.r_['1',np.real(data[:,i]).reshape(-1,1),
                               np.imag(data[:,i].reshape(-1,1))]
                       header_line.append('%s_%s_Real' %(self.name,i))
                       header_line.append('%s_%s_Imag' %(self.name,i))
                   else:
                       parsed=np.r_['1',data[:,i].reshape(-1,1)]
                       header_line.append('%s_%s' %(self.name,i))
                else:
                   if np.iscomplex(data[0,i]) or np.iscomplexobj(data[0,i]) :
                       parsed=np.r_['1',parsed,np.real(data[:,i]).reshape(-1,1),
                               np.imag(data[:,i].reshape(-1,1))]
                       header_line.append('%s_%s_Real' %(self.name,i))
                       header_line.append('%s_%s_Imag' %(self.name,i))
                   else:
                       parsed=np.r_['1',parsed,data[:,i].reshape(-1,1)]
                       header_line.append('%s_%s' %(self.name,i))

            df=pd.DataFrame(parsed,dtype=datatype)
            if self.hasheader:
                df.to_csv(path_or_buf=self.file,sep="\t",
                        index=False,header=header_line)
            else:
                df.to_csv(path_or_buf=self.file,sep="\t",
                        index=False,header=False)
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
                       parsed=np.r_['1',parsed,np.real(data[:,i]).reshape(-1,1),
                               np.imag(data[:,i].reshape(-1,1))]
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

