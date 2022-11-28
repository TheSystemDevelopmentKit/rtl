"""
Icarus is a mixin class used to provide simulator specific
properties and methods for RTL class

Initially written by Marko kosunen 20221030
"""

from thesdk import *
class icarus(thesdk,metaclass=abc.ABCMeta):
    @property
    def icarus_rtlcmd(self):
        submission=self.lsf_submission
        os.mkdir(self.rtlworkpath)
        vlogmodulesstring=' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vlogmodulefiles])
        vhdlmodulesstring=' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vhdlentityfiles])
        vlogcompcmd = ( 'iverilog -Wall -v -g2012 -o ' + self.rtlworkpath + '/' + self.name
    	            + ' ' + self.simtb + ' ' + self.simdut + ' ' + vlogmodulesstring)
        gstring=' '.join([ ('-g ' + str(param) +'='+ str(val)) 
            for param,val in iter(self.rtlparameters.items()) ])
        vlogsimargs = ' '.join(self.vlogsimargs)

        fileparams=''
        for name, file in self.iofile_bundle.Members.items():
            fileparams+=' '+file.simparam

        dofile=self.interactive_controlfile
        if os.path.isfile(dofile):
            dostring=' -do "'+dofile+'"'
            self.print_log(type='I',msg='Using interactive control file %s' % dofile)
        else:
            dostring=''
            self.print_log(type='I',msg='No interactive control file set.')

        if not self.interactive_rtl:
            rtlsimcmd = ('vvp -v ' + self.rtlworkpath + '/' + self.name + fileparams + ' ' + gstring)
        else:
            submission="" #Local execution
            rtlsimcmd = ('vvp -v ' + self.rtlworkpath + '/' + self.name
                         + ' && gtkwave -S ' + dofile + ' ' + self.name + '_dump.vcd')

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
        dofilepath = '%s/general.tcl' % dofiledir
        obsoletepath = '%s/Simulations/rtlsim/general.tcl' % self.entitypath
        newdofilepath = '%s/general.tcl' % self.simpath
        return (dofiledir, dofilepath,obsoletepath,newdofilepath)

