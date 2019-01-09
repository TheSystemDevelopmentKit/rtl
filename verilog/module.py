# Written by Marko Kosunen 20190109
# marko.kosunen@aalto.fi
import os
import sys
import subprocess
import shlex
from abc import * 
from thesdk import *
from verilog import *
from verilog.signal import verilog_signal

import numpy as np
import pandas as pd
from functools import reduce
import textwrap

class verilog_module(thesdk):
    # Idea  1) Collect IO's to database
    #       3) Reconstruct the module definition
    #       4) Create a method to create assigned module
    #          definition, where signals are 
    #          a) assigned by name
    #          b) to arbitrary name vector                            
    def __init__(self,**kwargs):
        self.file=''  #where to put/from where to read
        self.module=''

    def parse(self,**kwargs):
        pass

    @property
    def name(self):
        if not hasattr(self,'_name'):
            self._name=os.path.splitext(os.path.basename(self.file))[0]
            return self._name
        else:
            return self._name

    @property 
    def ios(self):
        if not hasattr(self,'_ios'):
            startmatch=re.compile(r"module *(?="+self.name+r")\s*"+r".*.+$")
            stopmatch=re.compile(r'.*\);\s*$')
            dut=''
            # Extract the module definition
            with open(self.file) as infile: 
                wholefile=infile.readlines()
                printing=False
                for line in wholefile:
                    if (not printing and startmatch.match(line)):
                        printing=True
                    elif ( printing and stopmatch.match(line)):
                        printing=False
                        #Inclusive
                        dut=dut+line +'\n'
                    if printing:
                        dut=dut+line
                #Generate lambda functions for pattern filtering
                fils=[
                    re.compile(r"(module\s*"+self.name+r"\s*\()"),
                    re.compile(r"^ *"),
                    re.compile(r","),
                    re.compile(r"\);.*")
                  ]
                func_list= [lambda s,fil=x: re.sub(fil,"",s) for x in fils] 
                self._ios=[]
                for line in dut.splitlines():
                    extr=reduce(lambda s, func: func(s), func_list, line)
                    if extr:
                        extr=extr.split()
                        signal=verilog_signal()
                        signal.dir=extr[0]
                        if len(extr)==2:
                            signal.name=extr[1]
                        elif len(extr)==3:
                            signal.name=extr[2]
                            busdef=re.match(r"^.*\[(\d+):(\d+)\]",extr[1])
                            signal.ll=int(busdef.group(1))
                            signal.rl=int(busdef.group(2))
                        self._ios.append(signal)
            return self._ios
        else:
            return self._ios

if __name__=="__main__":
    pass
