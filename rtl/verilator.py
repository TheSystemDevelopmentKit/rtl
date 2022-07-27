"""
===========
Verilator
===========
Module to generate a Verilator testbench for TheSyDeKick verilog entity.

Initially written by Aleksi Korsman, 2022

"""

import os
import sys
sys.path.append(os.path.abspath("../../thesdk"))

from thesdk import *
from rtl import *
from rtl.module import verilog_module, verilog_connector_bundle, verilog_connector

class verilator(thesdk):

    @property
    def _classfile(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

    def __init__(self, parent=None, **kwargs):
        '''Parameters
           ----------
           parent: object, None (mandatory to define). TheSyDeKick parent entity object for this testbench.
           **kwargs :
              None

        '''

        if parent==None:
            # TODO: replafe type to F
            self.print_log(type='I', msg="Parent of Verilog testbench not given")
        else:
            self.parent=parent
        try:  
            # The proper files are determined in rtl based on simulation model
            self._file = self.parent.simtb
            self._dutfile = self.parent.simdut
        except:
            # TODO: replace type to F
            self.print_log(type='I', msg="Verilog Testbench file definition failed")
        
        #The methods for these are derived from verilog_module
        self._name=''
        self._parameters=Bundle()
        self.connectors=verilog_connector_bundle()
        self.iofiles=Bundle()
        self.content_parameters={'c_Ts': ('const int','1/(g_Rs*1e-12)')} # Dict of name: (type,value)
        self.assignment_matchlist=[]

    @property
    def rtlcmd(self):
        vlogmodulesstring=' '.join([ self.parent.rtlsimpath + '/'+ 
            str(param) for param in self.parent.vlogmodulefiles])

        compile_tool = 'verilator'
        compile_args = ' '.join(['--cc', '--trace'])
        compile_dut = self.parent.simdut
        compile_extra_modules = vlogmodulesstring
        build_args = ' '.join(['--exe'])
        build_dut = self.parent.simtb

        #build_cmd = ' '.join([compile_tool, compile_args, compile_dut, compile_extra_modules, build_args, build_dut])
        build_cmd = ' '.join([compile_tool, compile_args, compile_dut])
        print(build_cmd)
        self._rtlcmd = build_cmd
        return self._rtlcmd
    @rtlcmd.setter
    def rtlcmd(self, value):
        self._rtlcmd = value
    @rtlcmd.deleter
    def rtlcmd(self):
        self._rtlcmd = None


class verilatortb(verilog_module):
    '''Verilator Testbench class. Extends `verilog_module`
    
    '''
    @property
    def _classfile(self):
        return os.path.dirname(os.path.realpath(__file__)) + "/"+__name__

    def __init__(self, parent=None, **kwargs):
        '''Parameters
           ----------
           parent: object, None (mandatory to define). TheSyDeKick parent entity object for this testbench.
           **kwargs :
              None

        '''

        if parent==None:
            # TODO: replafe type to F
            self.print_log(type='I', msg="Parent of Verilog testbench not given")
        else:
            self.parent=parent
        try:  
            # The proper files are determined in rtl based on simulation model
            self._file = self.parent.simtb
            self._dutfile = self.parent.simdut
        except:
            # TODO: replace type to F
            self.print_log(type='I', msg="Verilog Testbench file definition failed")
        
        #The methods for these are derived from verilog_module
        self._name=''
        self._parameters=Bundle()
        self.connectors=verilog_connector_bundle()
        self.iofiles=Bundle()
        self.content_parameters={'c_Ts': ('const int','1/(g_Rs*1e-12)')} # Dict of name: (type,value)
        self.assignment_matchlist=[]

    @property
    def file(self):
        '''Path to the testbench file

        Default: `self.parent.vlogsrcpath + '/tb_' + self.parent.name + '.cpp'`


        '''
        if not hasattr(self,'_file'):
            self._file=None
        return self._file

    @file.setter
    def file(self,value):
            self._file=value

    @property
    def dut_instance(self):
        '''RTL module parsed from the verilog

        '''
        if not hasattr(self,'_dut_instance'):
            if self.parent.model=='sv':
                self._dut_instance=verilog_module(**{'file':self._dutfile})
            elif self.parent.model=='vhdl':
                self.print_log(type='F', msg="Verilator supports only verilog!")
        return self._dut_instance

    #We should not need this, but it is wise to enable override
    @dut_instance.setter
    def dut_instance(self,value):
        self._dut_instance=value

    @property
    def verilog_instances(self):
        '''Verilog instances Bundle to be added to tesbench

        '''
        if not hasattr(self,'_verilog_instances'):
            self._verilog_instances=Bundle()
        return self._verilog_instances


    def verilog_instance_add(self,**kwargs):
        '''Add verilog instance to the Bundle fro a file

        Parameters
        ----------
        **kwargs:
           name : str
             name of the module
           file :
               File defining the module

        '''
        name=kwargs.get('name')
        file=kwargs.get('file')
        self.verilog_instances.Members[name]=verilog_module(file=file,instname=name)

    @property
    def parameter_definitions(self):
        '''Parameter and variable definition strings of the testbench
        '''
        definitions='// Parameter definitions\n'
        for name, val in self.content_parameters.items():
                definitions+= val[0]+ ' ' + name + '=' + val[1]+';\n'
        return definitions

    @property
    def connector_definitions(self):
        '''Verilog register and wire definition strings
        TODO FOR VERILATOR
        '''
        # Registers first
        definitions='//Register definitions\n'
        for name, val in self.connectors.Members.items():
            if val.cls=='reg':
                definitions=definitions+val.definition

        definitions=definitions+'\n//Wire definitions\n'
        for name, val in self.connectors.Members.items():
            if val.cls=='wire':
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
            iofile_defs=iofile_defs+val.verilog_statdef
            iofile_defs=iofile_defs+val.verilog_fopen
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
            iofile_close=iofile_close+val.verilog_fclose
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
        TODO FOR VERILATOR
        '''
        # Dut is creted automaticaly, if verilog file for it exists
        self.connectors.update(bundle=self.dut_instance.io_signals.Members)
        #Assign verilog simulation parameters to testbench
        self.parameters=self.parent.rtlparameters

        # Create clock if nonexistent 
        if 'clock' not in self.dut_instance.ios.Members:
            self.connectors.Members['clock']=verilog_connector(
                    name='clock',cls='reg', init='\'b0')

        # Create reset if nonexistent 
        if 'reset' not in self.dut_instance.ios.Members:
            self.connectors.Members['reset']=verilog_connector(
                    name='reset',cls='reg', init='\'b0')

        ## Start initializations
        #Init the signals connected to the dut input to zero
        for name, val in self.dut_instance.ios.Members.items():
            if val.cls=='input':
                val.connect.init='\'b0'

    # Automate this bsed in dir
    def connect_inputs(self):
        '''Define connections to DUT inputs.
        TODO FOR VERILATOR
        '''
        # Create TB connectors from the control file
        # See controller.py
        for ioname,val in self.parent.IOS.Members.items():
            if val.iotype is not 'file':
                self.parent.iofile_bundle.Members[ioname].verilog_connectors=\
                        self.connectors.list(names=val.ionames)
                if val.dir is 'in': 
                    # Data must be properly shaped
                    self.parent.iofile_bundle.Members[ioname].Data=self.parent.IOS.Members[ioname].Data
            elif val.iotype is 'file': #If the type is file, the Data is a bundle
                for bname,bval in val.Data.Members.items():
                    if val.dir is 'in': 
                        # Adoption transfers parenthood of the files to this instance
                        self.IOS.Members[ioname].Data.Members[bname].adopt(parent=self)
                    for connector in bval.verilog_connectors:
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
#include <verilated.h>
#include <verilated_vcd_c.h> // Writes VCD - TODO: add only if interactive mode

// Include the verilated module headers
""" \
+ \
"#include V%s.h\n" % self.dut_instance.instname + \
"#include V%s___024unit.h\n" % self.dut_instance.instname + \
"""

""" + self.parameter_definitions + \
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

if __name__=="__main__":
    testclass = verilator()
    testclass.generate_contents()
    print(testclass.contents)