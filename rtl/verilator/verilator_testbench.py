"""
===================
verilator_testbench
===================

Verilator testbench generator utility module for TheSyDeKick. Documentation provided in 'testbench' class

Extends `testbench_common`.

Initially written by Aleksi Korsman 2022, aleksi.korsman@aalto.fi
Refactored by Marko Kosunen 20240707, marko.kosunen@aalto.fi
"""
import os
import sys
import pdb
from rtl import indent
from rtl.connector import rtl_connector
from rtl.testbench_common import testbench_common

class verilator_testbench(testbench_common):
    """Verilator testbench class.

    """
    def __init__(self, parent=None, **kwargs):
        """ Executes init of testbench_common, thus having the same attributes and
        parameters.

        Parameters
        ----------
            **kwargs :
               See module module_common

        """
        super().__init__(parent,**kwargs)
        self.header = '#include <verilated.h>\n'
        self.header += '#include <verilated_vcd_c.h> // Writes VCD - TODO: add only if interactive mode\n'

    @property
    def parameter_definitions(self):
        '''Parameter and variable definition strings of the testbench
        '''
        definitions='// Parameter definitions\n'
        for name, val in self.content_parameters.items():
            definitions += 'auto ' + name + '=' + str(val[1]) + ';\n'
        for name, val in self.parameters.Members.items():
            definitions += 'auto ' + name + '=' + str(val[1]) + ';\n'

        return definitions

    @property
    def content_parameters(self):
        """ Parameters used inside the testbench

            Dict :  {name: (type,value)}

            Example
            -------

                ::

                {'c_Ts': ('integer','1/(g_Rs*1e-12)')}

        """
        if not hasattr(self,'_content_parameters'):
            self._content_parameters={'c_Ts': ('integer',f'1/(g_Rs*{self.rtl_timescale_num})')}
        return self._content_parameters
    @content_parameters.setter
    def content_parameters(self,val):
        self._content_parameters=val

    @property
    def connector_definitions(self):
        '''Verilator connector definitions string
        '''
        definitions='// Connector definitions\n'
        for name, val in self.connectors.Members.items():
            definitions=definitions+val.definition
        return definitions

    def assignments(self,**kwargs):
        '''Wire assingment strings
        TODO FOR VERILATOR
        '''
        matchlist=kwargs.get('matchlist',self.assignment_matchlist)
        assigns='\n//Assignments\n'
        for match in matchlist:
            assigns=assigns+self.connectors.assign(match=match)
        return intend(text=assigns,level=kwargs.get('level',0))

    @property
    def iofile_definitions(self):
        '''IOfile definition strings
        TODO FOR VERILATOR
        '''
        iofile_defs='//Variables for the io_files\n'
        for name, val in self.iofiles.Members.items():
            iofile_defs=iofile_defs+val.rtl_statdef
            iofile_defs=iofile_defs+val.rtl_fopen
        iofile_defs=iofile_defs+'\n'
        return iofile_defs

    @property
    def clock_definition(self):
        '''Clock definition string
        TODO FOR VERILATOR

        Todo
        Create append mechanism to add more clocks.

        '''
        clockdef='//Master clock is omnipresent\nalways #(c_Ts/2.0) clock = !clock;'
        return clockdef

    @property
    def iofile_close(self):
        '''File close procedure for all IO files.
        TODO FOR VERILATOR
        '''
        iofile_close='\n//Close the io_files\n'
        for name, val in self.iofiles.Members.items():
            iofile_close=iofile_close+val.rtl_fclose
        iofile_close=iofile_close+'\n'
        return iofile_close

    @property
    def misccmd(self):
        """String

        Miscellaneous command string corresponding to self.rtlmisc -list in
        the parent entity.
        """
        if not hasattr(self,'_misccmd'):
            self._misccmd="// Manual commands\n"
            mcmd = self.parent.rtlmisc
            for cmd in mcmd:
                self._misccmd += cmd + "\n"
        return self._misccmd

    # This method
    def define_testbench(self):
        '''Defines the tb connectivity, creates reset and clock, and initializes them to zero

        '''
        # Dut is creted automaticaly, if verilog file for it exists
        self.connectors.update(bundle=self.dut_instance.io_signals.Members)
        #Assign verilog simulation parameters to testbench
        self.parameters=self.parent.rtlparameters

        # Create clock if nonexistent and reset it
        if 'clock' not in self.dut_instance.ios.Members:
            self.connectors.Members['clock']=rtl_connector(lang='verilator',
                    name='clock',cls='reg', init='0')
        elif self.connectors.Members['clock'].init=='':
            self.connectors.Members['clock'].init='0'

        # Create reset if nonexistent and reset it
        if 'reset' not in self.dut_instance.ios.Members:
            self.connectors.Members['reset']=rtl_connector(lang='verilator',
                    name='reset',cls='reg', init='0')
        elif self.connectors.Members['reset'].init=='':
            self.connectors.Members['reset'].init='0'

        ## Start initializations
        #Init the signals connected to the dut input to zero
        for name, val in self.dut_instance.ios.Members.items():
            if val.cls=='input':
                val.connect.init='0'

    # This is a copy from verilog_testbench
    def connect_inputs(self):
        """Define connections to DUT inputs.

        """
        # Create TB connectors from the control file
        # See controller.py
        for ioname,val in self.parent.IOS.Members.items():
            if val.iotype != 'file':
                self.parent.iofile_bundle.Members[ioname].rtl_connectors=\
                        self.connectors.list(names=val.ionames)
                if val.dir == 'in':
                    # Data must be properly shaped
                    self.parent.iofile_bundle.Members[ioname].Data=self.parent.IOS.Members[ioname].Data
            elif val.iotype == 'file': #If the type is file, the Data is a bundle
                for bname,bval in val.Data.Members.items():
                    if val.dir == 'in':
                        # Adoption transfers parenthood of the files to this instance
                        self.IOS.Members[ioname].Data.Members[bname].adopt(parent=self)
                    for connector in bval.rtl_connectors:
                        self.tb.connectors.Members[connector.name]=connector
                        # Connect them to DUT
                        try:
                            self.dut.ios.Members[connector.name].connect=connector
                        except:
                            pass
        # Copy iofile simulation parameters to testbench
        for name, val in self.iofile_bundle.Members.items():
            self.tb.parameters.Members.update(val.rtlparam)
        # Define the iofiles of the testbench. '
        # Needed for creating file io routines
        self.tb.iofiles=self.iofile_bundle

    def generate_contents(self):
        ''' This is the method to generate testbench contents. Override if needed
            Contents of the testbench is constructed from attributes in the
            following order ::

                self.parameter_definitions
                self.connector_definitions
                self.assignments()
                self.iofile_definitions
                sefl.misccmd
                self.dut_instance.instance
                self.verilog_instance_members.items().instance (for all members)
                self.connectors.verilog_inits()
                self.iofiles.Members.items().verilog_io (for all members)
                self.iofile.close (for all members)

             Addtional code may be currently injected by appending desired
             strings (Verilog sytax) to the relevant string attributes.

             TODO FOR VERILATOR

             Verilator testbench is in C++

        '''
    # Start the testbench contents
        contents="""

// Include the verilated module headers. Should these go to headers
"""+"#include V%s.h\n" %(self.dut_instance.instname) + \
"#include V%s___024unit.h\n" %(self.dut_instance.instname) + \
"""

""" + self.parameter_definitions + \
    self.connector_definitions + \
"""

int main(int argc, char** argv, char** env) {

    // Construct a VerilatedContext to hold simulation time, etc.
    VerilatedContext* contextp = new VerilatedContext;

    // Construct the Verilated model, from Vtop.h generated from Verilating "top.v"
    // TODO: rename "top" to correspond the dut
    Vtop* top = new Vtop{contextp};

    // TODO: only if interactive mode (needs --trace in the verilator command as well)
    VerilatedVcdC *m_trace = new VerilatedVcdC;
    top->trace(m_trace, 5); // 5 limits the depth of trace - TODO: make changeable

    // TODO: randomize input values?
    // Requires arguments for verilator and exe
    Verilated::commandArgs(argc, argv);

    while (True) {
        clk ^= 1; // TODO
        // TODO: reset procedure
        if (sim_time > 1 && sim_time < 5){
            reset_procedure();
        }
        top -> eval; // TODO: rename top
        m_trace->dump(sim_time) // TODO: define sim_time
        sim_time++; // TODO: define sim_time
    }

    return 0;
}
        """
        self.contents=contents
        print(contents)

