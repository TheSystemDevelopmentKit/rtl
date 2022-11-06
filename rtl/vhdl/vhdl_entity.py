"""
===========
VHDL_entity
===========
VHDL import features for RTL simulation package of The System Development Kit 

Provides utilities to import VHDL entities to 
python environment. Imported VHDL entities will be instantiated as verilog modules, 
and are intended to be simulated within verilog testbench with simulator supporting 
cross language compilations. 

Initially written by Marko Kosunen, 2017

Transferred from VHDL package in Dec 2019

"""
import os
from thesdk import *
from copy import deepcopy
from rtl import *
from rtl.sv.verilog_module import verilog_module
from rtl.connector import verilog_connector
from rtl.connector import verilog_connector_bundle
from rtl.module_common import module_common

class vhdl_entity(verilog_module,thesdk):

    def __init__(self, **kwargs):
        ''' Executes init of verilog_module, thus having the same attributes and 
        parameters.

        Parameters
        ----------
            **kwargs :
               See module module
        
        '''
        super().__init__(**kwargs)
    

    @property
    def ios(self):
        '''Verilog connector bundle containing connectors for all module IOS.
           All the IOs are connected to signal connectors that 
           have the same name than the IOs. This is due to fact the we have decided 
           that all signals are connectors. 

        '''
        
        if not hasattr(self,'_ios'):
            startmatch=re.compile(r"entity *(?="+self.name+r"\s*is)"+r".*.+$")
            iomatch=re.compile(r".*port\(.*$")
            #iomatch=re.compile(r".*$")
            parammatch=re.compile(r".*generic\(.*$")
            iostopmatch=re.compile(r'.*\);.*$')
            dut=''
            # Extract the module definition
            self._ios=verilog_connector_bundle()
            if os.path.isfile(self.file):
                with open(self.file) as infile:
                    wholefile=infile.readlines()
                    modfind=False
                    paramfind=False
                    iofind=False
                    for line in wholefile:
                        if (not modfind and startmatch.match(line)):
                            modfind=True
                        if modfind and parammatch.match(line):
                                paramfind=True
                        if modfind and iomatch.match(line):
                                iofind=True
                        if modfind and iofind: 
                            # We need to filter all (); combinations 
                            # from the line and check if ); still exists
                            testline=re.sub("\(.*?\)","",line)
                            if iostopmatch.match(testline):
                                modfind=False
                                iofind=False
                                paramfind=False
                                #Inclusive
                                line=re.sub(r"--.*;.*$","\);",line) +'\n'
                                #Force newline
                                line=re.sub(r"\);","",line) +'\n'
                                dut+=re.sub(r"--.*;.*$","\);",line) +'\n'
                            dut=dut+re.sub(r"--.*$","",line)
                    #Remove the EOL comments
                    dut=re.sub(r";.*$",",",dut)
                    dut=dut.replace("\n","")
                    #Generate lambda functions for pattern filtering
                    fils=[
                        re.compile(r"port\s*\(\s*"),
                        re.compile(r"^\s*"),
                        re.compile(r"--.*$"),
                      ]
                    func_list= [lambda s,fil=x: re.sub(fil,"",s) for x in fils]
                    dut=reduce(lambda s, func: func(s), func_list, dut)
                    dut=re.sub(r"\s+"," ",dut)
                    dut=re.sub(r"\s+in\s*","in :",dut)
                    dut=re.sub(r"\s+out\s*","out :",dut)
                    dut=re.sub(r"\s+inout\s*","inout :",dut)
                    dut=re.sub(r"\s*:\s*",":",dut)
                    dut=re.sub(r"\s*;\s*",";",dut)
                    if dut:
                        for ioline in dut.split(';'):
                            extr=ioline.split(':')
                            signal=verilog_connector()
                            if extr[1]=='in':
                                signal.cls='input'
                            elif extr[1]=='out':
                                signal.cls='output'
                            signal.name=extr[0]
                            #signal.type=extr[2]
                            signal.type=''
                            busdef=re.match(r"^.*\(\s*(.*)(\s+downto\s+|\s+to\s+)(.*)\s*\)",extr[2])
                            if busdef:
                                signal.ll=busdef.group(1)
                                signal.rl=busdef.group(3)
                            #By default, we create a connector that is cross connected to the input
                            signal.connect=deepcopy(signal)
                            if signal.cls=='input':
                                signal.connect.cls='reg'
                            if signal.cls=='output':
                                signal.connect.cls='wire'

                            self._ios.Members[signal.name]=signal
                            signal.connect.connect=signal
                            self._ios.Members[signal.name]=signal
        return self._ios

    # Setting principle, assign a dict
    # individual parameters can be set externally
    @ios.setter
    def ios(self,value):
        self._ios=deepcopy(value)

    @property
    def parameters(self):
        '''Verilog parameters extracted from generics of the VHDL entity

        '''
        if not hasattr(self,'_parameters'):
            startmatch=re.compile(r"entity *(?="+self.name+r"\s*is)"+r".*.+$")
            parammatch=re.compile(r".*(?<=generic)\(.*$")
            paramstopmatch=re.compile(r".*\);.*$")
            parablock=''
            self._parameters=Bundle()
            # Extract the module definition
            if os.path.isfile(self.file):
                with open(self.file) as infile:
                    wholefile=infile.readlines()
                    modfind=False
                    parafind=False
                    for line in wholefile:
                        if (not modfind and startmatch.match(line)):
                            modfind=True
                        if modfind and parammatch.match(line):
                              parafind=True
                        if ( modfind and parafind and paramstopmatch.match(line)):
                            modfind=False
                            parafind=False
                            line=re.sub(r"\);.*$","",line)
                            line=re.sub(r"--.*$","",line)
                            #Inclusive
                            parablock=parablock+line +'\n'
                        elif modfind and parafind:
                            line=re.sub(r"--.*$","",line)
                            parablock=parablock+line
                    # Eventually we need to generate at least a tuple,
                    # but we could also have a parameter class with more properties  
                    if parablock:
                        #Generate lambda functions for pattern filtering
                        parablock.replace("\n","")
                        #After these values we have name:type:value
                        fils=[
                            re.compile(r"generic\s*"),
                            re.compile(r"--"),
                            re.compile(r"\(*"),
                            re.compile(r"\)*"),
                            re.compile(r"\s*"),
                            re.compile(r"="),
                          ]
                        func_list= [lambda s,fil=x: re.sub(fil,"",s) for x in fils]
                        parablock=reduce(lambda s, func: func(s), func_list, parablock)
                        parablock=parablock.split(';')
                        for param in parablock:
                            extr=param.split(':')
                            self._parameters.Members[extr[0]]=extr[2]
        return self._parameters

    # Setting principle, assign a dict
    # individual parameters can be set externally
    @parameters.setter
    def parameters(self,value):
        self._parameters.Members=deepcopy(value)

    @property
    def contents(self):
        ''' Contents is extracted. We do not know what to do with it yet. 
        
        '''
        if not hasattr(self,'_contents'):
            startmatch=re.compile(r"\s*architecture\s+.*\s+of\s+"+self.name+r".*$")
            modulestopmatch=re.compile(r"\s*end\s+.* architecture\s*$")
            self._contents='\n'
            # Extract the module definition
            if os.path.isfile(self.file):
                modfind=False
                with open(self.file) as infile:
                    wholefile=infile.readlines()
                    for line in wholefile:
                        if startmatch.match(line):
                            self._contents=line
                            modfind=True
                        elif modfind and modulestopmatch.match(line):
                            modfind=False
                            #exclusive
                        elif modfind:
                            self._contents=self._contents+line
        return self._contents
    @contents.setter
    def contents(self,value):
        self._contents=value
    @contents.deleter
    def contents(self,value):
        self._contents=None

if __name__=="__main__":
    pass
