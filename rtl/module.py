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
#<<<<<<< HEAD Check where to transfer
#        if not hasattr(self,'_definition'):
#            self._definition = ''
#            # module-wide directives
#            self._definition += '\n'.join(self.directives) + '\n'
#            # module parameters
#            if self.parameters.Members:
#                parameters=''
#                first=True
#                for name, val in self.parameters.Members.items():
#                    if first:
#                        parameters='#(\n    parameter %s = %s' %(name,val)
#                        first=False
#                    else:
#                        parameters=parameters+',\n    parameter %s = %s' %(name,val)
#                parameters=parameters+'\n)'
#                self._definition+='module %s %s' %(self.name, parameters)
#            else:
#                self._definition+='module %s ' %(self.name)
#            # module io
#            first=True
#            if self.ios.Members:
#                for ioname, io in self.ios.Members.items():
#                    if first:
#                        self._definition=self._definition+'(\n'
#                        first=False
#                    else:
#                        self._definition=self._definition+',\n'
#                    if io.cls in [ 'input', 'output', 'inout' ]:
#                        if io.width==1:
#                            self._definition=(self._definition+
#                                    ('    %s %s' %(io.cls, io.name)))
#                        else:
#                            self._definition=(self._definition+
#                                    ('    %s [%s:%s] %s' %(io.cls, io.ll, io.rl, io.name)))
#                    else:
#                        self.print_log(type='F', msg='Assigning signal direction %s to verilog module IO.' %(io.cls))
#                self._definition=self._definition+'\n)'
#            self._definition=self._definition+';'
#            # module body
#            if self.contents:
#                self._definition=self._definition+self.contents+'\nendmodule'
#        return self._definition
#||||||| 30941e9
#        if not hasattr(self,'_definition'):
#            #First we print the parameter section
#            if self.parameters.Members:
#                parameters=''
#                first=True
#                for name, val in self.parameters.Members.items():
#                    if first:
#                        parameters='#(\n    parameter %s = %s' %(name,val)
#                        first=False
#                    else:
#                        parameters=parameters+',\n    parameter %s = %s' %(name,val)
#                parameters=parameters+'\n)'
#                self._definition='module %s %s' %(self.name, parameters)
#            else:
#                self._definition='module %s ' %(self.name)
#            first=True
#            if self.ios.Members:
#                for ioname, io in self.ios.Members.items():
#                    if first:
#                        self._definition=self._definition+'(\n'
#                        first=False
#                    else:
#                        self._definition=self._definition+',\n'
#                    if io.cls in [ 'input', 'output', 'inout' ]:
#                        if io.width==1:
#                            self._definition=(self._definition+
#                                    ('    %s %s' %(io.cls, io.name)))
#                        else:
#                            self._definition=(self._definition+
#                                    ('    %s [%s:%s] %s' %(io.cls, io.ll, io.rl, io.name)))
#                    else:
#                        self.print_log(type='F', msg='Assigning signal direction %s to verilog module IO.' %(io.cls))
#                self._definition=self._definition+'\n)'
#            self._definition=self._definition+';'
#            if self.contents:
#                self._definition=self._definition+self.contents+'\nendmodule'
#        return self._definition
#=======
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

