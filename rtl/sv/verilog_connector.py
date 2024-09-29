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

class verilog_connector(connector_common,thesdk):
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
        self.parent=kwargs.get('parent', None)

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
            self._definition='%s %s;\n' %(self.cls, self.name)
        elif self.type:
            self._definition='%s %s [%s:%s] %s;\n' %(self.cls, self.type, self.ll, self.rl, self.name)
        else:
            self._definition='%s [%s:%s] %s;\n' %(self.cls, self.ll, self.rl, self.name)
        return self._definition

    @property
    def initialization(self):
        return '%s = %s;\n' %(self.name,self.init)
    
    @property
    def assignment(self,**kwargs):
        self._assignment='assign %s = %s;\n' %(self.name,self.connect.name)
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

