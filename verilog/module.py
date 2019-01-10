# Written by Marko Kosunen 20190109
# marko.kosunen@aalto.fi
import os
from thesdk import *
from verilog import *
from copy import deepcopy
from verilog.signal import verilog_signal

class verilog_module(thesdk):
    # Idea  1) Collect IO's to database
    #       3) Reconstruct the module definition
    #       4) Create a method to create assigned module
    #          definition, where signals are
    #          a) assigned by name
    #          b) to arbitrary name vector
    def __init__(self, **kwargs):
        self.file=kwargs.get('file','')

    @property
    def name(self):
        if not hasattr(self,'_name'):
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
                        #By default, we connect to the wire of same name than the input
                        signal.connect=signal.name
                        self._ios.append(signal)
        return self._ios

    # The names and widths are defined by the module file,
    # only connects and inits can be redefined
    @ios.setter
    def ios(self,value):
        self._ios=copy(value)

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
        return self._definition

    # Instance is defined through the io_signals
    # Therefore it is always regenerated
    @property
    def instance(self):
        self._instance='%s %s ( ' %(self.name, self.instname)
        first=True
        for i in range(len(self.ios)):
            if first:
                self._instance=self._instance+'\n'
                first=False
            else:
                self._instance=self._instance+',\n'
            if self.ios[i].dir in [ 'input', 'output', 'inout' ]:
                    self._instance=(self._instance+
                            ('    .%s(%s)' %(self.ios[i].name, self.io_signals[i].name)))
            else:
                self.print_log({'type':'F', 'msg':'Assigning signal direction %s to verilog module IO.' %(io.dir)})
        self._instance=self._instance+('\n);')
        return self._instance

if __name__=="__main__":
    pass
