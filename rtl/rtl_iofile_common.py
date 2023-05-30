import os
import sys
import pdb
from abc import * 
from thesdk import *
from thesdk.iofile import iofile
import numpy as np
import pandas as pd
import sortedcontainers as sc
"""
========================
RTL IOfile common module 
========================

Collection of common properties and methods for Verilog- and VHDL file-io  
for TheSyDeKick RTL intereface.

Initially written by Marko Kosunen, marko.kosunen@aalto.fi 20230530
"""
class rtl_iofile_common(iofile):

    #Overload from iofile package
    @property
    def file(self):
        ''' Name of the IO file to be read or written.

        '''
        if not hasattr(self,'_file'):
            self._file=self.parent.simpath +'/' + self.name \
                    + '_' + self.rndpart +'.txt'
        return self._file
    



