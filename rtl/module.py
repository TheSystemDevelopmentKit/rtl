"""
======
Module
======
Module import features for RTL simulation package of 
The System Development Kit. 'Module' represents verilog 
module or VHDL entity.

Provides utilities to import Verilog modules to 
python environment.

Initially written by Marko Kosunen, 2017

"""
import os
from thesdk import *
from rtl import *
from copy import deepcopy
from rtl.connector import verilog_connector
from rtl.connector import verilog_connector_bundle
from rtl.module_common import module_common
from rtl.sv.verilog_module import verilog_module
from rtl.vhdl.vhdl_entity import vhdl_entity
from rtl.verilator.verilator_module import verilator_module

class module(module_common,thesdk):
    """ Currently module class is just an alias for verilog_module.

    """
    def __init__(self, **kwargs):
        ''' Executes init of module_common, thus having the same attributes and 
        parameters.

        Parameters
        ----------
            **kwargs :
               See module module_common
        
        '''
        super().__init__({**kwargs})

    #@property
    #def lang(self)
    #    '''Description language used.

    #    Default: `sv`

    #    '''
    #    if not hasattr(self,'_lang'):
    #        self._lang='sv'
    #    return self._lang
    #@lang.setter
    #def lang(self,value):
    #        self._lang=value

    @property
    def langmodule(self):
        """The language specific operation is defined with an instance of 
        language specific class. Properties and methods return values from that class.
        """
        if not hasattr(self, '_langmodule'):
            if self.lang == 'sv':
                self._langmodule=verilog_module(
                        file=self.file, name=self.name, 
                        instname=self.instname)
            elif self.lang == 'vhdl':  
                self._langmodule=vhdl_entity(
                        file=self.file, name=self.name, 
                        instname=self.instname)
            elif self.lang == 'verilator':  
                self._langmodule=verilator_module(
                        file=self.file, name=self.name, 
                        instname=self.instname)
        return self._langmodule

    @property
    def ios(self):
        '''Connector bundle containing connectors for all module IOS.
           All the IOs are connected to signal connectors that 
           have the same name than the IOs. This is due to fact the we have decided 
           that all signals are connectors. 

        '''
        return self.langmodule.ios

    # Setting principle, assign a dict
    # individual parameters can be set externally
    @ios.setter
    def ios(self,value):
        self.langmodule.ios=deepcopy(value)

    @property
    def directives(self):
        ''' Verilog directives affecting the whole module.
        '''
        if not hasattr(self,'_directives'):
            self._directives = list()
        return self._directives
    @directives.setter
    def directives(self, value):
        self._directives = value

    @property
    def parameters(self):
        '''Parameters of the verilog module. Bundle of values of type string.

        '''
        return self.langmodule.parameters
    @parameters.setter
    def parameters(self,value):
        self.langmodule.parameters.Members=deepcopy(value)

    @property
    def contents(self):
        '''Contents of the module. String containing the Verilog code after 
        the module definition.

        '''
        return self.langmodule.contents
    @contents.setter
    def contents(self,value):
        self.langmodule.contents=value
    @contents.deleter
    def contents(self,value):
        self.langmodule.contents=None

    @property
    def io_signals(self):
        '''Bundle containing the signal connectors for IO connections.

        '''
        return self.langmodule.io_signals

    @io_signals.setter
    def io_signals(self,value):
        for conn in value.Members :
            self.langmodule.io_signals.Members[conn.name].connect=conn
        return self.langmodule.io_signals

    @property
    def definition(self):
        '''Module definition part extracted for the file. Contains parameters and 
        IO definitions.

        '''
        return self.langmodule.definition

    @property
    def header(self):
        """Header configuring the e.g. libraries if needed"""
        return self.langmodule.header
    @header.setter
    def header(self,value):
        self.langmodule.header=value

    # Instance is defined through the io_signals
    # Therefore it is always regenerated
    @property
    def instance(self):
        '''Instantiation string of the module. Can be used inside of the other modules.

        '''
        return self.langmodule.instance

    #Methods
    def export(self,**kwargs):
        '''Method to export the module to a given file.

        Parameters
        ----------
           **kwargs :

               force: Bool

        '''
        self.langmodule.export(force=kwargs.get('force'))

if __name__=="__main__":
    pass

