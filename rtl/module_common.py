"""
=============
Module common
=============
Class containing common properties and methods for all language dependent modules


Initially written by Marko Kosunen, 28.10.2022
"""
import os
from thesdk import *
from rtl import *
from copy import deepcopy

class module_common(thesdk):
    def __init__(self, **kwargs):
        '''Parameters
           ----------
              **kwargs :
                 file: str
                    Verilog file containing the module
                 name: str
                    Name of the module
                 instname: str, self.name
                    Name of the instance
                 lang: str, language of the module 'sv' | 'vhdl' not supported yet.
                     Default: 'sv'
        '''

        self.file=kwargs.get('file','')
        self._name=kwargs.get('name','')
        self._instname=kwargs.get('instname',self.name)
        if not self.file and not self._name:
            self.print_log(type='F', msg='Either name or file must be defined')
        
    @property
    def name(self):
        """Name of the module. Derived from the file name.

        """

        if not self._name:
            self._name=os.path.splitext(os.path.basename(self.file))[0]
        return self._name

    @property
    def instname(self):
        """Name of the instance, when instantiated inside other module.

        Default: `self.name_DUT`

        """
        if not hasattr(self,'_instname'):
            self._instname=self.name+'_DUT'
        return self._instname
    @instname.setter
    def instname(self,value):
            self._instname=value

    @property
    @abstractmethod
    def ios(self):
        '''Connector bundle containing connectors for all module IOS.
           All the IOs are connected to signal connectors that 
           have the same name than the IOs. This is due to fact the we have decided 
           that all signals are connectors. 

        '''
        return self.langmodule.ios

    @property
    @abstractmethod
    def parameters(self):
        '''Parameters of the verilog module. Bundle of values of type string.

        '''
        return self.langmodule.parameters

    @parameters.setter
    def parameters(self,value):
        self.langmodule.parameters.Members=deepcopy(value)

    @property
    @abstractmethod
    def contents(self):
        '''Contents of the module. String containing the Verilog code after 
        the module definition.

        '''
        return self.langmodule.contents

    @property
    @abstractmethod
    def io_signals(self):
        '''Bundle containing the signal connectors for IO connections.

        '''
        return self.langmodule.io_signals

    @property
    @abstractmethod
    def definition(self):
        '''Module definition part extracted for the file. Contains parameters and 
        IO definitions.

        '''
        return self.langmodule.definition

    # Instance is defined through the io_signals
    # Therefore it is always regenerated
    @property
    @abstractmethod
    def instance(self):
        '''Instantioation string of the module. Can be used inside of the other modules.

        '''
        return self.langmodule.instance

    #Methods
    @abstractmethod
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

