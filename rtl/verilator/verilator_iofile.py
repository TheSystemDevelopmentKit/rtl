"""
=======================
Verilator IOfile module
=======================

Provides verilog- file-io related attributes and methods
for TheSyDeKick Verilator intereface.

Adapted from verilog_iofile by Aleksi Korsman, aleksi.korsman@aalto.fi, 2022

"""
import os
import sys
import pdb
from abc import *

from thesdk import *
from rtl.rtl_iofile_common import rtl_iofile_common
import numpy as np
import pandas as pd
import sortedcontainers as sc
from rtl.connector import indent

class verilator_iofile(rtl_iofile_common):
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
        '''Status variable name to be used in verilator testbench.

        '''
        if not hasattr(self,'_rtl_stat'):
            self._rtl_stat = 'status_%s' %(self.name)
        return self._rtl_stat

    @rtl_stat.setter
    def rtl_stat(self,value):
        self._rtl_stat=value

    #Timestamp integers for control files
    @property
    def rtl_ctstamp(self):
        '''Current time stamp variable name to be used in verilator testbench.
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
        if not hasattr(self,'_rtl_diff'):
            self._rtl_tdiff='tdiff_%s' %(self.name)
        return self._rtl_tdiff

    # File pointer
    @property
    def rtl_fptr(self):
        '''Verilator file pointer name.

        '''
        self._rtl_fptr='f_%s' %(self.name)
        return self._rtl_fptr

    @rtl_fptr.setter
    def rtl_fptr(self,value):
        self._rtl_fptr=value


    @property
    def rtl_statdef(self):
        '''Verilator file read status integer variable definitions and initializations strings.

        '''
        if self.parent.iotype == 'sample':
            self._rtl_statdef = 'int %s;\n' % (self.rtl_stat)
        elif self.iotype == 'event':
            self._rtl_statdef = 'int %s;\n' % (self.rtl_stat)
            self._rtl_statdef += 'time_t %s, %s, %s;\n' % (self.rtl_ctstamp,
                    self.rtl_pstamp, self.rtl_tdiff)
            self._rtl_statdef += '%s = 0;\n' % self.rtl_ctstamp
            self._rtl_statdef += '%s = 0;\n' % self.rtl_pstamp
            for connector in self.parent.rtl_connectors:
                self._rtl_statdef += 'int buffer_%s;\n' % connector.name
        return self._rtl_statdef

    # File opening, direction dependent
    @property
    def rtl_fopen(self):
        '''Verilator file open routine string.

        '''
        if self.parent.dir == 'in':
            self._rtl_fopen = 'std::ifstream %s(%s);\n' % (self.rtl_fptr,next(iter(self.rtlparam)))
        if self.parent.dir == 'out':
            self._rtl_fopen = 'std::ofstream %s(%s);\n' % (self.rtl_fptr,next(iter(self.rtlparam)))
        return self._rtl_fopen

    # File close
    @property
    def rtl_fclose(self):
        '''Verilator file close routine sting.

        '''
        self._rtl_fclose = '%s.close();\n' % self.rtl_fptr
        return self._rtl_fclose

    # Condition string for monitoring if the signals are unknown
    @property
    def rtl_io_condition(self):
        '''Verilator condition string that must be true in order to file IO read/write to occur.
        This is true always as initial values, because signal values in verilator are always defined, being either 0 or 1.

        Default for output file: `true` for all connectors of the file.
        Default for input file: `true`
        file is always read with rising edge of the clock or in the time of an event defined in the file.

        '''
        if not hasattr(self, '_rtl_io_condition'):
            self._verilog_io_condition = 'true'
        return self._verilog_io_condition
    @rtl_io_condition.setter
    def rtl_io_condition(self,value):
        self._rtl_io_condition=value

    @property
    def rtl_io_sync(self):
        '''File io synchronization condition for sample type input.
        Default: clock == 1 (this assumes that clock changes 0->1->0->1 all the time)
        #Note MK: This assumption might be false. We sould define rising-and falling transitions for the clock.
        '''

        if not hasattr(self, '_rtl_io_sync'):
            if self.iotype == 'sample':
                self._rtl_io_sync = 'clock == 1'
        return self._rtl_io_sync

    @rtl_io_sync.setter
    def rtl_io_sync(self, value):
        self._rtl_io_sync = value

    def rtl_io_condition_append(self, **kwargs):
        '''Append new condition string to `rtl_io_condition`

        Parameters
        ----------
        **kwargs :
           cond : str

        '''
        cond=kwargs.get('cond', '')
        if cond:
            self.rtl_io_condition='%s \n%s' %(self.rtl_io_condition, cond)

    def rtl_io(self, **kwargs):
        '''Verilator  write/read construct for file IO depending on the direction and file type (event/sample).

        Returns
        _______
        str
            C++ code for file IO to read/write the IO file.

        '''
        first = True
        if self.iotype == 'sample':
            self._rtl_io = 'if ( %s ) {\n' % self.rtl_io_sync
            self._rtl_io += '\tif ( %s ) {\n' % self.rtl_io_condition
            self._rtl_io += '\t\t%s ' % self.rtl_fptr

            iolines = ''
            if self.parent.dir == 'out':
                for connector in self.rtl_connectors:
                    if first:
                        iolines += '<< %s ' % connector.name
                        first = False
                    else:
                        iolines += '<< \'\t\' << %s ' % connector.name
                self._io += iolines + '<< std::endl;\n\t}\n}\n'

            elif self.parent.dir == 'in':
                for connector in self.rtl_connectors:
                    iolines += '>> %s ' % connector.name
                self._rtl_io += iolines + ';\n\t}\n}\n'

        elif self.iotype == 'event':
            self.print_log(type='F', msg='Event based file IO for Verilator has not yet been implemented!')
            if self.parent.dir == 'out':
                self.print_log(type='F', msg='Output writing for control files not supported')
        else:
            self.print_log(type='F', msg='Iotype not defined')
        return self._rtl_io

