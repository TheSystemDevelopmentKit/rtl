"""
======================
Verilog IOfile module 
======================

Provides verilog- file-io related attributes and methods 
for TheSyDeKick RTL intereface.

Initially written by Marko Kosunen, marko.kosunen@aalto.fi,
Yue Dai, 2018

"""
import os
import sys
import pdb
from abc import * 
from thesdk import *
#from thesdk.iofile import iofile
from rtl.rtl_iofile_common import rtl_iofile_common
import numpy as np
import pandas as pd
import sortedcontainers as sc
from rtl.connector import indent

class verilog_iofile(rtl_iofile_common):
    """
    Class to provide file IO for rtl simulations. When created, 
    adds a rtl_iofile object to the parents iofile_bundle attribute.
    Accessible as self.iofile_bundle.Members['name'].

    Provides methods and attributes that can be used to construct sections
    in Verilog testbenches, like file io routines, file open and close routines,
    file io routines, file io format strings and read/write conditions.
    """

    @property
    def ioformat(self):
        '''Formatting string for verilog file reading
           Default %d, i.e. content of the file is single column of
           integers.
           
        '''
        if not hasattr(self,'_ioformat'):
            self._ioformat='%d'
        return self._ioformat
    
    @ioformat.setter
    def ioformat(self,value):
        self._ioformat=value

    @property
    def rtlparam(self):
        '''Extracts the parameter name and value from simparam attribute. 
        Used to construct the parameter definitions for Verilog testbench. 

        Default {'g_file_<self.name>', ('string',self.file) }

        '''
        if not hasattr(self,'_rtlparam'):
            key=re.sub(r"-g ",'',self.simparam).split('=')[0]
            val=re.sub(r"-g ",'',self.simparam).split('=')[1]
            self._rtlparam={key:('string','\"%s\"'%(val))}
        return self._rtlparam

    # Status parameter
    @property
    def rtl_stat(self):
        '''Status variable name to be used in verilog testbench.

        '''
        if not hasattr(self,'_rtl_stat'):
            self._rtl_stat='status_%s' %(self.name)
        return self._rtl_stat

    @rtl_stat.setter
    def rtl_stat(self,value):
        self._rtl_stat=value

    #Timestamp integers for control files
    @property
    def rtl_ctstamp(self):
        '''Current time stamp variable name to be used in verilog testbench.
        Used in event type file IO.

        '''
        if not hasattr(self,'_rtl_ctstamp'):
            self._rtl_ctstamp='ctstamp_%s' %(self.name)
        return self._rtl_ctstamp

    @property
    def rtl_pstamp(self):
        '''Past time stamp variable for verilog testbench. Used in event type file IO.

        '''
        if not hasattr(self,'_rtl_pstamp'):
            self._rtl_pstamp='ptstamp_%s' %(self.name)
        return self._rtl_pstamp

    @property
    def rtl_tdiff(self):
        '''Verilog time differencec variable. Used in event based file IO.
        '
        '''
        if not hasattr(self,'_verilog_diff'):
            self._rtl_tdiff='tdiff_%s' %(self.name)
        return self._rtl_tdiff

    # File pointer
    @property
    def rtl_fptr(self):
        '''Verilog file pointer name.

        '''
        self._rtl_fptr='f_%s' %(self.name)
        return self._rtl_fptr

    @rtl_fptr.setter
    def rtl_fptr(self,value):
        self._rtl_fptr=value


    @property
    def rtl_statdef(self):
        '''Verilog file read status integer variable definitions and initializations strings.

        '''
        if self.parent.iotype=='sample':
            self._rtl_statdef='integer %s, %s;\n' %(self.rtl_stat, self.rtl_fptr)
        elif self.parent.iotype=='event':
            self._rtl_statdef='integer %s, %s;\n' %(self.rtl_stat, self.rtl_fptr)
            self._rtl_statdef+='time %s, %s, %s;\n' %(self.rtl_ctstamp, self.rtl_pstamp, self.rtl_tdiff)
            self._rtl_statdef+='initial %s=0;\n' %(self.rtl_ctstamp) 
            self._rtl_statdef+='initial %s=0;\n' %(self.rtl_pstamp) 
            for connector in self.parent.rtl_connectors:
                self._rtl_statdef+='integer buffer_%s;\n' %(connector.name)
        return self._rtl_statdef

    # File opening, direction dependent 
    @property
    def rtl_fopen(self):
        '''Verilog file open routine string.

        '''
        if self.parent.dir=='in':
            self._rtl_fopen='initial %s = $fopen(%s,\"r\");\n' %(self.rtl_fptr,next(iter(self.rtlparam)))
        if self.parent.dir=='out':
            self._rtl_fopen='initial %s = $fopen(%s,\"w\");\n' %(self.rtl_fptr,next(iter(self.rtlparam)))
        return self._rtl_fopen

    # File close
    @property
    def rtl_fclose(self):
        '''Verilog file close routine sting.

        '''
        self._rtl_fclose='$fclose(%s);\n' %(self.rtl_fptr)
        return self._rtl_fclose

    # Condition string for monitoring if the signals are unknown
    @property 
    def verilog_io_condition(self):
        '''Verilog condition string that must be true in ordedr to file IO read/write to occur.

        Default for output file: `~$isunknown(connector.name)` for all connectors of the file.
        Default for input file: `'1'` 
        file is always read with rising edge of the clock or in the time of an event defined in the file.

        '''
        if not hasattr(self,'_verilog_io_condition'):
            if self.parent.dir=='out':
                first=True
                for connector in self.parent.rtl_connectors:
                    if first:
                        self._verilog_io_condition='~$isunknown(%s)' %(connector.name)
                        first=False
                    else:
                        self._verilog_io_condition='%s \n&& ~$isunknown(%s)' \
                                %(self._verilog_io_condition,connector.name)
            elif self.parent.dir=='in':
                self.verilog_io_condition= ' 1 '
        return self._verilog_io_condition

    @verilog_io_condition.setter
    def verilog_io_condition(self,value):
        self._verilog_io_condition=value

    @property 
    def verilog_io_sync(self):
        '''File io synchronization condition for sample type input.
        Default: `@(posedge clock)`

        '''

        if not hasattr(self,'_verilog_io_sync'):
            if self.iotype=='sample':
                self._verilog_io_sync= '@(posedge clock)\n'
        return self._verilog_io_sync

    @verilog_io_sync.setter
    def verilog_io_sync(self,value):
        self._verilog_io_sync=value

    def verilog_io_condition_append(self,**kwargs ):
        '''Append new condition string to `verilog_io_condition`

        Parameters
        ----------
        **kwargs :
           cond : str

        '''
        cond=kwargs.get('cond', '')
        if not (not cond ):
            self._verilog_io_condition='%s \n%s' \
            %(self.verilog_io_condition,cond)

    @property
    def verilog_io(self):
        '''Verilog  write/read construct for file IO depending on the direction and file type (event/sample).

        Returns 
        _______
        str
            Verilog code for file IO to read/write the IO file.


        '''
        first=True
        if self.parent.iotype=='sample':
            if self.parent.dir=='out':
                self._verilog_io='always '+self.verilog_io_sync +'begin\n'
                self._verilog_io+=indent(text='if ( %s ) begin\n' %(self.verilog_io_condition), level=1)
                self._verilog_io+=indent(text='$fwrite(%s, ' %(self.rtl_fptr), level=2)
            elif self.parent.dir=='in':
                self._verilog_io='while (!$feof(f_%s)) begin\n' %self.name
                self._verilog_io+=indent(text='%s' %self.verilog_io_sync, level=0)
                self._verilog_io+=indent(text='if ( %s ) begin\n' %self.verilog_io_condition, level=1)
                self._verilog_io+=indent(text='%s = $fscanf(%s, ' \
                        %(self.rtl_stat, self.rtl_fptr), level=2)
            for connector in self.parent.rtl_connectors:
                if first:
                    iolines='%s' %(connector.name)
                    format='\"%s' %(connector.ioformat)
                    first=False
                else:
                    iolines='%s,\n%s' %(iolines,connector.name)
                    format='%s\\t%s' %(format,connector.ioformat)

            format=format+'\\n\",\n'
            self._verilog_io+=indent(text=format+iolines+'\n);',level=2)+indent(text='end', level=1)+indent(text='end', level=0)

        #Control files are handled differently
        elif self.parent.iotype=='event':
            if self.parent.dir=='out':
                self.print_log(type='F', msg='Output writing for control files not supported')
            elif self.parent.dir=='in':
                self._verilog_io='begin\nwhile(!$feof(%s)) begin\n    ' \
                        %(self.rtl_fptr)
                self._verilog_io+='%s = %s-%s;\n    #%s begin\n    ' \
                        %(self.rtl_tdiff,
                        self.rtl_ctstamp, self.rtl_pstamp,
                        self.rtl_tdiff)    

                #t= Every control file requires status, diff, current_timestamp 
                # and past timestamp
                self._verilog_io+='    %s = %s;\n    ' \
                        %(self.rtl_pstamp, self.rtl_ctstamp)

                for connector in self.parent.rtl_connectors:
                    self._verilog_io+='    %s = buffer_%s;\n    ' \
                            %(connector.name,connector.name)

                self._verilog_io+='    %s = $fscanf(%s, ' \
                        %(self.rtl_stat,self.rtl_fptr)

            #The first column is timestap
            iolines='            %s' %(self.rtl_ctstamp) 
            format='\"%d'
            for connector in self.parent.rtl_connectors:
                iolines='%s,\n            buffer_%s' \
                        %(iolines,connector.name)
                format='%s\\t%s' %(format,connector.ioformat)
            format=format+'\\n\",\n'
            self._verilog_io+=format+iolines+'\n        );\n    end\nend\n'

            #Repeat the last assignment outside the loop
            self._verilog_io+='%s = %s-%s;\n#%s begin\n' %(self.rtl_tdiff,
                    self.rtl_ctstamp, self.rtl_pstamp,self.rtl_tdiff)    
            self._verilog_io+='    %s = %s;\n' %(self.rtl_pstamp,
                    self.rtl_ctstamp)
            for connector in self.parent.rtl_connectors:
                self._verilog_io+='    %s = buffer_%s;\n' \
                %(connector.name,connector.name)
            self._verilog_io+='end\nend\n'
        else:
            self.print_log(type='F', msg='Iotype not defined')
        return self._verilog_io



    
