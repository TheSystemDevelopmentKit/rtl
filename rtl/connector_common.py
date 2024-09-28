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
        type: str, For verilog: signed, unsigned for VHDL: std_logic, std_logic-vector
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
        self._ll=kwargs.get('ll',0)      # Bus range left limit 0 by default
        self._rl=kwargs.get('rl',0)      # Bus bus range right limit 0 by default
        self._init=kwargs.get('init','') # Initial value
        self.connect=kwargs.get('connect',None) # Can be another connector, would be recursive
        self.lang=kwargs.get('lang','sv')

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
    def init(self):
        '''Initial value of the signal at the time instace 0

        Default: '' , meaning undefined.

        '''
        if not hasattr(self,'_init'):
            self._init=''
        return self._init
    @init.setter
    def init(self,value):
            self._init=value

    @property
    def width(self):
        ''' Width of the connector: int | str (for parametrized bounds)'''
            
        if (isinstance(self.ll,str) or isinstance(self.rl,str)):
            self._width=str(self.ll) + '-' + str(self.rl)+'+1'
        else: 
            self._width=int(self.ll)-int(self.rl)+1
        return self._width

    @property
    def ll(self):
        ''' Left (usually upper) limit of the connector bus: int | str (for parametrized bounds)

        Strings that evaluate to integers are automatically evaluated.
        
        '''
            
        if not hasattr(self,'_ll'):
            self._ll = 0
        return self._ll
    @ll.setter
    def ll(self,value):
        if type(value) == str:
            #Try to evaluate string
            try:
                self._ll = eval(value)
            except:
                self._ll = value
        else:
            self._ll = value
        return self._ll
    @property
    def rl(self):
        ''' Right /usuarly lower) limit of the connector bus: int | str (for parametrized bounds)

        Strings that evaluate to integers are automaticarly evaluated.
        
        '''
            
        if not hasattr(self,'_rl'):
            self._rl=0
        return self._rl
    @rl.setter
    def rl(self,value):
        if type(value) == str:
            #Try to evaluate string
            try:
                self._rl = eval(value)
            except:
                self._rl = value
        else:
            self._rl = value
        return self._rl

