# Written by Marko Kosunen 20190109 marko.kosunen@aalto.fi
import os
from thesdk import *
from verilog import *

## Class for storing signals in wide sense, including IO's
class verilog_signal(thesdk):
    def __init__(self,**kwargs):
        self.name=''
        self.dir=''     # Input,output,inout,reg,wire,reg_s,wire_s
        self.ll=0       # Signal bus range left limit 0 by default
        self.rl=0       # Signal bus range right limit 0 by default
        self.connect=''
        self.init=''    # Initial value

    @property
    def width(self):
        self._width=self.ll-self.rl+1
        return self._width


if __name__=="__main__":
    pass
