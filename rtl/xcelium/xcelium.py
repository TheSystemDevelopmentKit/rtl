"""
TheSyDeKick interface for Cadence Xcelium.
Developed for Xcelium 21.03

Initially written by Tomi Valkonen 20250718
"""

from thesdk import *
import os
import glob
class xcelium(thesdk):

    @property
    def xcelium_rtlcmd(self):
        submission=self.lsf_submission
        # Collect all Verilog and SystemVerilog files into a string
        verilog_files = glob.glob(os.path.join(self.rtlsimpath, "*.v"))
        systemverilog_files = glob.glob(os.path.join(self.rtlsimpath, "*.sv"))
        all_files = sorted(self.vloglibfilemodules + verilog_files + systemverilog_files)

        module_string = " ".join(all_files)
        tb_string = f"tb_{self.name}"

        if not self.interactive_rtl:
            self._rtlcmd = f"{submission} xrun -sv -access +rwc -input {self.interactive_controlfile} -timescale {self.rtl_timescale}/{self.rtl_timeprecision} {module_string} -top {tb_string}"
        else:
            self._rtlcmd = f"xrun -sv -access +rwc -input {self.interactive_controlfile} -timescale {self.rtl_timescale}/{self.rtl_timeprecision} {module_string} -top {tb_string} -gui"

        return self._rtlcmd

    @property
    def xcelium_simdut(self):
        ''' Source file for Device Under Test in simulations directory

            Returns
            -------
                self.rtlsimpath + self.name + self.vlogext for 'sv' model
                self.rtlsimpath + self.name + '.vhd' for 'vhdl' model
        '''
        # Currently Xcelium only supports Verilog because the developer is lazy
        extension = self.vlogext
        self._simdut = os.path.join(self.rtlsimpath, self.name+extension)
        return self._simdut

    @property
    def xcelium_simtb(self):
        ''' Icarus Testbench source file in simulations directory.

        This file and it's format is dependent on the language(s)
        supported by the simulator. Currently we have support only for verilog testbenches.

        '''
        self._simtb=self.rtlsimpath + '/tb_' + self.name + self.vlogext
        return self._simtb

    @property
    def xcelium_dofilepaths(self):
        dofiledir = '%s/interactive_control_files/simvision' % self.entitypath
        dofile = '%s/run.tcl' % dofiledir
        obsoletedofile = '%s/Simulations/rtlsim/general.tcl' % self.entitypath
        generateddofile = '%s/run.tcl' % self.simpath
        return (dofiledir, dofile, obsoletedofile, generateddofile)

    @property
    def xcelium_controlfilepaths(self):
        controlfiledir = '%s/interactive_control_files/simvision' % self.entitypath
        controlfile = '%s/run.tcl' % controlfiledir
        generatedcontrolfile = '%s/run.tcl' % self.simpath
        return (controlfiledir, controlfile, generatedcontrolfile)

