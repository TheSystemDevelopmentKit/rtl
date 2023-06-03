"""
Questasim is a mixin class it is used to provide simulator specific
properties and methods for RTL class

Initially written by Marko kosunen 20221030
"""
from thesdk import *
class questasim(thesdk,metaclass=abc.ABCMeta):
    @property
    def questasim_svcmd(self):
        submission=self.lsf_submission
        rtllibcmd =  'vlib ' +  self.rtlworkpath
        rtllibmapcmd = 'vmap work ' + self.rtlworkpath

        # Additional sources
        vlogmodulesstring=' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vlogmodulefiles])
        vhdlmodulesstring=' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vhdlentityfiles])

        # If there are additional VHDL source files, handle as co-simulation
        cosim = vhdlmodulesstring != ''
        
        vlogcompcmd = ( 'vlog -sv -work work ' + vlogmodulesstring 
                + ' ' + self.simdut + ' ' + self.simtb + ' ' + ' '.join(self.vlogcompargs))

        vhdlcompcmd = ( 'vcom -2008 -work work ' + ' ' + vhdlmodulesstring + ' ' + ' '.join(self.vhdlcompargs))
                       

        gstring = ' '.join([ 
                                ('-g ' + str(param) +'='+ str(val[1])) 
                                for param,val in self.rtlparameters.items() 
                            ])
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
            if dostring == '':
                dostring=' -do "run -all; quit;"'

            rtlsimcmd = ( 'vsim -64 -batch -t ' + self.rtl_timescale + ' -voptargs=+acc ' 
                    + fileparams + ' ' + gstring
                    + ' ' + vlogsimargs + ' work.tb_' + self.name  
                    + dostring)
        else:
            submission = ''
            rtlsimcmd = ( 'vsim -64 -t ' + self.rtl_timescale + ' -novopt ' + fileparams 
                    + ' ' + gstring + ' ' + vlogsimargs + ' work.tb_' + self.name + dostring )

        self._rtlcmd =  rtllibcmd  +\
                ' && ' + rtllibmapcmd +\
                ((' && ' + vhdlcompcmd) if cosim else '') +\
                ' && ' + vlogcompcmd +\
                ' && sync ' + self.rtlworkpath +\
                ' && ' + submission +\
                rtlsimcmd
        return self._rtlcmd

    @property
    def questasim_vhdlcmd(self):
        submission = self.lsf_submission
        rtllibcmd =  'vlib ' +  self.rtlworkpath
        rtllibmapcmd = 'vmap work ' + self.rtlworkpath
        vlogmodulesstring =' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vlogmodulefiles])
        vhdlmodulesstring =' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vhdlentityfiles])
        vlogcompcmd = ( 'vlog -sv -work work ' + vlogmodulesstring 
                + ' ' + self.simtb )
        vhdlcompcmd = ( 'vcom -2008 -work work ' + ' ' +
                       vhdlmodulesstring + ' ' + self.vhdlsrc )
        gstring = ' '.join([ 
                                ('-g ' + str(param) +'='+ str(val[1])) 
                                for param,val in self.rtlparameters.items() 
                            ])
        vlogsimargs = ' '.join(self.vlogsimargs)

        fileparams = ''
        for name, file in self.iofile_bundle.Members.items():
            fileparams += ' '+file.simparam

        dofile=self.interactive_controlfile
        if os.path.isfile(dofile):
            dostring=' -do "'+dofile+'"'
            self.print_log(type='I',msg='Using interactive control file %s' % dofile)
        else:
            dostring=''
            self.print_log(type='I',msg='No interactive control file set.')

        if dostring == '':
            dostring=' -do "run -all; quit;"'

        if not self.interactive_rtl:
            rtlsimcmd = ( 'vsim -64 -batch -t ' + self.rtl_timescale + ' -voptargs=+acc ' 
                    + fileparams + ' ' + gstring
                    + ' ' + vlogsimargs + ' work.tb_' + self.name  
                    + dostring)
        else:
            submission = ''
            rtlsimcmd = ( 'vsim -64 -t ' + self.rtl_timescale + ' -novopt ' + fileparams 
                    + ' ' + gstring + ' ' + vlogsimargs + ' work.tb_' + self.name + dostring )

        self._rtlcmd =  rtllibcmd  +\
                ' && ' + rtllibmapcmd +\
                ' && ' + vhdlcompcmd +\
                ' && ' + vlogcompcmd +\
                ' && sync ' + self.rtlworkpath +\
                ' && ' + submission +\
                rtlsimcmd
        return self._rtlcmd

    @property
    def questasim_simdut(self):
        ''' Source file for Device Under Test in simulations directory

            Returns
            -------
                self.rtlsimpath + self.name + self.vlogext for 'sv' model
                self.rtlsimpath + self.name + '.vhd' for 'vhdl' model
        '''
        extension = None
        if self.model == 'sv':
            extension = self.vlogext
        if self.model == 'vhdl':
            extension = '.vhd'
        self._simdut = os.path.join(self.rtlsimpath, self.name+extension)
        return self._simdut

    @property
    def questasim_simtb(self):
        ''' Questasim testbench source file in simulations directory.

        This file and it's format is dependent on the language(s)
        supported by the simulator. Currently we have support only for verilog testbenches.

        '''
        if self.lang == 'sv':
            self._simtb=self.vlogsimtb
        if self.lang == 'vhdl':
            self._simtb=self.vhdlsimtb
        return self._simtb

    @property
    def questasim_dofilepaths(self):
        dofiledir = '%s/interactive_control_files/modelsim' % self.entitypath
        dofilepath = '%s/dofile.do' % dofiledir
        obsoletepath = '%s/Simulations/rtlsim/dofile.do' % self.entitypath
        newdofilepath = '%s/dofile.do' % self.simpath
        return (dofiledir, dofilepath,obsoletepath,newdofilepath)

