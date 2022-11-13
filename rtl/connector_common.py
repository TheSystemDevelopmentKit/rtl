"""
=================
Connector common
=================

Written by Marko Kosunen 13.11.2022 marko.kosunen@aalto.fi
"""
import os
from thesdk import *

class connector_common(thesdk):
    def __init__(self,**kwargs):
        """
        Parameters
        ----------
        name : str
        cls : str, input | output | inout | reg | wire
            Default ''
        type: str, signed (if not unsigned)
            Default ''
        ll: int, Left limit of a signal bus
            Default: 0
        rl: int, Right limit of a signalbus
            Default: 0
        init: str, initial value
            Default ''
        connect: verilog_connector instance, An connector this conenctor is connected to.
            Default: None
        ioformat: str, Verilog formating string fo the signal for parsing it from a file.
            Default; '%d', i.e parse as integers.
            
        """
        self.name=kwargs.get('name','')
        self.cls=kwargs.get('cls','')   # Input,output,inout,reg,wire
        self.type=kwargs.get('type','') # signed
        self.ll=kwargs.get('ll',0)      # Bus range left limit 0 by default
        self.rl=kwargs.get('rl',0)      # Bus bus range right limit 0 by default
        self.init=kwargs.get('init','') # Initial value
        self.connect=kwargs.get('connect',None) # Can be another connector, would be recursive

    @property
    def width(self):
        ''' Width of the connector: int | str (for parametrized bounds)'''
            
        if (isinstance(self.ll,str) or isinstance(self.rl,str)):
            self._width=str(self.ll) + '-' + str(self.rl)+'+1'
        else: 
            self._width=int(self.ll)-int(self.rl)+1
        return self._width

    @property
    def definition(self):
        if self.width==1:
            self._definition='%s %s;\n' %(self.cls, self.name)
        elif self.type:
            self._definition='%s %s [%s:%s] %s;\n' %(self.cls, self.type, self.ll, self.rl, self.name)
        else:
            self._definition='%s [%s:%s] %s;\n' %(self.cls, self.ll, self.rl, self.name)
        return self._definition
    
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

