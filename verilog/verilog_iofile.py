# Verilog_iofile class 
# Provides verilog- file-io related properties and methods for TheSDK verilog
#
# Initially written by Marko Kosunen, marko.kosunen@aalto.fi, 
#                      Yue Dai, 
# 2018
##############################################################################
import os
import sys
from abc import * 
from thesdk import *
import numpy as np
import pandas as pd
from verilog.connector import intend

class verilog_iofile(thesdk):
    def __init__(self,parent=None,**kwargs):
        if parent==None:
            self.print_log(type='F', msg="Parent of Verilog input file not given")
        try:  
            self.parent=parent
            self.rndpart=os.path.basename(tempfile.mkstemp()[1])
            self.name=kwargs.get('name') 
            self.data=kwargs.get('data',np.array([]))
            self.paramname=kwargs.get('param','-g g_file_')
            self.datatype=kwargs.get('datatype',int)
            self.dir=kwargs.get('dir','out')             # Files are output files by default, 
                                                         # and direction is 
                                                         # changed to 'in' when written 

            self.iotype=kwargs.get('iotype','data')      # The file is a data file by default 
                                                         # Option data,ctrl

            self.hasheader=kwargs.get('hasheader',False) # Headers False by default. 
                                                         # Do not generate things just 
                                                         # to remove them in the next step
            if hasattr(self.parent,'preserve_iofiles'):
                self.preserve=parent.preserve_iofiles
            else:
                self.preserve=False
        except:
            self.print_log(type='F', msg="Verilog IO file definition failed")


        #TODO: Needs a check to eliminate duplicate entries to iofiles
        if hasattr(self.parent,'iofiles'):
            self.print_log(type='O',msg="Attribute iofiles has been replaced by iofile_bundle")

        if hasattr(self.parent,'iofile_bundle'):
            self.parent.iofile_bundle.new(name=self.name,val=self)

    # Parameters for the verilog testbench estracted from
    # Simulation parameters
    @property
    def file(self):
        self._file=self.parent.vlogsimpath +'/' + self.name \
                + '_' + self.rndpart +'.txt'
        return self._file

    @property
    def simparam(self):
        self._simparam=self.paramname \
            + self.name + '=' + self.file
        return self._simparam
    @property
    def vlogparam(self):
        if not hasattr(self,'_vlogparam'):
            key=re.sub(r"-g ",'',self.simparam).split('=')[0]
            val=re.sub(r"-g ",'',self.simparam).split('=')[1]
            self._vlogparam={key:'\"%s\"'%(val)}
        return self._vlogparam
    
    # Status parameter
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
    

    # Status integer verilog definitions
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

    # File pointer
    @property
    def verilog_fptr(self):
        self._verilog_fptr='f_%s' %(self.name)
        return self._verilog_fptr

    @verilog_fptr.setter
    def verilog_fptr(self,value):
        self._verilog_fptr=value

    # File opening, direction dependent 
    @property
    def verilog_fopen(self):
        if self.dir=='in':
            self._verilog_fopen='initial %s = $fopen(%s,\"r\");\n' %(self.verilog_fptr,next(iter(self.vlogparam)))
        if self.dir=='out':
            self._verilog_fopen='initial %s = $fopen(%s,\"w\");\n' %(self.verilog_fptr,next(iter(self.vlogparam)))
        return self._verilog_fopen

    # File close
    @property
    def verilog_fclose(self):
        self._verilog_fclose='$fclose(%s);\n' %(self.verilog_fptr)
        return self._verilog_fclose
    
    # List for verilog connectors.
    # These are the verilog signals/regs associated with this file
    @property
    def verilog_connectors(self):
        if not hasattr(self,'_verilog_connectors'):
            self._verilog_connectors=[]
        return self._verilog_connectors

    @verilog_connectors.setter
    def verilog_connectors(self,value):
        #Ordered list.
        self._verilog_connectors=value

    # Verilog_connectors is an ordered list Because order is important in file
    # IO. However, we need a mapping from name to value to assing data to 
    # correct columns of data. Less use for data files, more for controls
    def connector_datamap(self,**kwargs):
        name=kwargs.get('name')
        if not self._verilog_connectors:
            self.print_log(type='F', msg='Connector undefined, can\'t access.')
        else:
            if self.iotype=='data':
                self._verilog_connector_datamap=dict()
            elif self.iotype=='ctrl':
                self._verilog_connector_datamap={'time':0}
            index=0
            for val in self.verilog_connectors:
                index+=1
                self._verilog_connector_datamap.update({'%s' %(val.name): index})
        return self._verilog_connector_datamap[name]

    def set_control_data(self,**kwargs):
        time=kwargs.get('time',int(0))
        name=kwargs.get('name')
        val=kwargs.get('val')
        init=kwargs.get('init',int(0))
        
        # First, we initialize the data
        if self.data.shape[0] == 0:
            if np.isscalar(init):
                self.data=(np.ones((1,len(self._verilog_connectors)+1))*init).astype(int)
                self.data[0,0]=int(time)
            elif init.shape[1]==len(self._verilog_connectors)+1:
                self.data=init.astype(int)
        else: #Lets manipulate
            index=np.where(self.data[:,0]==time)[0]
            if index.size > 0:
                # Alter existing value onwards from given time
                self.data[index[-1]:,self.connector_datamap(name=name)]=int(val)
            else:
                # Find the previous time, duplicate the row and alter the value
                previndex=np.where(self.data[:,0]<time)[0][-1]
                self.data=np.r_['0', self.data[0:previndex+1,:], self.data[previndex::,:]]
                self.data[previndex+1,0]=time
                self.data[previndex+1,self.connector_datamap(name=name)]=val


    # Condition string for monitoring if the signals are unknown
    @property 
    def verilog_io_condition(self):
        if not hasattr(self,'_verilog_io_condition'):
            first=True
            for connector in self.verilog_connectors:
                if first:
                    self._verilog_io_condition='~$isunknown(%s)' %(connector.name)
                    first=False
                else:
                    self._verilog_io_condition='%s \n&& ~$isunknown(%s)' \
                            %(self._verilog_io_condition,connector.name)
        return self._verilog_io_condition

    @verilog_io_condition.setter
    def verilog_io_condition(self,value):
        self._verilog_io_condition=value

    # Write or read construct for file IO
    @property
    def verilog_io(self,**kwargs):
        first=True
        if self.iotype=='data':
            if self.dir=='out':
                self._verilog_io='$fwrite(%s, ' %(self.verilog_fptr)
            elif self.dir=='in':
                self._verilog_io='%s = $fscanf(%s, ' \
                        %(self.verilog_stat, self.verilog_fptr)
            for connector in self.verilog_connectors:
                if first:
                    iolines='    %s' %(connector.name)
                    format='\"%s' %(connector.ioformat)
                    first=False
                else:
                    iolines='%s,\n    %s' %(iolines,connector.name)
                    format='%s\\t%s' %(format,connector.ioformat)

            format=format+'\\n\",\n'
            self._verilog_io+=format+iolines+'\n);'

        #Control files are handled differently
        elif self.iotype=='ctrl':
            if self.dir=='out':
                self.print_log(type='F', msg='Output writing for control files not supported')
            elif self.dir=='in':
                self._verilog_io='\nwhile(!$feof(%s)) begin\n    ' \
                        %(self.verilog_fptr)
                self._verilog_io+='%s = %s-%s;\n    #%s begin\n    ' \
                        %(self.verilog_tdiff,
                        self.verilog_ctstamp, self.verilog_ptstamp,
                        self.verilog_tdiff)    

                # Every control file requires status, diff, current_timestamp 
                # and past timestamp
                self._verilog_io+='    %s = %s;\n    ' \
                        %(self.verilog_ptstamp, self.verilog_ctstamp)

                for connector in self.verilog_connectors:
                    self._verilog_io+='    %s = buffer_%s;\n    ' \
                            %(connector.name,connector.name)

                self._verilog_io+='    %s = $fscanf(%s, ' \
                        %(self.verilog_stat,self.verilog_fptr)

            #The first column is timestap
            iolines='            %s' %(self.verilog_ctstamp) 
            format='\"%d'
            for connector in self.verilog_connectors:
                iolines='%s,\n            buffer_%s' \
                        %(iolines,connector.name)
                format='%s\\t%s' %(format,connector.ioformat)
            format=format+'\\n\",\n'
            self._verilog_io+=format+iolines+'\n        );\n    end\nend\n'

            #Repeat the last assignment outside the loop
            self._verilog_io+='%s = %s-%s;\n#%s begin\n' %(self.verilog_tdiff,
                    self.verilog_ctstamp, self.verilog_ptstamp,self.verilog_tdiff)    
            self._verilog_io+='    %s = %s;\n' %(self.verilog_ptstamp,
                    self.verilog_ctstamp)
            for connector in self.verilog_connectors:
                self._verilog_io+='    %s = buffer_%s;\n' \
                %(connector.name,connector.name)
            self._verilog_io+='end\n'
        else:
            self.print_log(type='F', msg='Iotype not defined')
        return self._verilog_io

    # Relocate i.e. change parent. 
    # probably this could be automated
    # by using properties
    def adopt(self,parent=None,**kwargs):
        if parent==None:
            self.print_log(type='F', msg='Parent must be given for relocation')
        self.parent=parent
        if hasattr(self.parent,'iofile_bundle'):
            self.parent.iofile_bundle.new(name=self.name,val=self)

    # File writing
    def write(self,**kwargs):
        self.dir='in'  # Only input files are written
        #Parse the rows to split complex numbers
        data=kwargs.get('data',self.data)
        datatype=kwargs.get('datatype',self.datatype)
        iotype=kwargs.get('iotype',self.iotype)
        header_line = []
        parsed=[]

        # Default is the data file
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
        # Control file is a different thing
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
        # This is to compensate filesystem delays
        time.sleep(10)
        
    # Reading
    def read(self,**kwargs):
        fid=open(self.file,'r')
        self.datatype=kwargs.get('datatype',self.datatype)
        dtype=kwargs.get('dtype',object)
        readd = pd.read_csv(fid,dtype=dtype,sep='\t',header=None).astype('int')
        #read method for complex signal matrix
        if self.datatype=='complex':
            print("Reading complex")
            rows=int(readd.values.shape[0])
            cols=int(readd.values.shape[1]/2)
            for i in range(cols):
                if i==0:
                    self.data=np.zeros((rows, cols),dtype=complex)
                    self.data[:,i]=readd.values[:,2*i]+1j*readd.values[:,2*i+1]
                else:
                    self.data[:,i]=readd.values[:,2*i]+1j*readd.values[:,2*i+1]

        else:
            self.data=readd.values
        fid.close()

    # Remove the file when no longer needed
    def remove(self):
        if self.preserve:
            self.print_log(type="I", msg="Preserve_value is %s" %(self.preserve))
            self.print_log(type="I", msg="Preserving file %s" %(self.file))
        else:
            try:
                os.remove(self.file)
            except:
                pass


