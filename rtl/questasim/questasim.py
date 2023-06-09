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
         
        vlogmodulesstring=' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vlogmodulefiles])
        vhdlmodulesstring=' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vhdlentityfiles])

        # The following cases are possible
        # Testbench is sv OR testbench is vhdl, identified with 'lang'
        # source is verilog OR source is vhdl, identified by 'model
        # Has additional source files in the 'other' language, identified by 'cosim'
        # In total, 8 cases
        if self.lang=='sv' and self.model=='sv':
            #We need to compile verilog testbench and simdut anyway.
            vlogcompcmd = ( 'vlog -sv -work work ' + vlogmodulesstring 
                + ' ' + self.simdut + ' ' + self.simtb + ' ' + ' '.join(self.vlogcompargs))
            # Define hdll compcmd, if we have cosim
            if len(vhdlmodulesstring) == 0:
                vhdlcompcmd = ' echo '' > /dev/null '
            else:
                vhdlcompcmd = ( 'vcom -2008 -work work ' + ' ' + vhdlmodulesstring + ' ' + ' '.join(self.vhdlcompargs))

        elif self.lang=='sv' and self.model=='vhdl':
            #We need to compile vhdl sources anyway, but no testbench
            vhdlcompcmd = ( 'vcom -2008 -work work ' + ' ' +
                       vhdlmodulesstring + ' ' + self.vhdlsrc )
            #We need to compile verilog testbench anyway, but simdut is in vhdl
            vlogcompcmd = ( 'vlog -sv -work work ' + vlogmodulesstring 
                    + ' ' + self.simtb )
            vlogcompcmd = ( 'vlog -sv -work work ' + vlogmodulesstring 
                + ' ' + self.simtb + ' ' + ' '.join(self.vlogcompargs))

        elif self.lang=='vhdl' and self.model=='sv':
            # We need to compile VHDL testbench anyway, but not the source
            vhdlcompcmd = ( 'vcom -2008 -work work ' + ' ' +
                       vhdlmodulesstring + ' ' + self.simtb )
            #We need to compile verilog simdut anyway.
            vlogcompcmd = ( 'vlog -sv -work work ' + vlogmodulesstring 
                + ' ' + self.simdut + ' '.join(self.vlogcompargs))

        elif self.lang=='vhdl' and self.model=='vhdl':
            # We need to compile VHDL source and testbench anyway
            vhdlcompcmd = ( 'vcom -2008 -work work ' + ' ' + vhdlmodulesstring 
                    + ' ' + self.vhdlsrc + ' ' + self.simtb )
            # Define vlog compcmd, if we have cosim
            if len(vlogmodulesstring) == 0:
                vlogcompcmd = ' echo '' > /dev/null '
            else:
                vlogcompcmd = ( 'vlog -sv -work work ' + vlogmodulesstring )

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

        self._rtlcmd =  rtllibcmd
        self._rtlcmd += ' && ' + rtllibmapcmd
        # Commpile dependencies first.
        if self.lang == 'sv':
            self._rtlcmd += ' && ' + vhdlcompcmd
            self._rtlcmd += ' && ' + vlogcompcmd
        elif self.lang == 'vhdl':
            self._rtlcmd += ' && ' + vlogcompcmd
            self._rtlcmd += ' && ' + vhdlcompcmd
        self._rtlcmd += ' && sync ' + self.rtlworkpath 
        self._rtlcmd += ' && ' + submission 
        self._rtlcmd +=  rtlsimcmd
        return self._rtlcmd

    @property
    def questasim_vhdlcmd(self):
        # This command is run if model='vhdl' 
        # Testbench is determined with 'lang'
        submission = self.lsf_submission
        rtllibcmd =  'vlib ' +  self.rtlworkpath
        rtllibmapcmd = 'vmap work ' + self.rtlworkpath
        vlogmodulesstring =' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vlogmodulefiles])
        vhdlmodulesstring =' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vhdlentityfiles])

        # If there are additional verilog source files, handle as co-simulation
        cosim = vlogmodulesstring != ''

        # Verilog testbench, but vhdl source, default in this command
        if self.lang=='sv':
            vhdlcompcmd = ( 'vcom -2008 -work work ' + ' ' +
                       vhdlmodulesstring + ' ' + self.vhdlsrc )
        #VHDL testbench in addition to vhdl sources
        if self.lang == 'vhdl':
            vhdlcompcmd = ( 'vcom -2008 -work work ' + ' ' +
                       vhdlmodulesstring + ' ' + self.vhdlsrc
                    + ' ' + self.simtb )

        # Verilog testbench, default operation
        if self.lang=='sv':
            vlogcompcmd = ( 'vlog -sv -work work ' + vlogmodulesstring 
                    + ' ' + self.simtb )
        elif self.lang=='vhdl' and cosim: # we should not end up here
            vlogcompcmd = ( 'vlog -sv -work work ' + vlogmodulesstring)

        gstring = ' '.join([ 
                                ('-g ' + str(param) +'='+ str(val[1])) 
                                for param,val in self.rtlparameters.items() 
                            ])
        vlogsimargs = ' '.join(self.vlogsimargs)

        fileparams = ''
        for name, file in self.iofile_bundle.Members.items():
            fileparams += ' '+file.simparam

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

        self._rtlcmd = rtllibcmd + ' && ' + rtllibmapcmd
        # Compile vhdl is tb is vhdl or we are cosimulating
        #if self.lang=='vhdl' or cosim:
        self._rtlcmd += ' && ' + vhdlcompcmd
        # Compile verilog is tb is verilog
        if self.lang=='sv' or cosim:
            self._rtlcmd += ' && ' + vlogcompcmd
        self._rtlcmd += ( ' && sync ' + self.rtlworkpath 
                + ' && ' + submission +rtlsimcmd)
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

