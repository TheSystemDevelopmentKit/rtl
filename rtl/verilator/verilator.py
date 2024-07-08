"""
=========
Verilator
=========
Verilator is a mixin class used to provide simulator specific
properties and methods for RTL class

Initially written by Aleksi Korsman, 2022
"""

from thesdk import *
import pdb

class verilator(thesdk,metaclass=abc.ABCMeta):
    @property
    def verilator_rtlcmd(self):
        submission=self.lsf_submission
        if not os.path.exists(self.rtlworkpath):
            os.mkdir(self.rtlworkpath)
        vlogmodulesstring=' '.join(self.vloglibfilemodules + [ self.rtlsimpath + '/'+ 
            str(param) for param in self.vlogmodulefiles ])
        vhdlmodulesstring=' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vhdlentityfiles])

        if vhdlmodulesstring != '':
            self.print_log(type='W', msg="Verilator does not support Verilog+VHDL cosimulation, ignoring additional VHDL files.")


        vlogcompcmd = ( 'verilator -Wall --Wno-lint --binary --trace --timing --Mdir ' + self.rtlworkpath +
                ' ' + self.simtb + ' ' + self.simdut + ' ' + vlogmodulesstring )
        gstring = ' '.join([ 
                                ('-G ' + str(param) +'='+ str(val[1])) 
                                for param,val in self.rtlparameters.items() 
                            ])

        # Still dont know what to do with these.
        vlogsimargs = ' '.join(self.vlogsimargs)

        fileparams=''
        for name, file in self.iofile_bundle.Members.items():
            fileparams+=' '+file.simparam


        if self.interactive_rtl:
            submission="" #Local execution
            dofile=self.interactive_controlfile
            if os.path.isfile(dofile):
                dostring=' -S "'+dofile+'"'
                self.print_log(type='I',msg='Using interactive control file %s' % dofile)
            else:
                dostring=''
                self.print_log(type='I',msg='No interactive control file set.')
            rtlsimcmd = ('cd '+ self.rtlworkpath + ' && ' + './Vtb_'+ self.name 
                         + ' && gtkwave ' + dostring + ' ' + self.rtlsimpath + '/' + self.name + '_dump.vcd')
        else:
            rtlsimcmd = ('cd '+ self.rtlworkpath + ' &&  ./Vtb_' + self.name )

        self._rtlcmd =  vlogcompcmd +\
                ' && sync ' + self.rtlworkpath +\
                ' && ' + submission +\
                rtlsimcmd

        return self._rtlcmd

    @property
    def verilator_simdut(self):
        ''' Source file for Device Under Test in simulations directory

            Returns
            -------
                self.rtlsimpath + self.name + self.vlogext for 'sv' model
                self.rtlsimpath + self.name + '.vhd' for 'vhdl' model
        '''
        extension = None
        # Verilator supports only verilog
        extension = self.vlogext
        self._simdut = os.path.join(self.rtlsimpath, self.name+extension)
        print(self.simdut)
        return self._simdut

    @property
    def verilator_simtb(self):
        ''' Verilator Testbench source file in simulations directory.

        This file and it's format is dependent on the language(s)
        supported by the simulator. Verilator supports verilog testbenches

        '''
        self._simtb=self.rtlsimpath + '/tb_' + self.name + self.vlogext
        return self._simtb
    
    @property
    def verilator_dofilepaths(self):
        dofiledir = '%s/interactive_control_files/gtkwave' % self.entitypath
        dofile = '%s/general.tcl' % dofiledir
        obsoletedofile = '%s/Simulations/rtlsim/general.tcl' % self.entitypath
        generateddofile = '%s/general.tcl' % self.simpath
        return (dofiledir, dofile, obsoletedofile,generateddofile)

    @property
    def verilator_controlfilepaths(self):
        controlfiledir = '%s/interactive_control_files/verilator' % self.entitypath
        controlfile = '%s/control.tcl' % controlfiledir
        generatedcontrolfile = '%s/control.tcl' % self.simpath
        return (controlfiledir, controlfile, generatedcontrolfile)

