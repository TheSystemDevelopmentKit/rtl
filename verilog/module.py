# Written by Marko Kosunen 20190109
# marko.kosunen@aalto.fi
import os
from thesdk import *
from verilog import *
from copy import deepcopy
from verilog.signal import verilog_signal

class verilog_module(thesdk):
    # Idea  1) a) Collect IO's to database
    #          b) collect parameters to dict
    #       2) Reconstruct the module definition
    #       3) a) Implement methods provide sinal connections
    #          b) Implement methods to provide parameter assingments   
    #       4) Create a method to create assigned module
    #          definition, where signals are
    #          a) assigned by name
    #          b) to arbitrary name vector
    #       5) Add contents, if required, and include that to definition
    def __init__(self, **kwargs):
        # No need to propertize these yet
        self.file=kwargs.get('file','')
        self._name=kwargs.get('name','')
        if not self.file and not self._name:
            self.print_log({'type':'F', 'msg':'Either name or file must be defined'})
    
    #Name derived from the file
    @property
    def name(self):
        if not self._name:
            self._name=os.path.splitext(os.path.basename(self.file))[0]
        return self._name

    @property
    def instname(self):
        if not hasattr(self,'_instname'):
            self._instname=self.name+'_DUT'
        return self._instname
    @instname.setter
    def instname(self,value):
            self._instname=value

    @property
    def ios(self):
        if not hasattr(self,'_ios'):
            startmatch=re.compile(r"module *(?="+self.name+r")\s*"+r".*.+$")
            iomatch=re.compile(r".*(?<!#)\(.*$")
            iostopmatch=re.compile(r'.*\);\s*$')
            dut=''
            # Extract the module definition
            with open(self.file) as infile:
                wholefile=infile.readlines()
                modfind=False
                iofind=False
                for line in wholefile:
                    if (not modfind and startmatch.match(line)):
                        modfind=True
                    if modfind and iomatch.match(line):
                            iofind=True
                    if ( modfind and iofind and iostopmatch.match(line)):
                        modfind=False
                        iofind=False
                        #Inclusive
                        dut=dut+line +'\n'
                    elif modfind and iofind:
                        dut=dut+line
                dut=dut.replace("\n","")
                #Generate lambda functions for pattern filtering
                fils=[
                    re.compile(r"module\s*"+self.name+r"\s*"),
                    re.compile(r"\("),
                    re.compile(r"\)"),
                    re.compile(r"^\s*"),
                    re.compile(r"\s*(?=> )"),
                    re.compile(r";.*"),
                    re.compile(r";.*")
                  ]
                func_list= [lambda s,fil=x: re.sub(fil,"",s) for x in fils]
                self._ios=[]
                dut=reduce(lambda s, func: func(s), func_list, dut)
                dut=re.sub(r",\s*",",",dut)
                for ioline in dut.split(','):
                    extr=ioline.split()
                    signal=verilog_signal()
                    signal.dir=extr[0]
                    if len(extr)==2:
                        signal.name=extr[1]
                    elif len(extr)==3:
                        signal.name=extr[2]
                        busdef=re.match(r"^.*\[(\d+):(\d+)\]",extr[1])
                        signal.ll=int(busdef.group(1))
                        signal.rl=int(busdef.group(2))
                    #By default, we connect to the wire of same name than the input
                    signal.connect=signal.name
                    self._ios.append(signal)
        return self._ios

    # Setting principle, assign a dict
    # individual parameters can be set externally
    @ios.setter
    def ios(self,value):
        self._ios=deepcopy(value)

    @property
    def parameters(self):
        if not hasattr(self,'_parameters'):
            startmatch=re.compile(r"module *(?="+self.name+r")\s*"+r".*.+$")
            parammatch=re.compile(r".*(?<=#)\(.*$")
            paramstopmatch=re.compile(r".*\).*$")
            parablock=''
            # Extract the module definition
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
                        line=re.sub(r"\).*$","",line)
                        #Inclusive
                        parablock=parablock+line +'\n'
                    elif modfind and parafind:
                        parablock=parablock+line
                #Generate lambda functions for pattern filtering
                parablock.replace("\n","")
                fils=[
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
                self._parameters=dict([])
                for param in parablock:
                        extr=param.split('=')
                        self._parameters[extr[0]]=extr[1]
        return self._parameters

    # Setting principle, assign a dict
    # individual parameters can be set externally
    @parameters.setter
    def parameters(self,value):
        self._parameters=deepcopy(value)

    @property
    def contents(self):
        if not hasattr(self,'_contents'):
            startmatch=re.compile(r"module *(?="+self.name+r")\s*"+r".*.+$")
            headerstopmatch=re.compile(r".*\);.*$")
            modulestopmatch=re.compile(r"\s*endmodule\s*$")
            self._contents='\n'
            # Extract the module definition
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
        if not hasattr(self,'_io_signals'):
            self._io_signals=deepcopy(self.ios)
            for io in self._io_signals:
                if io.dir=='input':
                    io.dir='reg'
                if io.dir=='output':
                    io.dir='wire'
        return self._io_signals
    @io_signals.setter
    def io_signals(self,value):
        for i in range(len(self._io_signals)):
            self._io_signals[i].connect=value[i].connect
        return self._io_signals

    @property
    def definition(self):
        if not hasattr(self,'_definition'):
            #First we print the parameter section
            print(self.parameters)
            if self.parameters :
                parameters=''
                first=True
                for name, val in self.parameters.items():
                    if first:
                        parameters='#(\n    %s = %s' %(name,val)
                        first=False
                    else:
                        parameters=parameters+',\n    %s = %s' %(name,val)
                parameters=parameters+'\n)'
                self._definition='module %s  %s ( ' %(self.name, parameters)
            else:
                self._definition='module %s ( ' %(self.name)
            first=True
            for io in self.ios:
                if first:
                    self._definition=self._definition+'\n'
                    first=False
                else:
                    self._definition=self._definition+',\n'
                if io.dir in [ 'input', 'output', 'inout' ]:
                    if io.width==1:
                        self._definition=(self._definition+
                                ('    %s %s' %(io.dir, io.name)))
                    else:
                        self._definition=(self._definition+
                                ('    %s [%s:%s] %s' %(io.dir, io.ll, io.rl, io.name)))
                else:
                    self.print_log({'type':'F', 'msg':'Assigning signal direction %s to verilog module IO.' %(io.dir)})
            self._definition=self._definition+('\n);')
            if self.contents:
                self._definition=self._definition+self.contents+'\nendmodule'
        return self._definition

    # Instance is defined through the io_signals
    # Therefore it is always regenerated
    @property
    def instance(self):
        #First we write the parameter section
        if self.parameters :
            parameters=''
            first=True
            for name, val in self.parameters.items():
                if first:
                    parameters='#(\n    .%s(%s)' %(name,val)
                    first=False
                else:
                    parameters=parameters+',\n    .%s(%s)' %(name,val)
            parameters=parameters+'\n)'
            self._instance='%s  %s %s ( ' %(self.name,self.instname, parameters)
        else:
            self._instance='%s %s ( ' %(self.name, self.instname)
        first=True
        # Then we write the IOs
        for i in range(len(self.ios)):
            if first:
                self._instance=self._instance+'\n'
                first=False
            else:
                self._instance=self._instance+',\n'
            if self.ios[i].dir in [ 'input', 'output', 'inout' ]:
                    self._instance=(self._instance+
                            ('    .%s(%s)' %(self.ios[i].name, self.ios[i].connect)))
            else:
                self.print_log({'type':'F', 'msg':'Assigning signal direction %s to verilog module IO.' %(io.dir)})
        self._instance=self._instance+('\n);')
        return self._instance

if __name__=="__main__":
    pass
