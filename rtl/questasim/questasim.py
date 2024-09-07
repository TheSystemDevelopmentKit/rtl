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

        # Produce a list of compile commands from self.rtlfiles
        # They are compiled in order
        # Consecutive, same language modules are grouped into one compile command
        comp_cmds = []

        vlog_start = ' '.join(["vlog","-sv","-work","work"] + self.vlogcompargs)
        vhdl_start = ' '.join(["vcom","-2008","-work","work"] + self.vhdlcompargs)
        comp_group = []
        group_lang = ""
        first = True
        for module in self.rtlfiles:
            _, file_ext = os.path.splitext(module)
            lang = "vlog" if file_ext in [".v", ".sv"] else "vhdl"
            if group_lang != lang and not first:
                # Finish compilation group as language changes
                comp_cmds += [' '.join(comp_group)]
                comp_group = []
            first = False
            if comp_group == []:
                group_lang = lang
                # Add compile command
                if lang == "vlog":
                    comp_group += [vlog_start]
                else:
                    comp_group += [vhdl_start]
            comp_group += [os.path.join(self.rtlsimpath, module)]
        # Append the last group
        comp_cmds += [' '.join(comp_group)]

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
        for comp_cmd in comp_cmds:
            self._rtlcmd += ' && ' + comp_cmd
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

