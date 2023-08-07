"""
=================
Verilog connector
=================
Class for describing signals in wide sense, including IO's

Written by Marko Kosunen 20190109 marko.kosunen@aalto.fi
"""
import os
from thesdk import *
from rtl.connector_common import connector_common

class vhdl_connector(connector_common,thesdk):
    def __init__(self, **kwargs):
        ''' Executes init of connector_common, thus having the same attributes and 
        parameters.

        Parameters
        ----------
            **kwargs :
               See module module_common
        
        '''
        super().__init__(**kwargs)
        self._type=kwargs.get('type', 'std_logic_vector' ) # Depends on language
    @property
    def type(self):
        ''' Type defaults to std_logic_vector meaning that all signals are handled as unsigned integers.
        '''
        if not hasattr(self, '_type'):
            if type(self.width) == str:
                self._type = 'std_logic_vector'
            elif self.width == 1:
                self._type = 'std_logic'
            elif self.width > 1:
                self._type = 'std_logic_vector'
        else:
            if self.width == 1 and self._type != 'std_logic':
                self.print_log(type='I', msg='Converting type \'%s\' to type \'std_logic\' for VHDL simulations ' %(self._type))
                self._type = 'std_logic'
            elif self.width > 1 and self._type != 'std_logic_vector':
                self.print_log(type='I', msg='Converting type \'%s\' to type \'std_logic_vector\' for VHDL simulations ' %(self._type))
                self._type = 'std_logic_vector'
        return self._type
    @type.setter
    def type(self,value):
       self._type = value


    @property
    def ioformat(self):
        if not hasattr(self, '_ioformat') or self._ioformat == None:
            self._ioformat='%d' #Language specific formatting
        return self._ioformat
    @ioformat.setter
    def ioformat(self,value):
        self._ioformat = value

    @property
    def definition(self):
        if self.width==1:
            if not self.type:
                self.type='std_logic'
            if not self.init:
                self._definition='signal %s :  %s;\n' %(self.name, self.type,)
            else:
                self._definition='signal %s :  %s := %s;\n' %(self.name, self.type,self.init)

        else:
            if not self.type:
                self.type='std_logic_vector'
            if not self.init:
                self._definition='signal %s : %s(%s downto %s);\n' %(self.name, self.type, self.ll, self.rl)
            else:
                self._definition='signal %s : %s(%s downto %s) := %s ;\n' %(self.name, self.type, self.ll, self.rl, self.init)
        return self._definition

    @property
    def initialization(self):
        self.print_log(type='W', msg='Initialization is not effective for VHDL')
        return ''
    
    @property
    def assignment(self,**kwargs):
        self._assignment='%s <= %s;\n' %(self.name,self.connect.name)
        return self._assignment

    def nbassign(self,**kwargs):
        time=kwargs.get('time','')
        value=kwargs.get('value',self.connect.name)
        if time:
            return '%s = #%s %s;\n' %(self.name,time, value)
        else:
            return '%s = %s;\n' %(self.name, value)

    def bassign(self):
        time=kwargs.get('time','')
        value=kwargs.get('value',self.connect.name)
        if time:
            return '%s <= #%s %s;\n' %(self.name,time, value)
        else:
            return '%s <= %s;\n' %(self.name, value)

if __name__=="__main__":
    pass

