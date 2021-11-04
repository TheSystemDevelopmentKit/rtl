"""
===========
Module
===========
Verilog module import features for RTL simulation package of 
The System Development Kit.

Provides utilities to import Verilog modules to 
python environment.

Initially written by Marko Kosunen, 2017
Last modification by Okko Järvinen, 28.10.2021 07:55

"""
import os
from thesdk import *
from rtl import *
from copy import deepcopy
from rtl.connector import verilog_connector
from rtl.connector import verilog_connector_bundle

class verilog_module(thesdk):
    '''Objective:

        1) 
           a) Collect IO's to database
           b) collect parameters to dict

        2) Reconstruct the module definition

        3) 
           a) Implement methods provide sinal connections
           b) Implement methods to provide parameter assingments   
              
        4) Create a method to create assigned module \
           definition, where signals are \
           
           a) assigned by name
           b) to arbitrary name vector.

        5) Add contents, if required, and include that to definition
            
    '''

    @property
    def _classfile(self):
        ''' Mandatory because nheriting thesdk class
        
        '''
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

    def __init__(self, **kwargs):
        '''Parameters
           ----------
              **kwargs :
                 file: str
                    Verilog file containing the module
                 name: str
                    Name of the module
                 instname: str, self.name
                    Name of the instance

        '''
        # No need to propertize these yet
        self.file=kwargs.get('file','')
        self._name=kwargs.get('name','')
        self._instname=kwargs.get('instname',self.name)
        if not self.file and not self._name:
            self.print_log(type='F', msg='Either name or file must be defined')
    
    #Name derived from the file
    @property
    def name(self):
        '''Name of the module. Derived from the file name.

        '''

        if not self._name:
            self._name=os.path.splitext(os.path.basename(self.file))[0]
        return self._name

    @property
    def instname(self):
        '''Name of the instance, when instantiated inside other module.

        Default: `self.name_DUT`

        '''
        if not hasattr(self,'_instname'):
            self._instname=self.name+'_DUT'
        return self._instname
    @instname.setter
    def instname(self,value):
            self._instname=value

    @property
    def ios(self):
        '''Verilog connector bundle containing connectors for all module IOS.
           All the IOs are connected to signal connectors that 
           have the same name than the IOs. This is due to fact the we have decided 
           that all signals are connectors. 

        '''
        if not hasattr(self,'_ios'):
            startmatch=re.compile(r"module *(?="+self.name+r")\s*"+r".*.+$")
            iomatch=re.compile(r".*(?<!#)\(.*$")
            parammatch=re.compile(r".*#\(.*$")
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
                        if ( modfind and (iofind or paramfind) and iostopmatch.match(line)):
                            modfind=False
                            iofind=False
                            paramfind=False
                            #Inclusive
                            dut=dut+re.sub(r"//.*;.*$","\);",line) +'\n'
                        elif modfind and iofind:
                            dut=dut+re.sub(r"//.*$","",line)
                    #Remove the scala comments
                    dut=re.sub(r",.*$",",",dut)
                    dut=dut.replace("\n","")
                    #Generate lambda functions for pattern filtering
                    fils=[
                        re.compile(r"module\s*"+self.name+r"\s*"),
                        re.compile(r"\("),
                        re.compile(r"\)"),
                        re.compile(r"^\s*"),
                        re.compile(r"\s*(?=> )"),
                        re.compile(r"////.*$"),
                        re.compile(r";.*")
                      ]
                    func_list= [lambda s,fil=x: re.sub(fil,"",s) for x in fils]
                    dut=reduce(lambda s, func: func(s), func_list, dut)
                    dut=re.sub(r",\s*",",",dut)
                    if dut:
                        for ioline in dut.split(','):
                            extr=ioline.split()
                            signal=verilog_connector()
                            signal.cls=extr[0]
                            if len(extr)==2:
                                signal.name=extr[1]
                            elif len(extr)==3:
                                signal.name=extr[2]
                                busdef=re.match(r"^.*\[(\d+):(\d+)\]",extr[1])
                                signal.ll=int(busdef.group(1))
                                signal.rl=int(busdef.group(2))

                            #By default, we create a connector that is cross connected to the input
                            signal.connect=deepcopy(signal)
                            if signal.cls=='input':
                                signal.connect.cls='reg'
                            if signal.cls=='output':
                                signal.connect.cls='wire'
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
        '''Parameters of the verilog module. Bundle of values of type string.

        '''
        if not hasattr(self,'_parameters'):
            startmatch=re.compile(r"module *(?="+self.name+r")\s*"+r".*.+$")
            iomatch=re.compile(r".*(?<!#)\(.*$")
            parammatch=re.compile(r".*(?<=#)\(.*$")
            paramstopmatch=re.compile(r".*\).*$")
            parablock=''
            self._parameters=Bundle()
            # Extract the module definition
            if os.path.isfile(self.file):
                with open(self.file) as infile:
                    wholefile = infile.readlines()
                    modfind = False
                    iofind = False
                    parafind = False
                    for line in wholefile:
                        if (not modfind and startmatch.match(line)):
                            modfind = True
                        if modfind and (not iofind) and iomatch.match(line):
                            iofind = True
                        if modfind and (not iofind) and parammatch.match(line):
                                parafind = True
                        if ( modfind and (not iofind) and parafind and paramstopmatch.match(line)):
                            modfind = False
                            parafind = False
                            line = re.sub(r"\).*$","",line)
                            line = re.sub(r"//.*$","",line)
                            #Inclusive
                            parablock = parablock+line +'\n'
                        elif modfind and parafind:
                            line = re.sub(r"//.*$","",line)
                            parablock = parablock+line
                    if parablock:
                        #Generate lambda functions for pattern filtering
                        parablock.replace("\n","")
                        fils = [
                            re.compile(r"module\s*"+self.name+r"\s*"),
                            re.compile(r"#"),
                            re.compile(r"\(*"),
                            re.compile(r"\)*"),
                            re.compile(r"\s*"),
                            re.compile(r";*")
                          ]
                        func_list= [lambda s,fil=x: re.sub(fil,"",s) for x in fils]
                        parablock=reduce(lambda s, func: func(s), func_list, parablock)
                        parablock=parablock.split(',')
                        for param in parablock:
                                extr=param.split('=')
                                self._parameters.Members[extr[0]]=extr[1]
        return self._parameters

    # Setting principle, assign a dict
    # individual parameters can be set externally
    @parameters.setter
    def parameters(self,value):
        self._parameters.Members=deepcopy(value)

    @property
    def contents(self):
        '''Contents of the module. String containing the Verilog code after 
        the module definition.

        '''
        if not hasattr(self,'_contents'):
            startmatch=re.compile(r"module *(?="+self.name+r")\s*"+r".*.+$")
            headerstopmatch=re.compile(r".*\);.*$")
            modulestopmatch=re.compile(r"\s*endmodule\s*$")
            self._contents='\n'
            # Extract the module definition
            if os.path.isfile(self.file):
                with open(self.file) as infile:
                    wholefile=infile.readlines()
                    modfind=False
                    headers=False
                    for line in wholefile:
                        if (not modfind and startmatch.match(line)):
                            modfind=True
                        if modfind and headerstopmatch.match(line):
                                headers=True
                        elif ( modfind and headers and modulestopmatch.match(line)):
                            modfind=False
                            headers=False
                            #exclusive
                        elif modfind and headers:
                            self._contents=self._contents+line
        return self._contents
    @contents.setter
    def contents(self,value):
        self._contents=value
    @contents.deleter
    def contents(self,value):
        self._contents=None

    @property
    def io_signals(self):
        '''Bundle containing the signal connectors for IO connections.

        '''
        if not hasattr(self,'_io_signals'):
            self._io_signals=verilog_connector_bundle()
            for ioname, io in self.ios.Members.items():
                # Connectior is created already in io definitio
                # just point to it  
                self._io_signals.Members[ioname]=io.connect
        return self._io_signals

    @io_signals.setter
    def io_signals(self,value):
        for conn in value.Members :
            self._io_signals.Members[conn.name].connect=conn
        return self._io_signals

    @property
    def definition(self):
        '''Module definition part extracted for the file. Contains parameters and 
        IO definitions.

        '''
        if not hasattr(self,'_definition'):
            #First we print the parameter section
            if self.parameters.Members:
                parameters=''
                first=True
                for name, val in self.parameters.Members.items():
                    if first:
                        parameters='#(\n    %s = %s' %(name,val)
                        first=False
                    else:
                        parameters=parameters+',\n    %s = %s' %(name,val)
                parameters=parameters+'\n)'
                self._definition='module %s %s' %(self.name, parameters)
            else:
                self._definition='module %s ' %(self.name)
            first=True
            if self.ios.Members:
                for ioname, io in self.ios.Members.items():
                    if first:
                        self._definition=self._definition+'(\n'
                        first=False
                    else:
                        self._definition=self._definition+',\n'
                    if io.cls in [ 'input', 'output', 'inout' ]:
                        if io.width==1:
                            self._definition=(self._definition+
                                    ('    %s %s' %(io.cls, io.name)))
                        else:
                            self._definition=(self._definition+
                                    ('    %s [%s:%s] %s' %(io.cls, io.ll, io.rl, io.name)))
                    else:
                        self.print_log(type='F', msg='Assigning signal direction %s to verilog module IO.' %(io.cls))
                self._definition=self._definition+'\n)'
            self._definition=self._definition+';'
            if self.contents:
                self._definition=self._definition+self.contents+'\nendmodule'
        return self._definition

    # Instance is defined through the io_signals
    # Therefore it is always regenerated
    @property
    def instance(self):
        '''Instantioation string of the module. Can be used inside of the other modules.

        '''
        #First we write the parameter section
        if self.parameters.Members:
            parameters=''
            first=True
            for name, val in self.parameters.Members.items():
                if first:
                    parameters='#(\n    .%s(%s)' %(name,name)
                    first=False
                else:
                    parameters=parameters+',\n    .%s(%s)' %(name,name)
            parameters=parameters+'\n)'
            self._instance='%s  %s %s' %(self.name, parameters, self.instname)
        else:
            self._instance='%s %s ' %(self.name, self.instname)
        first=True
        # Then we write the IOs
        if self.ios.Members:
            for ioname, io in self.ios.Members.items():
                if first:
                    self._instance=self._instance+'(\n'
                    first=False
                else:
                    self._instance=self._instance+',\n'
                if io.cls in [ 'input', 'output', 'inout' ]:
                        self._instance=(self._instance+
                                ('    .%s(%s)' %(io.name, io.connect.name)))
                else:
                    self.print_log(type='F', msg='Assigning signal direction %s to verilog module IO.' %(io.cls))
            self._instance=self._instance+('\n)')
        self._instance=self._instance+(';\n')
        return self._instance

    #Methods
    def export(self,**kwargs):
        '''Method to export the module to a given file.

        Parameters
        ----------
           **kwargs :

               force: Bool

        '''
        if not os.path.isfile(self.file):
            self.print_log(msg='Exporting verilog_module to %s.' %(self.file))
            with open(self.file, "w") as module_file:
                module_file.write(self.definition)

        elif os.path.isfile(self.file) and not kwargs.get('force'):
            self.print_log(type='F', msg=('Export target file %s exists.\n Force overwrite with force=True.' %(self.file)))

        elif kwargs.get('force'):
            self.print_log(msg='Forcing overwrite of verilog_module to %s.' %(self.file))
            with open(self.file, "w") as module_file:
                module_file.write(self.definition)


if __name__=="__main__":
    pass

