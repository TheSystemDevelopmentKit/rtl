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
from thesdk.iofile import iofile
import numpy as np
import pandas as pd
import sortedcontainers as sc

class verilog_iofile(iofile):
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

