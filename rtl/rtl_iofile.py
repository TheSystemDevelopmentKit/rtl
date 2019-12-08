"""
======================
Verilog_iofile package 
======================

Provides verilog- file-io related attributes and methods 
for TheSDK verilog

Initially written by Marko Kosunen, marko.kosunen@aalto.fi,
Yue Dai, 2018

"""
import os
import sys
from abc import * 
from thesdk import *
from thesdk.iofile import iofile
import numpy as np
import pandas as pd
from rtl.connector import intend

class rtl_iofile(iofile):
    """
    Class to provide file IO for verilog simulations. When created, 
    adds a rtl_iofile object to the parents iofile_bundle attribute.
    Accessible as iofile_bundle.Members['name'].

    Example
    -------
    Initiated in parent as: 
        _=rtl_iofile(self,name='foobar')
    
    Parameters
    -----------
    parent : object 
        The parent object initializing the 
        rtl_iofile instance. Default None
    
    **kwargs :  
            name : str  
                Name of the file. Appended with 
                random string during the simulation.
            param : str,  -g g_file
                The string defining the testbench parameter to be be 
                passed to the simulator at command line.
    """
    def __init__(self,parent=None,**kwargs):
        #This is a redundant check, but doens not hurt.to have it here too.
        if parent==None:
            self.print_log(type='F', msg="Parent of Verilog input file not given")
        try:  
            super(rtl_iofile,self).__init__(parent=parent,**kwargs)
            self.paramname=kwargs.get('param','-g g_file_')

            self._ioformat=kwargs.get('ioformat','%d') #by default, the io values are decimal integer numbers

        except:
            self.print_log(type='F', msg="Verilog IO file definition failed")


    @property
    def ioformat(self):
        if hasattr(self,'_ioformat'):
            return self._ioformat
        else:
            self._ioformat='%d'
        return self._ioformat
    
    @ioformat.setter
    def ioformat(self,velue):
        self._ioformat=value

    # Parameters for the verilog testbench estracted from
    # Simulation parameters
    @property
    def file(self):
        self._file=self.parent.simpath +'/' + self.name \
                + '_' + self.rndpart +'.txt'
        return self._file

    @property
    def simparam(self):
        self._simparam=self.paramname \
            + self.name + '=' + self.file
        return self._simparam

    @property
    def rtlparam(self):
        if not hasattr(self,'_rtlparam'):
            key=re.sub(r"-g ",'',self.simparam).split('=')[0]
            val=re.sub(r"-g ",'',self.simparam).split('=')[1]
            self._rtlparam={key:'\"%s\"'%(val)}
        return self._rtlparam
    
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
        if self.iotype=='sample':
            self._verilog_statdef='integer %s, %s;\n' %(self.verilog_stat, self.verilog_fptr)
        elif self.iotype=='event':
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
            self._verilog_fopen='initial %s = $fopen(%s,\"r\");\n' %(self.verilog_fptr,next(iter(self.rtlparam)))
        if self.dir=='out':
            self._verilog_fopen='initial %s = $fopen(%s,\"w\");\n' %(self.verilog_fptr,next(iter(self.rtlparam)))
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
            if self.iotype=='sample':
                self._verilog_connector_datamap=dict()
            elif self.iotype=='event':
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
        if self.Data is None:
            if np.isscalar(init):
                self.Data=(np.ones((1,len(self._verilog_connectors)+1))*init).astype(int)
                self.Data[0,0]=int(time)
            elif init.shape[1]==len(self._verilog_connectors)+1:
                self.Data=init.astype(int)
        else: #Lets manipulate
            index=np.where(self.Data[:,0]==time)[0]
            if index.size > 0:
                # Alter existing value onwards from given time
                self.Data[index[-1]:,self.connector_datamap(name=name)]=int(val)
            else:
                # Find the previous time, duplicate the row and alter the value
                previndex=np.where(self.Data[:,0]<time)[0][-1]
                self.Data=np.r_['0', self.Data[0:previndex+1,:], self.Data[previndex::,:]]
                self.Data[previndex+1,0]=time
                self.Data[previndex+1,self.connector_datamap(name=name)]=val


    # Condition string for monitoring if the signals are unknown
    @property 
    def verilog_io_condition(self):
        if not hasattr(self,'_verilog_io_condition'):
            if self.dir=='out':
                first=True
                for connector in self.verilog_connectors:
                    if first:
                        self._verilog_io_condition='~$isunknown(%s)' %(connector.name)
                        first=False
                    else:
                        self._verilog_io_condition='%s \n&& ~$isunknown(%s)' \
                                %(self._verilog_io_condition,connector.name)
            elif self.dir=='in':
                self._verilog_io_condition= ' 1 '
        return self._verilog_io_condition

    @verilog_io_condition.setter
    def verilog_io_condition(self,value):
        self._verilog_io_condition=value

    @property 
    def verilog_io_sync(self):
        if not hasattr(self,'_verilog_io_sync'):
            if self.iotype=='sample':
                self._verilog_io_sync= '@(posedge clock)\n'
        return self._verilog_io_sync

    @verilog_io_sync.setter
    def verilog_io_sync(self,value):
        self._verilog_io_sync=value

    def verilog_io_condition_append(self,**kwargs ):
        cond=kwargs.get('cond', '')
        if not (not cond ):
            self._verilog_io_condition='%s \n%s' \
            %(self.verilog_io_condition,cond)


    # Write or read construct for file IO
    @property
    def verilog_io(self,**kwargs):
        first=True
        if self.iotype=='sample':
            if self.dir=='out':
                self._verilog_io=' always '+self.verilog_io_sync +'begin\n'
                self._verilog_io+='if ( %s ) begin\n' %(self.verilog_io_condition)
                self._verilog_io+='$fwrite(%s, ' %(self.verilog_fptr)
            elif self.dir=='in':
                self._verilog_io='while (!$feof(f_%s)) begin\n' %self.name
                self._verilog_io+='   %s' %self.verilog_io_sync
                self._verilog_io+='        if ( %s ) begin\n' %self.verilog_io_condition      
                self._verilog_io+='        %s = $fscanf(%s, ' \
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
            self._verilog_io+=format+iolines+'\n);\n        end\n    end\n'

        #Control files are handled differently
        elif self.iotype=='event':
            if self.dir=='out':
                self.print_log(type='F', msg='Output writing for control files not supported')
            elif self.dir=='in':
                self._verilog_io='begin\nwhile(!$feof(%s)) begin\n    ' \
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
            self._verilog_io+='end\nend\n'
        else:
            self.print_log(type='F', msg='Iotype not defined')
        return self._verilog_io

