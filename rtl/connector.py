"""
=========
Connector
=========
Class for describing signals in wide sense, including IO's

This class stores signal parameters as name, type widt and indexes, and
returns definition strings according to given 'lang' paramenter

Written by Marko Kosunen 20190109 marko.kosunen@aalto.fi
"""
import os
from thesdk import *
from rtl.sv.verilog_connector import verilog_connector
from rtl.vhdl.vhdl_connector import vhdl_connector

class rtl_connector(thesdk):
    def __init__(self, **kwargs):
        ''' Executes init of module_common, thus having the same attributes and
        parameters.

        Parameters
        ----------
            **kwargs :
               See module module_common

        '''


    def __init__(self,**kwargs):
        """
        Parameters
        ----------
        name : str
        cls : str, input | output | inout | reg | wire
            Default ''
        type: str, For verilog: signed, unsigned for VHDL: std_logic, std_logic-vector
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
        self._name=kwargs.get('name','')
        self._lang=kwargs.get('lang','sv')
        self._cls=kwargs.get('cls','')   # Input,output,inout,reg,wire
        self._ll=kwargs.get('ll',0)      # Bus range left limit 0 by default
        self._rl=kwargs.get('rl',0)      # Bus bus range right limit 0 by default
        self._init=kwargs.get('init','') # Initial value
        self._connect=kwargs.get('connect',None) # Can be another connector, would be recursive
        self._typearg=kwargs.get('type','') # signed

    @property
    def name(self):
        '''Name of the connector

        '''
        if not hasattr(self,'_name'):
            self._name=''
        return self._name

    @name.setter
    def name(self,value):
            self._name=value

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
    def cls(self):
        '''Class of the connector

        str : Input | output | reg | wire

        '''
        if not hasattr(self,'_cls'):
            self._cls='sv'
        return self._cls

    @cls.setter
    def cls(self,value):
            self._cls=value

    @property
    def ll(self):
        ''' Left (usually upper) limit of the connector bus: int | str (for parametrized bounds)

        Strings that evaluate to integers are automatically evaluated.

        '''

        if not hasattr(self,'_ll'):
            self._ll = 0
        return self._ll
    @ll.setter
    def ll(self,value):
        if type(value) == str:
            #Try to evaluate string
            try:
                self._ll = eval(value)
            except:
                self._ll = value
        else:
            self._ll = value
        return self._ll

    @property
    def rl(self):
        ''' Right (usually lower) limit of the connector bus: int | str (for parametrized bounds)

        Strings that evaluate to integers are automaticarly evaluated.

        '''

        if not hasattr(self,'_rl'):
            self._rl=0
        return self._rl
    @rl.setter
    def rl(self,value):
        if type(value) == str:
            #Try to evaluate string
            try:
                self._rl = eval(value)
            except:
                self._rl = value
        else:
            self._rl = value
        return self._rl

    @property
    def init(self):
        '''Initial value of the signal at the time instace 0

        Default: '' , meaning undefined.

        '''
        if not hasattr(self,'_init'):
            self._init = ''
        return self._init
    @init.setter
    def init(self,value):
            self._init = value

    @property
    def connect(self):
        '''Connector of different name to which this connector is to be connected to.

        Default: None.

        '''
        if not hasattr(self,'_connect'):
            self._connect = None
        return self._connect
    @connect.setter
    def connect(self,value):
            self._connect = value


    @property
    def width(self):
        ''' Width of the connector: int | str (for parametrized bounds)'''

        if (isinstance(self.ll,str) or isinstance(self.rl,str)):
            self._width=str(self.ll) + '-' + str(self.rl)+'+1'
        else:
            self._width=int(self.ll)-int(self.rl)+1
        return self._width

    @property
    def langobject(self):
        """The language specific operation is defined with an instance of
        language specific class. Properties and methods return values from that class.

        Two instances are created to have the lanquage dependent content available
        in both languages for mixed lanquage simulations. This can be further clarified later,
        as the strings returned should not be fixed at creation.
        """
        if not hasattr(self,'_verilog_langobject'):
            self._verilog_langobject=verilog_connector(
                        parent=self,
                        type = self._typearg,
                        )
        if not hasattr(self,'_vhdl_langobject'):
            self._vhdl_langobject=vhdl_connector(
                        parent=self,
                        type = self._typearg,
                        )
        if self.lang == 'sv':
            return self._verilog_langobject
        if self.lang == 'vhdl':
            return self._vhdl_langobject

    @property
    def type(self):
        return self.langobject.type
    @type.setter
    def type(self,value):
        self.langobject.type = value

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

    def bassign(self, **kwargs):
        time=kwargs.get('time','')
        value=kwargs.get('value',self.connect.name)
        return self.langobject.bassign(time=time,value=value)

class rtl_connector_bundle(Bundle):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.lang=kwargs.get('lang','sv')

    @property
    def lang(self):
        '''Description language used.

        Default: `sv`

        '''
        if not hasattr(self,'_lang'):
            self._lang='sv'
        return self._lang
    @lang.setter
    def lang(self,val):
        self._lang = val


    def new(self,**kwargs):
        name=kwargs.get('name','')
        cls=kwargs.get('cls','')           # Input,output,inout,reg,wire,reg,wire
        type=kwargs.get('type','')         # signed
        ll=kwargs.get('ll',0)              # Bus range left limit 0 by default
        rl=kwargs.get('rl',0)              # Bus bus range right limit 0 by default
        init=kwargs.get('init','')         # Initial value
        connect=kwargs.get('connect',None) # Can't be verilog connector by default. Would be recursive
        self.Members[name]=rtl_connector(lang=self.lang,name=name,cls=cls,type=type,ll=ll,rl=rl,init=init,connect=connect)

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
            if re.fullmatch(match,name):
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

