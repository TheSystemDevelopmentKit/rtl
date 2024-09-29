"""
=================
VHDL connector
=================
Class for describing signals specific to VHDL

Inititally written by Marko Kosunen 20190109 marko.kosunen@aalto.fi
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
        self.parent=kwargs.get('parent', None)


    @property
    def type(self):
        ''' Type defaults to None meaning that all signals are handled as unsigned integers.
        Can be explicitly set to 'signed' if needed for type conversion of the output signals.
        '''

        # We must handle parametrized widths
        if not hasattr(self, '_type'):
            if type(self.width) == str:
                self._type = None
            else:
                if self.width == 1:
                    self._type = None
                elif self.width > 1:
                    self._type = None
        else:
            if type(self.width) == str:
                if self._type != 'signed':
                    self.print_log(type='I', msg='Setting type of \'%s\' to \'None\' due to parametrized width ' %(self.name))
                    self._type = None
            else:
                if self.width == 1 and self._type != 'signed':
                    self._type = None
                elif self.width > 1 and self._type != 'signed':
                    self._type = None
        return self._type
    @type.setter
    def type(self,value):
       self.print_log(type='I', msg='Setting type of \'%s\' to \'%s\' ' %(self.name,value))
       self._type = value

    @property
    def name(self):
        return self.parent.name

    @property
    def init(self):
        return self.parent.init

    @property
    def width(self):
        return self.parent.width

    @property
    def ll(self):
        return self.parent.ll

    @property
    def rl(self):
        return self.parent.rl

    @property
    def vhdl_signal_type(self):
        ''' Type defaults to std_logic_vector meaning that all signals are handled as unsigned integers.
        '''
        if not hasattr(self, '_vhdl_signal_type'):
            if type(self.width) == str:
                self._vhdl_signal_type = 'std_logic_vector'
            elif self.width == 1:
                self._vhdl_signal_type = 'std_logic'
            elif self.width > 1:
                self._vhdl_signal_type = 'std_logic_vector'
        else:
            if type(self.width) == str:
                self._vhdl_signal_type = 'std_logic_vector'
            elif self.width == 1 and self._vhdl_signal_type != 'std_logic':
                self.print_log(type='I', msg='Setting vhdl_signal_type of \'%s\' to type \'std_logic\' for VHDL simulations ' %(self.name))
                self._vhdl_signal_type = 'std_logic'
            elif self.width > 1 and self._vhdl_signal_type != 'std_logic_vector':
                self.print_log(type='I', msg='Setting vhdl_signal_type of \'%s\' to \'std_logic_vector\' for VHDL simulations ' %(self.name))
                self._vhdl_signal_type = 'std_logic_vector'
        return self._vhdl_signal_type

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
            if not self.init:
                self._definition='signal %s :  %s;\n' %(self.name, self.vhdl_signal_type,)
            else:
                self._definition='signal %s :  %s := %s;\n' %(self.name, self.vhdl_signal_type,self.init)

        else:
            if not self.init:
                self._definition='signal %s : %s(%s downto %s);\n' %(self.name, self.vhdl_signal_type, self.ll, self.rl)
            else:
                self._definition='signal %s : %s(%s downto %s) := %s ;\n' %(self.name, self.vhdl_signal_type, self.ll, self.rl, self.init)
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

