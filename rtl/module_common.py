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
        self._lang=kwargs.get('lang',self.lang)

        if not self.file and not self._name:
            self.print_log(type='F', msg='Either name or file must be defined')
        
    @property
    def lang(self):
        '''Description language used.

        Default: `sv`

        '''
        if not hasattr(self,'_lang'):
            self._lang='sv'
        return self._lang

    @lang.setter
    def lang(self,value):
            self._lang=value

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

    # Instance is defined through the io_signals
    # Therefore it is always regenerated
    @property
    def verilog_instance(self):
        '''Instantioation string of the module. Can be used inside of the other modules.

        '''
        #First we write the parameter section
        pdb.set_trace()
        if self.parameters.Members:
            parameters=''
            first=True
            for name, val in self.parameters.Members.items():
                if first:
                    parameters='#(\n    .%s(%s)' %(name,name)
                    first=False
                else:
                    parameters=parameters+',\n    .%s(%s)' %(name,name)
            parameters=parameters+'\n)'
            self._verilog_instance='%s  %s %s' %(self.name, parameters, self.instname)
        else:
            self._verilog_instance='%s %s ' %(self.name, self.instname)
        first=True
        # Then we write the IOs
        if self.ios.Members:
            for ioname, io in self.ios.Members.items():
                if first:
                    self._verilog_instance=self._verilog_instance+'(\n'
                    first=False
                else:
                    self._verilog_instance=self._verilog_instance+',\n'
                if io.cls in [ 'input', 'output', 'inout' ]:
                        self._verilog_instance=(self._verilog_instance+
                                ('    .%s(%s)' %(io.name, io.connect.name)))
                else:
                    self.print_log(type='F', msg='Assigning signal direction %s to verilog module IO.' %(io.cls))
            self._verilog_instance=self._verilog_instance+('\n)')
        self._verilog_instance=self._verilog_instance+(';\n')
        return self._verilog_instance

    @property
    def vhdl_instance(self):
        '''Instantioation string of the module. Can be used inside of the other modules.

        '''
        #First we write the parameter section
        if self.parameters.Members:
            parameters=''
            first=True
            for name, val in self.parameters.Members.items():
                if first:
                    parameters='generic map(\n    %s => %s' %(name,name)
                    first=False
                else:
                    parameters=parameters+',\n    %s > %s' %(name,name)
            parameters=parameters+'\n)'
            self.vhdl_instance='%s  is entity work.%s\n%s\n' %(self.instname, self.name, parameters)
        else:
            self.vhdl_instance='%s is entity work.%s\n ' %(self.instname, self.name)
        first=True
        # Then we write the IOs
        if self.ios.Members:
            for ioname, io in self.ios.Members.items():
                if first:
                    self.vhdl_instance=self.vhdl_instance+'port map(\n'
                    first=False
                else:
                    self.vhdl_instance=self.vhdl_instance+',\n'
                if io.cls in [ 'input', 'output', 'inout' ]:
                        self.vhdl_instance=(self.vhdl_instance+
                                ('    %s => %s' %(io.name, io.connect.name)))
                else:
                    self.print_log(type='F', msg='Assigning signal direction %s to VHDL entity IO.' %(io.cls))
            self.vhdl_instance=self.vhdl_instance+('\n    )')
        self.vhdl_instance=self.vhdl_instance+(';\n')
        return self.vhdl_instance

if __name__=="__main__":
    pass

