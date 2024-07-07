"""
===================
Verilator connector
===================
Class for describing signals in wide sense, including IO's

Written by Marko Kosunen 20190109 marko.kosunen@aalto.fi
"""
import os
from thesdk import *
from rtl.connector_common import connector_common

class verilator_connector(connector_common,thesdk):
    def __init__(self, **kwargs):
        ''' Executes init of connector_common, thus having the same attributes and 
        parameters.

        Parameters
        ----------
            **kwargs :
               See module module_common
        
        '''
        super().__init__(**kwargs)
        #This internal attribute is needed to avoid recursive definition of 'type'
        self._type=kwargs.get('type', 'signed' ) # Depends on language

    @property
    def type(self):
        ''' Type defaults to None mening that all signals are handled as unsigned integers.
        Can be explicitly set to 'signed' if needed for type conversion of the output signals.
        '''

        # We must handle parametrized widths
        if not hasattr(self, '_type'):
            if type(self.width) == str:
                self._type = None
            elif self.width == 1:
                self._type = None
            elif self.width > 1:
                self._type = None
        else:
            if type(self.width) == str and self._type != 'signed':
                self.print_log(type='I', msg='Setting type of \'%s\' to \'None\' due to parametrized width ' %(self.name))
                self._type = None
            elif self.width == 1 and self._type != 'signed':
                self._type = None
            elif self.width > 1 and self._type != 'signed':
                self._type = None
        return self._type
    @type.setter
    def type(self,value):
       self.print_log(type='I', msg='Setting type of \'%s\' to \'%s\' ' %(self.name,value))
       self._type = value


    @property
    def verilator_signal_type(self):
        ''' Type defaults to std_logic_vector meaning that all signals are handled as unsigned integers.
        '''
        if self.type == 'signed':
            unsigned = ''
        else:
            unsigned = 'u'

        bits = 1
        if self.width <= 1:
            bits = 1
        elif self.width <= 8:
            bits = 8
        elif self.width <= 16:
            bits = 16
        elif self.width <= 32:
            bits = 32
        elif self.width <= 64:
            bits = 64
        else:
            self.print_log(cls='F', msg="Our Verilator interface cannot handle more bits than 64 for now")


        if not hasattr(self, '_verilator_signal_type'):
            if type(self.width) == str:
                self._verilator_signal_type = unsigned+'int64_t'
            elif self.width == 1:
                self._verilator_signal_type = 'bool'
            elif self.width > 1:
                self._verilator_signal_type = unsigned + 'int' + str(bits) + '_t'

        else:
            if type(self.width) == str:
                self._verilator_signal_type = unsigned+'int64_t'
            elif self.width == 1 and self._verilator_signal_type != 'bool':
                self.print_log(type='I', msg='Setting verilator_signal_type of \'%s\' to type \'bool\' for Verilator simulations ' %(self.name))
                self._verilator_signal_type = 'bool'
            elif self.width > 1 and self._verilator_signal_type != unsigned + 'int' + str(bits)+'_t':
                self.print_log(type='I', msg='Setting verilator_signal_type of \'%s\' to \'%sint%s_t\' for Verilator simulations ' %(self.name,unsigned,str(bits)))
                self._verilator_signal_type = unsigned + 'int' + str(bits) + '_t'
        return self._verilator_signal_type

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
        if not self.init:
            self._definition='%s %s;\n' %(self.verilator_signal_type, self.name)
        else:
            self._definition='%s %s = %s;\n' %(self.verilator_signal_type,self.name,self.init)
        return self._definition
    @property
    def assignment(self, **kwargs):
        self._assignment = '%s = %s;\n' % (self.name, self.connect.name)
        return self._assignment

    def nbassign(self,**kwargs):
        time=kwargs.get('time','')
        value=kwargs.get('value',self.connect.name)
        if time:
            return '%s = #%s %s;\n' %(self.name,time, value)
        else:
            return '%s = %s;\n' %(self.name, value)

    def bassign(self, **kwargs):
        time=kwargs.get('time','')
        value=kwargs.get('value',self.connect.name)
        if time:
            return '%s <= #%s %s;\n' %(self.name,time, value)
        else:
            return '%s <= %s;\n' %(self.name, value)

if __name__=="__main__":
    pass
