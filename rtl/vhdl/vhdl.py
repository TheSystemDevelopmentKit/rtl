"""
VHDL class
==========

This class contains all VHDL related properties that
are used by the simulator specific classes.

Initially written by Marko Kosunen 30.10.20200, marko.kosunen@aalto.fi 
"""

from thesdk import *
from rtl.rtl_iofile import rtl_iofile as rtl_iofile

class vhdl(thesdk,metaclass=abc.ABCMeta):
    @property
    def vhdlsrcpath(self):
        ''' VHDL search path
            self.entitypath/vhdl

            Returns
            -------
                self.entitypath/vhdl

        '''
        if not hasattr(self, '_vhdlsrcpath'):
            self._vhdlsrcpath  =  self.entitypath + '/vhdl'
        return self._vhdlsrcpath

    @property
    def vhdlsrc(self):
        '''VHDL source file
           self.vhdlsrcpath/self.name.vhd'

           Returns
           -------
               self.vhdlsrcpath + '/' + self.name + '.vhd'

        '''
        if not hasattr(self, '_vhdlsrc'):
            self._vhdlsrc=self.vhdlsrcpath + '/' + self.name + '.vhd'
        return self._vhdlsrc

    @property
    def vhdlentityfiles(self):
        '''List of VHDL entity files to be compiled in addition to DUT

        '''
        if not hasattr(self, '_vhdlentityfiles'):
            self._vhdlentityfiles =list([])
        return self._vhdlentityfiles
    @vhdlentityfiles.setter
    def vhdlentityfiles(self,value): 
            self._vhdlentityfiles = value
    @vhdlentityfiles.deleter
    def vhdlentityfiles(self): 
            self._vhdlentityfiles = None 


