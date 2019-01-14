# Written by Marko Kosunen 20190109 marko.kosunen@aalto.fi

import os
from thesdk import *
from verilog import *

## Class for storing signals in wide sense, including IO's
class verilog_connector(thesdk):
    def __init__(self,**kwargs):
        self.name=kwargs.get('name','')
        self.cls=kwargs.get('cls','')   # Input,output,inout,reg,wire,reg,wire
        self.type=kwargs.get('type','') # signed
        self.ll=0                       # Bus range left limit 0 by default
        self.rl=0                       # Bus bus range right limit 0 by default
        self.init=kwargs.get('init','') # Initial value
        self.connect=kwargs.get('connect',None) # Verilog_connector_bundle

    @property
    def width(self):
        self._width=self.ll-self.rl+1
        return self._width

    @property
    def connected(self,**kwargs):
        if hasattr(self,'connect'):
            return self.connect.Members.keys()
        else:
            return None

class verilog_connector_bundle(Bundle):
    def __init__(self,**kwargs):
        super(verilog_connector_bundle,self).__init__(**kwargs)

    def mv(self,**kwargs):
        fro=kwargs.get('fro')
        to=kwargs.get('to')
        self.Members[to]=self.Members.pop(fro)
        self.Members[to].name=to

if __name__=="__main__":
    pass

