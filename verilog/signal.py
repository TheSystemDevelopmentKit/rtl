# Written by Marko Kosunen 20190109 marko.kosunen@aalto.fi
import os
import sys
import subprocess
import shlex
from abc import * 
from thesdk import *
from verilog import *
import numpy as np
import pandas as pd
from functools import reduce
import textwrap

## Class for storing signals in wide sense, including IO's
class verilog_signal(thesdk):
    def __init__(self,**kwargs):
        self.name=''
        self.dir='' # In,out,inout,reg,wire
        self.ll=0   # Signal bus range left limit 0 by default
        self.rl=0   # Signal bus range right limit 0 by default

    @property
    def width(self):
        if not hasattr(self,'_width'):
            self._width=self.ll-self.rl+1
        return self._width

if __name__=="__main__":
    pass
