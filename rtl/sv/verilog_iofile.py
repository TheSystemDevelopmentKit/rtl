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
            print(self.paramname)
            print(self.name)
            print(self.file)
            key=re.sub(r"-g ",'',self.simparam).split('=')[0]
            val=re.sub(r"-g ",'',self.simparam).split('=')[1]
            self._rtlparam={key:('string','\"%s\"'%(val))}
        return self._rtlparam

    # Status parameter
    @property
    def verilog_stat(self):
        '''Status variable name to be used in verilog testbench.

        '''
        if not hasattr(self,'_verilog_stat'):
            self._verilog_stat='status_%s' %(self.name)
        return self._verilog_stat

    @verilog_stat.setter
    def verilog_stat(self,value):
        self._verilog_stat=value

    #Timestamp integers for control files
    @property
    def verilog_ctstamp(self):
        '''Current time stamp variable name to be used in verilog testbench.
        Used in event type file IO.

        '''
        if not hasattr(self,'_verilog_ctstamp'):
            self._verilog_ctstamp='ctstamp_%s' %(self.name)
        return self._verilog_ctstamp

    @property
    def verilog_ptstamp(self):
        '''Past time stamp variable for verilog testbench. Used in event type file IO.

        '''
        if not hasattr(self,'_verilog_ptstamp'):
            self._verilog_ptstamp='ptstamp_%s' %(self.name)
        return self._verilog_ptstamp

