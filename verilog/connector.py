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
        self.ll=kwargs.get('ll',0)      # Bus range left limit 0 by default
        self.rl=kwargs.get('ll',0)      # Bus bus range right limit 0 by default
        self.init=kwargs.get('init','') # Initial value
        self.connect=kwargs.get('connect',None) # Can be verilog connector, would be recursive
        self._assignment=''
        self._definition=''

    @property
    def width(self):
        self._width=self.ll-self.rl+1
        return self._width

    @property
    def definition(self):
        if self.width==1:
            self._defininition='%s %s;\n' %(self.cls, self.name)
        elif self.type:
            self._definition='%s %s [%s:%s] %s;\n' %(self.cls, self.type, self.ll, self.rl, self.name)
        else:
            self._definition='%s [%s:%s] %s;\n' %(self.cls, self.ll, self.rl, self.name)
        return self._definition
    
    @property
    def assignment(self,**kwargs):
        self._assignment='assign %s = %s;\n' %(self.name,self.connect.name)
        return self._assignment

    def nbassign(self,**kwargs):
        time=kwargs.get('time','')
        value=kwargs.get('value',self.connect.name)
        if time:
            return '%s = #%s %s;\n' %(self.name,time, value)
        else:
            return '%s = %s;\n' %(self.name, value)

    def bassign(self):
        time=kwargs.get('time','')
        value=kwargs.get('value',self.connect.name)
        if time:
            return '%s <= #%s %s;\n' %(self.name,time, value)
        else:
            return '%s <= %s;\n' %(self.name, value)

class verilog_connector_bundle(Bundle):
    def __init__(self,**kwargs):
        super(verilog_connector_bundle,self).__init__(**kwargs)

    def new(self,**kwargs):
        name=kwargs.get('name','')
        cls=kwargs.get('cls','')   # Input,output,inout,reg,wire,reg,wire
        type=kwargs.get('type','') # signed
        ll=kwargs.get('ll',0)      # Bus range left limit 0 by default
        rl=kwargs.get('ll',0)      # Bus bus range right limit 0 by default
        init=kwargs.get('init','') # Initial value
        connect=kwargs.get('connect',None) # Can be verilog connector, would be recursive
        self.Members[name]=verilog_connector(name=name,cls=cls,type=type,ll=ll,rl=rl,init=init,connect=connect)

    def update(self,**kwargs):
        bundle=kwargs.get('bundle',None)
        self.Members.update(bundle)
    
    def mv(self,**kwargs):
        fro=kwargs.get('fro')
        to=kwargs.get('to')
        self.Members[to]=self.Members.pop(fro)
        self.Members[to].name=to

    def connect(self,**kwargs):
        match=kwargs.get('match')
        conname=kwargs.get('connect')
        for name, value in self.Members.items():
            if re.match(match,name):
                value.connect=self.Members[conname]

    def assign(self,**kwargs):
        match=kwargs.get('match')
        assignments=''
        for name, value in self.Members.items():
            if re.match(match,name):
                assignments=assignments+value.assignment
        return assignments

if __name__=="__main__":
    pass

