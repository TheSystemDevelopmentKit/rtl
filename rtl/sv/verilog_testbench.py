"""
=================
verilog_testbench
=================

Verilog testbench generator utility module for TheSyDeKick. Documentation provided in 'testbench' class

Extends `testbench_common`.

Initially written by Marko Kosunen 20190108, marko.kosunen@aalto.fi
Refactored from 'testbench' by Marko Kosunen 20221119, marko.kosunen@aalto.fi
"""
import os
import sys
import pdb
from rtl import indent
from rtl.connector import rtl_connector
from rtl.testbench_common import testbench_common

class verilog_testbench(testbench_common):
    """ Verilog testbench class.

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
        self.header=''
        
    @property
    def parameter_definitions(self):
        """Parameter  and variable definition strings of the testbench

        """
        definitions='//Parameter definitions\n'
        for name, val in self.content_parameters.items():
                definitions+='parameter '+ val[0]+' '+name+'='+ val[1]+';\n'
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
            self._content_parameters={'c_Ts': ('integer','1/(g_Rs*1e-12)')} 
        return self._content_parameters
    @content_parameters.setter    
    def content_parameters(self,val):
        self._content_parameters=val
    
    @property
    def connector_definitions(self):
        """Verilog register and wire definition strings

        """
        #Update the language formatting. We are operating in verilog
        for name, val in self.connectors.Members.items():
            val.lang='sv'

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
        """Wire assingment strings

        """
        matchlist=kwargs.get('matchlist',self.assignment_matchlist)
        assigns='\n//Assignments\n'
        for match in matchlist:
            assigns=assigns+self.connectors.assign(match=match)
        return indent(text=assigns,level=kwargs.get('level',0))
     
    @property
    def iofile_definitions(self):
        """IOfile definition strings

        """
        iofile_defs='//Variables for the io_files\n'
        for name, val in self.iofiles.Members.items():
            iofile_defs=iofile_defs+val.rtl_statdef
            iofile_defs=iofile_defs+val.rtl_fopen
        iofile_defs=iofile_defs+'\n'
        return iofile_defs 

    @property
    def clock_definition(self):
        """Clock definition string

        Todo
        Create append mechanism to add more clocks.

        """
        clockdef='//Master clock is omnipresent\nalways #(c_Ts/2.0) clock = !clock;'
        return clockdef

    @property
    def iofile_close(self):
        """File close procedure for all IO files.

        """
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
    
    @misccmd.setter
    def misccmd(self,value):
        self._misccmd=value
    @misccmd.deleter
    def misccmd(self,value):
        self._misccmd=None

    def define_testbench(self):
        """Defines the tb connectivity, creates reset and clock, and initializes them to zero

        """
        # Dut is creted automaticaly, if verilog file for it exists
        self.connectors.update(bundle=self.dut_instance.io_signals.Members)
        #Assign verilog simulation parameters to testbench
        self.parameters=self.parent.rtlparameters

        # Create clock if nonexistent and reset it
        if 'clock' not in self.dut_instance.ios.Members:
            self.connectors.Members['clock']=rtl_connector(lang='sv',
                    name='clock',cls='reg', init='\'b0')
        elif self.connectors.Members['clock'].init=='':
            self.connectors.Members['clock'].init='\'b0'

        # Create reset if nonexistent and reset it
        if 'reset' not in self.dut_instance.ios.Members:
            self.connectors.Members['reset']=rtl_connector(lang='sv',
                    name='reset',cls='reg', init='\'b0')
        elif self.connectors.Members['reset'].init=='':
            self.connectors.Members['reset'].init='\'b0'

        ## Start initializations
        #Init the signals connected to the dut input to zero
        for name, val in self.dut_instance.ios.Members.items():
            if val.cls=='input':
                val.connect.init='\'b0'
    
    # Automate this based in dir
    def connect_inputs(self):
        """Define connections to DUT inputs.

        """
        # Create TB connectors from the control file
        # See controller.py
        for ioname,val in self.parent.IOS.Members.items():
            if val.iotype != 'file':
                self.parent.iofile_bundle.Members[ioname].verilog_connectors=\
                        self.connectors.list(names=val.ionames)
                if val.dir == 'in': 
                    # Data must be properly shaped
                    self.parent.iofile_bundle.Members[ioname].Data=self.parent.IOS.Members[ioname].Data
            elif val.iotype == 'file': #If the type is file, the Data is a bundle
                for bname,bval in val.Data.Members.items():
                    if val.dir == 'in': 
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
        """ This is the method to generate testbench contents. Override if needed
            Contents of the testbench is constructed from attributes in the 
            following order ::
            
                self.parameter_definitions
                self.connector_definitions
                self.assignments()
                self.iofile_definitions
                self.misccmd
                self.dumpfile
                self.dut_instance.verilog_instance
                self.verilog_instance_members.items().instance (for all members)
                self.connectors.verilog_inits()
                self.iofiles.Members.items().verilog_io (for all members)
                self.iofile.close (for all members)

             Addtional code may be currently injected by appending desired 
             strings (Verilog sytax) to the relevant string attributes.

        """
        # Start the testbench contents
        contents="""
//timescale 1ps this should probably be a global model parameter
"""+self.parameter_definitions+\
self.connector_definitions+\
self.assignments()+\
self.iofile_definitions+\
self.misccmd+\
self.dumpfile+\
"""
//DUT definition
"""+\
self.dut_instance.verilog_instance

        for inst, module in self.verilog_instances.Members.items():
            contents+=module.instance

        contents+=self.clock_definition
        contents+="""

//io_out
"""
        for key, member in self.iofiles.Members.items():
            if member.dir=='out':
                contents+=member.verilog_io
        contents+="""

//Execution with parallel fork-join and sequential begin-end sections
initial #0 begin
fork
""" + \
self.connectors.rtl_inits(level=1)+\
"""

    // Sequences enabled by initdone
    $display("Ready to read"); 
"""

        for key, member in self.iofiles.Members.items():
            if member.dir=='in':
                contents+=indent(text=member.verilog_io, level=1)

        contents+='\njoin\n'+self.iofile_close+'\n$finish;\nend\n'
        self.contents=contents

if __name__=="__main__":
    pass
