"""
Icarus is a mixin class used to provide simulator specific
properties and methods for RTL class

Initially written by Marko kosunen 20221030
"""

from thesdk import *
import pdb
class icarus(thesdk,metaclass=abc.ABCMeta):
    @property
    def icarus_rtlcmd(self):
        submission=self.lsf_submission
        if not os.path.exists(self.rtlworkpath):
            os.mkdir(self.rtlworkpath)
        vlogmodulesstring=' '.join(self.vloglibfilemodules + [ self.rtlsimpath + '/'+ 
            str(param) for param in self.vlogmodulefiles ])
        vhdlmodulesstring=' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vhdlentityfiles])

        if vhdlmodulesstring != '':
            self.print_log(type='W', msg="Icarus does not support Verilog+VHDL cosimulation, ignoring additional VHDL files.")

        vlogcompcmd = ( 'iverilog -Wall -v -g2012 -o ' + self.rtlworkpath + '/' + self.name
                    + ' ' + vlogmodulesstring)
        gstring = ' '.join([ 
                                ('-g ' + str(param) +'='+ str(val[1])) 
                                for param,val in self.rtlparameters.items() 
                            ])
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
            rtlsimcmd = ('vvp -v ' + self.rtlworkpath + '/' + self.name
                         + ' && gtkwave ' + dostring + ' ' + self.rtlsimpath + '/' + self.name + '_dump.vcd')
        else:
            rtlsimcmd = ('vvp -v ' + self.rtlworkpath + '/' + self.name + fileparams + ' ' + gstring)

        self._rtlcmd =  vlogcompcmd +\
                ' && sync ' + self.rtlworkpath +\
                ' && ' + submission +\
                rtlsimcmd

        return self._rtlcmd

    @property
    def icarus_simdut(self):
        ''' Source file for Device Under Test in simulations directory

            Returns
            -------
                self.rtlsimpath + self.name + self.vlogext for 'sv' model
                self.rtlsimpath + self.name + '.vhd' for 'vhdl' model
        '''
        extension = None
        # Icarus supports only verilog
        extension = self.vlogext
        self._simdut = os.path.join(self.rtlsimpath, self.name+extension)
        print(self.simdut)
        return self._simdut

    @property
    def icarus_simtb(self):
        ''' Icarus Testbench source file in simulations directory.

        This file and it's format is dependent on the language(s)
        supported by the simulator. Currently we have support only for verilog testbenches.

        '''
        self._simtb=self.rtlsimpath + '/tb_' + self.name + self.vlogext
        return self._simtb
    
    @property
    def icarus_dofilepaths(self):
        dofiledir = '%s/interactive_control_files/gtkwave' % self.entitypath
        dofile = '%s/general.tcl' % dofiledir
        obsoletedofile = '%s/Simulations/rtlsim/general.tcl' % self.entitypath
        generateddofile = '%s/general.tcl' % self.simpath
        return (dofiledir, dofile, obsoletedofile,generateddofile)

    @property
    def icarus_controlfilepaths(self):
        controlfiledir = '%s/interactive_control_files/icarus' % self.entitypath
        controlfile = '%s/control.tcl' % controlfiledir
        generatedcontrolfile = '%s/control.tcl' % self.simpath
        return (controlfiledir, controlfile, generatedcontrolfile)

