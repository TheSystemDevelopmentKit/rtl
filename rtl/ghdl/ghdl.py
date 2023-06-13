"""
GHDL is a mixin class used to provide simulator specific
properties and methods for RTL class

Initially written by Marko Kosunen 20230610
"""

from thesdk import *
class ghdl(thesdk):
    @property
    def ghdl_rtlcmd(self):
        submission=self.lsf_submission
        if not os.path.exists(self.rtlworkpath):
            os.mkdir(self.rtlworkpath)
        vlogmodulesstring=' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vlogmodulefiles])
        vhdlmodulesstring=' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vhdlentityfiles])

        if vlogmodulesstring != '':
            self.print_log(type='W', msg="GHDL does not support Verilog+VHDL cosimulation, ignoring additional Verilog files.")
        # We need to compile VHDL source and testbench anyway
        vhdlcompcmd = ( 'ghdl -a -Wall --std=08 ' + ' ' + vhdlmodulesstring 
                + ' ' + self.simdut + ' ' + self.simtb )
        vhdlanalysiscmd = ( 'ghdl -e --std=08 ' 'tb_' + self.name )


        gstring = ' '.join([ 
                                ('-g ' + str(param) +'='+ str(val[1])) 
                                for param,val in self.rtlparameters.items() 
                            ])
        vhdlsimargs = ' '.join(self.vhdlsimargs)

        fileparams=''
        for name, file in self.iofile_bundle.Members.items():
            fileparams+=' '+file.simparam

        controlfile=self.simulator_controlfile
        if os.path.isfile(controlfile):
            controlstring=' --read-wave-opt="'+controlfile+'"'
            self.print_log(type='I',msg='Using interactive control file %s' % controlfile)
        else:
            controlstring=''
            self.print_log(type='I',msg='No simulator control file set.')

        interactive_controlfile=self.interactive_controlfile
        if os.path.isfile(interactive_controlfile):
            interactive_string=' -S "'+interactive_controlfile+'"'
            self.print_log(type='I',msg='Using interactive control file %s' % interactive_controlfile)
        else:
            interactive_string=''
            self.print_log(type='I',msg='No interactive control file set.')

        if not self.interactive_rtl:
            rtlsimcmd = ('ghdl -r --std=08 ' + controlstring + ' tb_' + self.name)
        else:
            submission="" #Local execution
            rtlsimcmd = ('ghdl -r --std=08 ' + 'tb_' + self.name + controlstring + ' --vcd='+self.name +'_dump.vcd'
                         + ' && gtkwave ' + interactive_string + ' ' + self.name + '_dump.vcd')

        self._rtlcmd =  vhdlcompcmd +\
                ' && sync ' + self.rtlworkpath +\
                ' && ' + submission +\
                rtlsimcmd

        return self._rtlcmd

    @property
    def ghdl_simdut(self):
        ''' Source file for Device Under Test in simulations directory

            Returns
            -------
                self.rtlsimpath + self.name + self.vlogext for 'sv' model
                self.rtlsimpath + self.name + '.vhd' for 'vhdl' model
        '''
        # Icarus supports only verilog
        extension = self.vhdlext
        self._simdut = os.path.join(self.rtlsimpath, self.name+extension)
        return self._simdut

    @property
    def ghdl_simtb(self):
        ''' Icarus Testbench source file in simulations directory.

        This file and it's format is dependent on the language(s)
        supported by the simulator. Currently we have support only for verilog testbenches.

        '''
        self._simtb=self.rtlsimpath + '/tb_' + self.name + self.vhdlext
        return self._simtb
    
    @property
    def ghdl_dofilepaths(self):
        dofiledir = '%s/interactive_control_files/gtkwave' % self.entitypath
        dofile = '%s/general.tcl' % dofiledir
        obsoletedofile = '%s/Simulations/rtlsim/general.tcl' % self.entitypath
        generateddofile = '%s/general.tcl' % self.simpath
        return (dofiledir, dofile,obsoletedofile,generateddofile)

    @property
    def ghdl_controlfilepaths(self):
        controlfiledir = '%s/interactive_control_files/ghdl' % self.entitypath
        controlfile = '%s/general.tcl' % controlfiledir
        generatedcontrolfile = '%s/wave.opt' % self.simpath
        return (controlfiledir, controlfile, generatedcontrolfile)

