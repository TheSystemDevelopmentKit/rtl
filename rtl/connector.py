"""
=================
Verilog connector
=================
Class for describing signals in wide sense, including IO's

Written by Marko Kosunen 20190109 marko.kosunen@aalto.fi
"""
import os
from thesdk import *

class verilog_connector(thesdk):
    def __init__(self,**kwargs):
        """
        Parameters
        ----------
        name : str
        cls : str, input | output | inout | reg | wire
            Default ''
        type: str, signed (if not unsigned)
            Default ''
        ll: int, Left limit of a signal bus
            Default: 0
        rl: int, Right limit of a signalbus
            Default: 0
        init: str, initial value
            Default ''
        connect: verilog_connector instance, An connector this conenctor is connected to.
            Default: None
        ioformat: str, Verilog formating string fo the signal for parsing it from a file.
            Default; '%d', i.e parse as integers.
            
        """
        self.name=kwargs.get('name','')
        self.cls=kwargs.get('cls','')   # Input,output,inout,reg,wire
        self.type=kwargs.get('type','') # signed
        self.ll=kwargs.get('ll',0)      # Bus range left limit 0 by default
        self.rl=kwargs.get('rl',0)      # Bus bus range right limit 0 by default
        self.init=kwargs.get('init','') # Initial value
        self.connect=kwargs.get('connect',None) # Can be verilog connector, would be recursive
        self.ioformat=kwargs.get('ioformat','%d')# By default, connectors are handles as integers in file io.

    @property
    def width(self):
        ''' Width of the connector: int | str (for parametrized bounds)'''
            
        if (isinstance(self.ll,str) or isinstance(self.rl,str)):
            self._width=str(self.ll) + '-' + str(self.rl)+'+1'
        else: 
            self._width=int(self.ll)-int(self.rl)+1
        return self._width

    @property
    def definition(self):
        if self.width==1:
            self._definition='%s %s;\n' %(self.cls, self.name)
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
        cls=kwargs.get('cls','')           # Input,output,inout,reg,wire,reg,wire
        type=kwargs.get('type','')         # signed
        ll=kwargs.get('ll',0)              # Bus range left limit 0 by default
        rl=kwargs.get('rl',0)              # Bus bus range right limit 0 by default
        init=kwargs.get('init','')         # Initial value
        connect=kwargs.get('connect',None) # Can't be verilog connector by default. Would be recursive
        self.Members[name]=verilog_connector(name=name,cls=cls,type=type,ll=ll,rl=rl,init=init,connect=connect)

    def update(self,**kwargs):
        #[TODO]: Write sanity checks
        bundle=kwargs.get('bundle',None)
        for key,val in bundle.items():
            if key not in self.Members: 
                self.Members[key]=val
    
    def mv(self,**kwargs):
        #[TODO]: Write sanity checks
        fro=kwargs.get('fro')
        to=kwargs.get('to')
        self.Members[to]=self.Members.pop(fro)
        self.Members[to].name=to

    def connect(self,**kwargs):
        #[TODO]: Write sanity checks
        match=kwargs.get('match',r".*")  #By default, connect all
        conname=kwargs.get('connect')
        for name, value in self.Members.items():
            if re.match(match,name):
                value.connect=self.Members[conname]

    def init(self,**kwargs):
        #[TODO]: Write sanity checks
        match=kwargs.get('match',r".*")  #By default, connect all
        initval=kwargs.get('init','')
        for name, value in self.Members.items():
            if re.match(match,name):
                value.init=initval

    def assign(self,**kwargs):
        #[TODO]: Write sanity checks
        match=kwargs.get('match',r".*") #By default, assign all
        assignments=''
        for name, value in self.Members.items():
            if re.match(match,name):
                assignments=assignments+value.assignment
        return indent(text=assignments, level=kwargs.get('level',0))

    def verilog_inits(self,**kwargs):
        #[TODO]: Write sanity checks
        inits=''
        match=kwargs.get('match',r".*") #By default, assign all
        for name, val in self.Members.items():
            if re.match(match,name) and ( val.init is not None and val.init != '' ):
                inits=inits+'%s = %s;\n' %(val.name,val.init)
        return indent(text=inits, level=kwargs.get('level',0))

    def list(self,**kwargs):
        #[TODO]: Write sanity checks
        names=kwargs.get('names','')
        connectors=[]
        if names:
            for name in names:
                connectors.append(self.Members[name])
        return connectors

#Helper to indent text blocks
def indent(**kwargs):
    '''
    Helper for indenting text blocks
    Also adds a newline after every line (including last one)
    Parameters
    -----------
    **kwargs : 
        text  : text to indent (may allow line breaks)
        level : level of indent (level * 4 spaces will be added to each row)
    '''
    text = kwargs.get('text', '')
    nspaces = 4
    level = kwargs.get('level', 0)
    textout=''
    for line in text.splitlines():
        spaces = ' ' * nspaces*level
        textout += spaces+line+'\n'
    return textout

# Support the old name for backwards compatibility
def intend(**kwargs):
    return indent(**kwargs)


if __name__=="__main__":
    pass

