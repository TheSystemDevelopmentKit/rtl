# Written by Marko Kosunen 20190108
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
## Some guidelines:
## DUT is parsed from the verilog file.
## Simparams are parsed to header from the parent
## All io's are read from a file? (Is this good)
## Code injection should be possible
## at least between blocks
## Default structure during initialization?

#Utilizes logging method from thesdk
class testbench(thesdk):
    @property
    def _classfile(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

    def __init__(self,parent=None, **kwargs):
        if parent==None:
            self.print_log({'type':'F', 'msg':"Parent of Verilog testbench not given"})
        else:
            self.parent=parent
        try:  
            self._file=self.parent.vlogsrcpath + '/tb_' + self.parent.name + '_test.sv'
            self._dutfile=self.parent.vlogsrcpath + '/' + self.parent.name + '.sv'
        except:
            self.print_log({'type':'F', 'msg':"Verilog Testbench file definition failed"})
    
    @property
    def name(self):
        if hasattr(self,'_name'):
            return self._name
    @property
    def file(self):
        if hasattr(self,'_file'):
            return self._file
    
    @property
    def header(self):
        if hasattr(self,'_header'):
            return self._header.content
        else:
            self._header=section(self,name='header')
            return self._header.content
    @header.setter
    def header(self, value):
        if not hasattr(self,'_header'):
            self._header=section(self,name='header')
        self._header.content=value

    @property
    def wire(self):
        if hasattr(self,'_wire'):
            return self._wire.content
        else:
            self._wire=section(self,name='wire')
            return self._wire.content
    @wire.setter
    def wire(self, value):
        if not hasattr(self,'_wire'):
            self._wire=section(self,name='wire')
        self._wire.content='wire %s;\n' %(value)

    @property
    def reg(self):
        if hasattr(self,'_reg'):
            return self._reg.content
        else:
            self._reg=section(self,name='reg')
            return self._reg.content
    @reg.setter
    def reg(self, value):
        if not hasattr(self,'_reg'):
            self._reg=section(self,name='reg')
        self._reg.content='reg %s;\n' %(value)

    @property
    def dut(self):
        if hasattr(self,'_dut'):
            return self._dut.content
        else:
            self._dut=section(self,name='dut')
            if os.path.isfile(self._dutfile):
             #re.match('from bag.design.module import Module',line)
             mod=''

            #I really could not match the parens
            #startmatch=re.compile(r"module *(?="+self.parent.name+r")\s*"+r"\(.*$")
            startmatch=re.compile(r"module *(?="+self.parent.name+r")\s*"+r".*.+$")
            stopmatch=re.compile(r'.*\);\s*$')
            dut=''
            with open(self._dutfile) as infile: 
                wholefile=infile.readlines()
                printing=False
                for line in wholefile:
                    if (not printing and startmatch.match(line)):
                        printing=True
                    elif ( printing and stopmatch.match(line)):
                        printing=False
                        #Inclusive
                        dut=dut+line
                    if printing:
                        dut=dut+line
            self._dut.content=dut
            return self._dut.content

    #We should not need this, but it is wise to enable override
    @dut.setter
    def dut(self, value):
        if not hasattr(self,'_dut'):
            self._dut=section(self,name='dut')
        self._dut.content='dut %s;\n' %(value)

# This might be an overkill, but it makes it possible to have
# section attributes
class section(thesdk):
    def __init__(self,parent=None,**kwargs):
        if parent==None:
            self.print_log({'type':'F', 'msg':"Parent of Verilog section not given"})
        self.name=kwargs.get('name')

    @property
    def content(self):
        if hasattr(self,'_content'):
            return self._content
        else:
            self._content=''
        return self._content

    @content.setter
    def content(self,value):
        self._content=textwrap.dedent(value)

if __name__=="__main__":
    pass
