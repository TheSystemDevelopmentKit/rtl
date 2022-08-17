"""
===========
Verilator
===========
Module to generate a Verilator testbench for TheSyDeKick verilog entity.

Initially written by Aleksi Korsman, 2022

"""

import os
import sys
sys.path.append(os.path.abspath("../../thesdk"))

from thesdk import *
from rtl.verilator_connector import verilator_connector_bundle
from rtl.verilator_iofile import verilator_iofile
from copy import deepcopy

class verilator(thesdk):

    @property
    def _classfile(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

    def __init__(self, tb, parent=None, **kwargs):
        '''Parameters
           ----------
           parent: object, None (mandatory to define). TheSyDeKick parent entity object for this testbench.
           **kwargs :
              None

        '''

        if parent==None:
            # TODO: replafe type to F
            self.print_log(type='I', msg="Parent of Verilog testbench not given")
        else:
            self.parent=parent
        try:  
            # The proper files are determined in rtl based on simulation model
            self._file = self.parent.simtb
            self._dutfile = self.parent.simdut
        except:
            # TODO: replace type to F
            self.print_log(type='I', msg="Verilog Testbench file definition failed")
        
        #The methods for these are derived from verilog_module
        self._name=''
        self.tb = tb
        self._parameters=Bundle()
        self.connectors=verilator_connector_bundle()
        self.iofiles=Bundle()
        self.content_parameters={'c_Ts': ('const int','1/(g_Rs*1e-12)')} # Dict of name: (type,value)
        self.assignment_matchlist=[]

    @property
    def rtlcmd(self):
        if not hasattr(self, '_rtlcmd'):
            vlogmodulesstring=' '.join([ self.parent.rtlsimpath + '/'+ 
                str(param) for param in self.parent.vlogmodulefiles])

            compile_tool = 'verilator'
            compile_args = ' '.join(['--cc', '--trace'])
            compile_dut = self.parent.simdut
            compile_extra_modules = vlogmodulesstring
            build_args = ' '.join(['--exe'])
            build_dut = self.parent.simtb

            #build_cmd = ' '.join([compile_tool, compile_args, compile_dut, compile_extra_modules, build_args, build_dut])
            build_cmd = ' '.join([compile_tool, compile_args, compile_dut])
            print(build_cmd)
            self._rtlcmd = build_cmd
        return self._rtlcmd
    @rtlcmd.setter
    def rtlcmd(self, value):
        self._rtlcmd = value
    @rtlcmd.deleter
    def rtlcmd(self):
        self._rtlcmd = None

    def create_connectors(self):
        '''Cretes verilog connector definitions from 
           1) From a iofile that is provided in the Data 
           attribute of an IO.
           2) IOS of the verilog DUT

        '''
        # Create TB connectors from the control file
        # See controller.py
        for ioname,io in self.parent.IOS.Members.items():
            # If input is a file, adopt it
            if isinstance(io.Data,verilator_iofile): 
                if io.Data.name is not ioname:
                    self.print_log(type='I', 
                            msg='Unifying file %s name to ioname %s' %(io.Data.name,ioname))
                    io.Data.name=ioname
                io.Data.adopt(parent=self)
                self.tb.parameters.Members.update(io.Data.rtlparam)

                for connector in io.Data.verilog_connectors:
                    self.tb.connectors.Members[connector.name]=connector
                    # Connect them to DUT
                    try: 
                        self.dut.ios.Members[connector.name].connect=connector
                    except:
                        pass
            # If input is not a file, look for corresponding file definition
            elif ioname in self.iofile_bundle.Members:
                val=self.iofile_bundle.Members[ioname]
                for name in val.ionames:
                    # [TODO] Sanity check, only floating inputs make sense.
                    if not name in self.tb.connectors.Members.keys():
                        self.print_log(type='I', 
                                msg='Creating non-existent IO connector %s for testbench' %(name))
                        self.tb.connectors.new(name=name, cls='reg')
                self.iofile_bundle.Members[ioname].verilog_connectors=\
                        self.tb.connectors.list(names=val.ionames)
                self.tb.parameters.Members.update(val.rtlparam)
        # Define the iofiles of the testbench. '
        # Needed for creating file io routines 
        self.tb.iofiles=self.iofile_bundle


if __name__=="__main__":
    print("WRONG FILE, FOOL")