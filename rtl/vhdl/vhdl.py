"""
==========
VHDL class
==========

This mixin contains all VHDL related properties that
are used by the simulator specific classes.

Initially written by Marko Kosunen 30.10.20200, marko.kosunen@aalto.fi 
"""

from thesdk import *
from rtl.rtl_iofile import rtl_iofile as rtl_iofile

class vhdl(thesdk,metaclass=abc.ABCMeta):
    @property
    def vhdlsimtb(self):
        ''' Name of the VHDL testbench
        '''
        return self.rtlsimpath + '/tb_' + self.name + self.vhdlext



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
            self._vhdlsrc=self.vhdlsrcpath + '/' + self.name + self.vhdlext
        return self._vhdlsrc

    @property
    def vhdlext(self):
        ''' File extension for verilog files

            Default is '.vhd', but this can be overridden.

        '''
        if not hasattr(self, '_vhdlext'):
            self._vhdlext = '.vhd'
        return self._vhdlext

    @vhdlext.setter
    def vhdlext(self, value):
        self._vhdlext = value

    @property
    def vhdlcompargs(self):
        ''' List of arguments passed to the simulator
        during VHDL compilation
        
        '''
        if not hasattr(self, '_vhdlcompargs'):
            self._vhdlcompargs = []
        return self._vhdlcompargs
    @vhdlcompargs.setter
    def vhdlcompargs(self, value):
        self._vhdlcompargs = value

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


