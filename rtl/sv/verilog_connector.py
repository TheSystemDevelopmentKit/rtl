"""
=================
Verilog connector
=================
Class for describing signals in wide sense, including IO's

Written by Marko Kosunen 20190109 marko.kosunen@aalto.fi
"""
import os
from thesdk import *

class verilog_connector(thesdk):
    def __init__(self, **kwargs):
        ''' Executes init of connector_common, thus having the same attributes and
        parameters.

        Parameters
        ----------
            **kwargs :
               See module module_common

        '''
        #This internal attribute is needed to avoid recursive definition of 'type'
        self._type = kwargs.get('type', 'signed' ) # Depends on language
        self.parent = kwargs.get('parent', None)

    @property
    def type(self):
        ''' Type defaults to None mening that all signals are handled as unsigned integers.
        Can be explicitly set to 'signed' if needed for type conversion of the output signals.
        '''

        # We must handle parametrized widths
        if not hasattr(self, '_type'):
            if type(self.parent.width) == str:
                self._type = None
            else:
                if self.parent.width == 1:
                    self._type = None
                elif self.parent.width > 1:
                    self._type = None
        else:
            if type(self.parent.width) == str:
                if self._type != 'signed':
                    self.print_log(type = 'I',
                        msg = ('Setting type of \'%s\' to \'None\' due to parametrized width.'
                            %(self.parent.name)
                            )
                        )
                self._type = None
            else:
                if self.parent.width == 1 and self._type != 'signed':
                    self._type = None
                elif self.parent.width > 1 and self._type != 'signed':
                    self._type = None
        return self._type
    @type.setter
    def type(self,value):
       self.print_log(type = 'I',
               msg = ('Setting type of \'%s\' to \'%s\'.'
                   %(self.parent.name,value)
                   )
               )
       self._type = value


    @property
    def ioformat(self):
        if not hasattr(self, '_ioformat') or self._ioformat == None:
            self._ioformat = '%d' #Language specific formatting
        return self._ioformat

    @ioformat.setter
    def ioformat(self,value):
        self._ioformat = value

    @property
    def definition(self):
        if self.parent.width==1:
            self._definition = '%s %s;\n' %(self.parent.cls, self.parent.name)
        elif self.type:
            self._definition = ( '%s %s [%s:%s] %s;\n'
                %(self.parent.cls, self.type, self.parent.ll,
                    self.parent.rl, self.parent.name)
            )
        else:
            self._definition = ('%s [%s:%s] %s;\n'
                    %(self.parent.cls, self.parent.ll,
                        self.parent.rl, self.parent.name)
                    )
        return self._definition

    @property
    def initialization(self):
        return '%s = %s;\n' %(self.parent.name,self.parent.init)

    @property
    def assignment(self,**kwargs):
        self._assignment = ( 'assign %s = %s;\n'
                %(self.parent.name,self.parent.connect.name)
                )
        return self._assignment

    def nbassign(self,**kwargs):
        time = kwargs.get('time','')
        value = kwargs.get('value',self.parent.connect.name)
        if time:
            return '%s = #%s %s;\n' %(self.parent.name,time, value)
        else:
            return '%s = %s;\n' %(self.parent.name, value)

    def bassign(self):
        time = kwargs.get('time','')
        value = kwargs.get('value',self.parent.connect.name)
        if time:
            return '%s <= #%s %s;\n' %(self.parent.name,time, value)
        else:
            return '%s <= %s;\n' %(self.parent.name, value)

