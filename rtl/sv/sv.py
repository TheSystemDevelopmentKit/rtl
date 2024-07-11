"""
====================
System verilog class
====================

This mixin class contains all system verilog and verilog related properties that
are used by simulator specific classes.

Initially written by Marko Kosunen 30.10.20200, marko.kosunen@aalto.fi
"""


from thesdk import *
from rtl.rtl_iofile import rtl_iofile as rtl_iofile
class sv(thesdk,metaclass=abc.ABCMeta):

    @property
    def vlogsimtb(self):
        ''' Name of the VHDL testbench
        '''
        return self.rtlsimpath + '/tb_' + self.name + self.vlogext

    @property
    def vlogsrcpath(self):
        ''' Search path for the verilogfiles
            self.entitypath/sv

            Returns
            -------
                self.entitypath/sv


        '''
        if not hasattr(self, '_vlogsrcpath'):
            self._vlogsrcpath  =  self.entitypath + '/sv'
        return self._vlogsrcpath
    #No setter, no deleter.

    @property
    def vlogsrc(self):
        '''Verilog source file
           self.vlogsrcpath/self.name.sv

           Returns
           -------
               self.vlogsrcpath + '/' + self.name + self.vlogext

        '''
        if not hasattr(self, '_vlogsrc'):
            #_classfile is an abstract property that must be defined in the class.
            self._vlogsrc=self.vlogsrcpath + '/' + self.name + self.vlogext
        return self._vlogsrc

    @property
    def vlogext(self):
        ''' File extension for verilog files

            Default is '.sv', but this can be overridden to support, e.g.
            generators like Chisel that always use the '.v' prefix.

        '''
        if not hasattr(self, '_vlogext'):
            self._vlogext = '.sv'
        return self._vlogext
    @vlogext.setter
    def vlogext(self, value):
        self._vlogext = value

    @property
    def vlogcompargs(self):
        ''' List of arguments passed to the simulator
        during the verilog compilation '''
        if not hasattr(self, '_vlogcompargs'):
            self._vlogcompargs = []
        return self._vlogcompargs
    @vlogcompargs.setter
    def vlogcompargs(self, value):
        self._vlogcompargs = value

    @property
    def vlogmodulefiles(self):
        '''List of verilog modules to be compiled in addition of DUT

        '''
        if not hasattr(self, '_vlogmodulefiles'):
            self._vlogmodulefiles =list([])
        return self._vlogmodulefiles
    @vlogmodulefiles.setter
    def vlogmodulefiles(self,value):
            self._vlogmodulefiles = value
    @vlogmodulefiles.deleter
    def vlogmodulefiles(self):
            self._vlogmodulefiles = None

    @property
    def vlogsimargs(self):
        '''Custom parameters for verilog simulation
        Provide as a list of strings
        '''
        if self.sim_optimization:
            self._verilog_sim_args = self.sim_opt_dict[self.sim_optimization]
        else:
            if not hasattr(self,'_verilog_sim_args'):
                self._verilog_sim_args = []
        return self._verilog_sim_args
    @vlogsimargs.setter
    def vlogsimargs(self, simparam):
        self._verilog_sim_args = simparam

    def sv_create_connectors(self):
        '''Cretes verilog connector definitions from
           1) From a iofile that is provided in the Data
           attribute of an IO.
           2) IOS of the verilog DUT

        '''
        # Create TB connectors from the control file
        # See controller.py
        for ioname,io in self.IOS.Members.items():
            # If input is a file, adopt it
            if isinstance(io.Data,rtl_iofile):
                if io.Data.name is not ioname:
                    self.print_log(type='I',
                            msg='Unifying file %s name to ioname %s' %(io.Data.name,ioname))
                    io.Data.name=ioname
                io.Data.adopt(parent=self)
                self.tb.parameters.Members.update(io.Data.rtlparam)

                for connector in io.Data.rtl_connectors:
                    self.tb.connectors.Members[connector.name]=connector
                    # Connect them to DUT
                    try:
                        self.dut.ios.Members[connector.name].connect=connector
                    except:
                        pass
            # If input is not a file, look for corresponding file definition
            elif ioname in self.iofile_bundle.Members:
                val=self.iofile_bundle.Members[ioname]
                for name in val.ionames:
                    # [TODO] Sanity check, only floating inputs make sense.
                    if not name in self.tb.connectors.Members.keys():
                        self.print_log(type='I',
                                msg='Creating non-existent IO connector %s for testbench' %(name))
                        self.tb.connectors.new(name=name, cls='reg')
                self.iofile_bundle.Members[ioname].rtl_connectors=\
                        self.tb.connectors.list(names=val.ionames)
                self.tb.parameters.Members.update(val.rtlparam)
        # Define the iofiles of the testbench. '
        # Needed for creating file io routines
        self.tb.iofiles=self.iofile_bundle

