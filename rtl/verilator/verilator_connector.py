import os
from thesdk import *
from rtl.connector import verilog_connector, verilog_connector_bundle


class verilator_connector(thesdk):
    """Verilator connector. Maintains the same properties as verilog connector, but
    redefines some of the methods.

    The connector can be provided as it would for a Verilog tb with Questa, or it can be 
    directly provided in C++ types

    Name : signal name
    cls  : signal type ()
    
    """
    @property
    def _classfile(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

    def __init__(self,**kwargs):
        self.name=kwargs.get('name','')
        self._cls=kwargs.get('cls','')  # Input,output,inout,reg,wire,reg,wire
        self.type=kwargs.get('type','') # signed
        self.ll=kwargs.get('ll',0)      # Bus range left limit 0 by default
        self.rl=kwargs.get('rl',0)      # Bus bus range right limit 0 by default
        self.init=kwargs.get('init','') # Initial value
        self.connect=kwargs.get('connect',None) # Can be verilog connector, would be recursive
        self.ioformat=kwargs.get('ioformat','%d')# By default, connectors are handles as integers in file io.
        self._cls = self.verilate_cls(self._cls)

    @property
    def cls(self):
        return self._cls
    @cls.setter
    def cls(self, value):
        self._cls = self.verilate_cls(value)
        return self._cls

    def verilate_cls(self, cls):
        """Transfers verilog type to C++ type.
        C++ does not know "registers" or "wires", thus everything is a C++ datatype

        """
        bits = 1
        unsigned = 'u'
        if self.width <= 1:
            bits = 1
        elif self.width <= 8:
            bits = 8
        elif self.width <= 16:
            bits = 16
        elif self.width <= 32:
            bits = 32
        elif self.width <= 64:
            bits = 64
        else:
            self.print_log(cls='F', msg="Our Verilator interface cannot handle more bits than 64 for now")

        if self.type == 'signed':
            unsigned = ''

        final = 'bool'
        if bits > 1:
            final = unsigned + 'int' + str(bits) + '_t'

        return final 

        #if cls in ['bit', '']:
        #    return 'bool'
        #elif cls == 'byte':
        #    return 'int8_t'
        #elif cls == 'shortint':
        #    return 'int16_t'
        #elif cls in ['int', 'integer']:
        #    return 'int32_t'
        #elif cls == 'longint':
        #    return 'int64_t'
        #elif cls == 'time':
        #    return 'uint64_t'
        #elif cls == 'shortreal':
        #    return 'float'
        #elif cls == 'real':
        #    return 'double'
        #elif cls == 'realtime':
        #    return 'double'
        #elif cls == 'string':
        #    return 'string'
        #else:
        #    self.print_log(cls='I', msg='Unknown type, assuming it is C++ type: %s' % cls)
        #    return cls

    @property
    def width(self):
        ''' Width of the connector: int
        ''' 
        self._width=int(self.ll)-int(self.rl)+1
        return self._width

    @property
    def definition(self):
        self._definition='%s %s;\n' %(self.cls, self.name)
        return self._definition

    @property
    def assignment(self, **kwargs):
        self._assignment = '%s = %s;\n' % (self.name, self.connect.name)
        return self._assignment

    def nbassign(self,**kwargs):
        time=kwargs.get('time','')
        value=kwargs.get('value',self.connect.name)
        if time:
            return '%s = #%s %s;\n' %(self.name,time, value)
        else:
            return '%s = %s;\n' %(self.name, value)

    def bassign(self, **kwargs):
        time=kwargs.get('time','')
        value=kwargs.get('value',self.connect.name)
        if time:
            return '%s <= #%s %s;\n' %(self.name,time, value)
        else:
            return '%s <= %s;\n' %(self.name, value)

class verilator_connector_bundle(Bundle):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def new(self,**kwargs):
        name=kwargs.get('name','')
        cls=kwargs.get('cls','')           # Input,output,inout,reg,wire,reg,wire
        type=kwargs.get('type','')         # signed
        ll=kwargs.get('ll',0)              # Bus range left limit 0 by default
        rl=kwargs.get('rl',0)              # Bus bus range right limit 0 by default
        init=kwargs.get('init','')         # Initial value
        connect=kwargs.get('connect',None) # Can't be verilog connector by default. Would be recursive
        self.Members[name]=verilator_connector(name=name,cls=cls,type=type,ll=ll,rl=rl,init=init,connect=connect)

    def update(self,**kwargs):
        #[TODO]: Write sanity checks
        bundle=kwargs.get('bundle',None)
        self.Members.update(bundle)
    
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
        return intend(text=assignments, level=kwargs.get('level',0))

    def verilog_inits(self,**kwargs):
        #[TODO]: Write sanity checks
        inits=''
        match=kwargs.get('match',r".*") #By default, assign all
        for name, val in self.Members.items():
            if re.match(match,name) and ( val.init is not None and val.init is not '' ):
                inits=inits+'%s = %s;\n' %(val.name,val.init)
        return intend(text=inits, level=kwargs.get('level',0))

    def list(self,**kwargs):
        #[TODO]: Write sanity checks
        names=kwargs.get('names','')
        connectors=[]
        if names:
            for name in names:
                connectors.append(self.Members[name])
        return connectors

#Helper to intend text blocks
def intend(**kwargs):
    textout=''
    nspaces=4
    for line in (kwargs.get('text')).splitlines():
        for _ in range(nspaces*kwargs.get('level')):
            line=line+' '
        textout=textout+line+'\n'
    return textout

if __name__=="__main__":
    pass
