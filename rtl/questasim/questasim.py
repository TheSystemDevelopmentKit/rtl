"""
Questasim is a mixin class it is used to provide simulator specific
properties and methods for RTL class

Initially written by Marko kosunen 20221030
"""
from thesdk import *
import os
class questasim(thesdk):

    @property
    def questasim_sim_opt_dict(self):
        '''Preset dictionary for running optimization on the simulation.

        - 'no-opt' - no optimizations, full visibility to signals
        - 'full-opt' - fully optimized, might lose visibility to a lot of signals. Simulation may not work.
        - 'default' - not optimized simulation for interactive sims,
        optimized with full visibility for non-interactive sims
        - 'top-visible' - optimized while keeping top level (testbench) signals.
        - 'top-dut-visible' - optimized while keeping top level (testbench) and DUT signals on the first hierarchy level
        '''
        if not hasattr(self, '_sim_opt_dict'):
            self._questasim_sim_opt_dict = {
                'no-opt': ['-novopt'],
                'opt-visible': ['-vopt', '-voptargs=+acc'],
                'full-opt': ['-vopt'],
                'top-visible': [
                    '-vopt',
                    f'-voptargs="+acc=bcglnprst+tb_{self.name}"'
                ],
                'top-dut-visible': [
                    '-vopt',
                    f'-voptargs="+acc=bcglnprst+tb_{self.name} +acc=bcglnprst+{self.name}"'
                ]
            }
        return self._questasim_sim_opt_dict
    @questasim_sim_opt_dict.setter
    def questasim_sim_opt_dict(self, value):
        self._questasim_sim_opt_dict = value

    @property
    def questasim_rtlcmd(self):
        submission=self.lsf_submission
        rtllibcmd =  'vlib ' +  self.rtlworkpath
        rtllibmapcmd = 'vmap work ' + self.rtlworkpath
         

        if not self.add_tb_timescale:
            timescalestring = ' -t ' + self.rtl_timescale
        else:
            timescalestring = ''

        # Produce a list of compile commands for modules that have been defined
        # in self.compile_order
        comp_cmds = []

        for comp_list in self.compile_order:
            comp_cmd = ""
            first = True
            lang = None
            for module in comp_list:
                # Check if the module is in vlogmodulefiles or vhdlentityfiles
                # Same entry should contain modules from one language only
                if module in self.vlogmodulefiles:
                    if first:
                        lang = "sv"
                        first = False
                        comp_cmd = ["vlog -sv -work work"]
                    if lang != "sv":
                        self.print_log(type='F', msg='You can only add same language modules in one entry of compile_order!')
                    comp_cmd += [os.path.join(self.rtlsimpath, module)]
                    self.vlogmodulefiles.remove(module)
                elif module in self.vhdlentityfiles:
                    if first:
                        lang = "vhdl"
                        first = False
                        comp_cmd = ["vcom -2008 -work work"]
                    if lang != "vhdl":
                        self.print_log(type='F', msg='You can only add same language modules in one entry of compile_order!')
                    comp_cmd += [os.path.join(self.rtlsimpath, module)]
                    self.vhdlentityfiles.remove(module)
                else:
                    self.print_log(type='W', msg=f'File not included in vlogmodulefiles or vhdlentityfiles: {module}')
            comp_cmds += [' '.join(comp_cmd)]


        vlogmodulesstring=' '.join(self.vloglibfilemodules + [ self.rtlsimpath + '/'+ 
            str(param) for param in self.vlogmodulefiles ])
        vhdlmodulesstring=' '.join(self.vhdllibfileentities + [ self.rtlsimpath + '/'+ 
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
                vhdlcompcmd = ( 'vcom -2008 -work work ' + ' '
                               + vhdlmodulesstring + ' ' + ' '.join(self.vhdlcompargs))

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

        controlfile=self.simulator_controlfile
        if os.path.isfile(controlfile):
            controlstring=' -do "'+controlfile+'"'
            self.print_log(type='I',msg='Using control file %s' % controlfile)
        else:
            controlstring=' -do "run -all; quit;"'
            self.print_log(type='I',msg='No simulator control file set.')

        interactive_controlfile=self.interactive_controlfile
        if os.path.isfile(interactive_controlfile):
            interactive_string=' -do "'+ interactive_controlfile+'"'
            self.print_log(type='I',msg='Using interactive control file %s' % interactive_controlfile)
        else:
            interactive_string=' -do "run -all; quit;"'
            self.print_log(type='I',msg='No interactive control file set.')

        # Choose command
        if not self.interactive_rtl:
            rtlsimcmd = ( 'vsim -64 -batch' + timescalestring
                    + fileparams + ' ' + gstring
                    + ' ' + vlogsimargs + ' work.tb_' + self.name
                    + controlstring)
        else:
            submission="" #Local execution
            rtlsimcmd = ( 'vsim -64 ' + timescalestring + fileparams
                    + ' ' + gstring + ' ' + vlogsimargs + ' work.tb_' + self.name
                         + interactive_string )

        self._rtlcmd =  rtllibcmd
        self._rtlcmd += ' && ' + rtllibmapcmd
        # Commpile dependencies first.
        if self.lang == 'sv':
            for comp_cmd in comp_cmds:
                self._rtlcmd += ' && ' + comp_cmd
            self._rtlcmd += ' && ' + vhdlcompcmd
            self._rtlcmd += ' && ' + vlogcompcmd
        elif self.lang == 'vhdl':
            for comp_cmd in comp_cmds:
                self._rtlcmd += ' && ' + comp_cmd
            self._rtlcmd += ' && ' + vlogcompcmd
            self._rtlcmd += ' && ' + vhdlcompcmd
        self._rtlcmd += ' && sync ' + self.rtlworkpath
        self._rtlcmd += ' && ' + submission
        self._rtlcmd +=  rtlsimcmd
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
        dofile = '%s/dofile.do' % dofiledir
        obsoletefile = '%s/Simulations/rtlsim/dofile.do' % self.entitypath
        generateddofile = '%s/dofile.do' % self.simpath
        return (dofiledir, dofile, obsoletefile, generateddofile)

    @property
    def questasim_controlfilepaths(self):
        controlfiledir = '%s/interactive_control_files/modelsim' % self.entitypath
        controlfile = '%s/control.do' % controlfiledir
        generatedcontrolfile = '%s/control.do' % self.simpath
        return (controlfiledir, controlfile, generatedcontrolfile)

