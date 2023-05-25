"""
=========
Connector
=========
Class for describing signals in wide sense, including IO's

Written by Marko Kosunen 20190109 marko.kosunen@aalto.fi
"""
import os
from thesdk import *
from rtl.connector_common import connector_common
from rtl.sv.verilog_connector import verilog_connector
from rtl.vhdl.vhdl_connector import vhdl_connector

class rtl_connector(connector_common,thesdk):
    def __init__(self, **kwargs):
        ''' Executes init of module_common, thus having the same attributes and 
        parameters.

        Parameters
        ----------
            **kwargs :
               See module module_common
        
        '''
        super().__init__(**kwargs)

    @property
    def lang(self):
        '''Description language used.

        Default: `sv`

        '''
        if not hasattr(self,'_lang'):
            self._lang='sv'
        return self._lang

    @lang.setter
    def lang(self,value):
            self._lang=value

    @property
    def langobject(self):
        """The language specific operation is defined with an instance of 
        language specific class. Properties and methods return values from that class.
        """
        if not hasattr(self,'_langobject'):
            if self.lang == 'sv':
                self._langobject=verilog_connector(
                        name=self.name,
                        cls=self.cls,
                        type = self.type,
                        ll = self.ll,
                        rl = self.rl,
                        init = self.init,
                        connect = self.connect
                        )
            elif self.lang == 'vhdl':
                self._langobject=vhdl_connector(
                        name=self.name,
                        cls=self.cls,
                        type = self.type,
                        ll = self.ll,
                        rl = self.rl,
                        init = self.init,
                        connect = self.connect
                        )
        return self._langobject

    @property
    def definition(self):
        return self.langobject.definition

    @property
    def ioformat(self):
        return self.langobject.ioformat
    @ioformat.setter
    def ioformat(self,value):
        self.langobject.ioformat = value

    @property
    def assignment(self,**kwargs):
        return self.langobject.assignment

    @property
    def initialization(self,**kwargs):
        return self.langobject.initialization

    def nbassign(self,**kwargs):
        time=kwargs.get('time','')
        value=kwargs.get('value',self.connect.name)
        return self.langobject.nbassign(time=time,value=value)

    def bassign(self):
        time=kwargs.get('time','')
        value=kwargs.get('value',self.connect.name)
        return self.langobject.bassign(time=time,value=value)

class rtl_connector_bundle(Bundle):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

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

    def rtl_inits(self,**kwargs):
        """Initialization strings for the coonectors to be used in creating testbench.

        """
        #[TODO]: Write sanity checks
        inits=''
        match=kwargs.get('match',r".*") #By default, assign all
        for name, val in self.Members.items():
            if re.match(match,name) and ( val.init is not None and val.init != '' ):
                #inits=inits+'%s = %s;\n' %(val.name,val.init)
                inits=inits+val.initialization
        return indent(text=inits, level=kwargs.get('level',0))

    def list(self,**kwargs):
        #[TODO]: Write sanity checks
        names=kwargs.get('names','')
        connectors=[]
        if names:
            for name in names:
                connectors.append(self.Members[name])
        return connectors

class verilog_connector_bundle(rtl_connector_bundle,thesdk):
    def __init__(self,**kwargs):
        super(verilog_connector_bundle,self).__init__(**kwargs)

        msg = 'verilog_connector_bundle class is obsolete. Use rtl_connector_bundle instead'
        typestr = "[OBSOLETE]"
        cviolet = '\33[35m'
        cend    = '\33[0m'
        print("%s %s%s%s %s: %s" %(time.strftime("%H:%M:%S"),cviolet,typestr,cend, 
            self.__class__.__name__ , msg))


    def verilog_inits(self,**kwargs):
        """ Obsolete method to retain backwards compatibility use 'rtl_inits instead'
        """
        #[TODO]: Write sanity checks
        inits=''
        match=kwargs.get('match',r".*") #By default, assign all
        for name, val in self.Members.items():
            if re.match(match,name) and ( val.init is not None and val.init != '' ):
                #inits=inits+'%s = %s;\n' %(val.name,val.init)
                inits=inits+val.initialization
        #self.print_log(type='O', msg = 'verilog_inits is obsolete. Use rtl_inits instead')
        return indent(text=inits, level=kwargs.get('level',0))

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

