"""
==============
vhdl_testbench
==============

VHDL testbench generator utility module for TheSyDeKick. Documentation provided in 'testbench' class

Extends `testbench_common`.

Initially written by Marko Kosunen 20190108, marko.kosunen@aalto.fi
Derived from 'verilog_testbench' by Marko Kosunen 20230523, marko.kosunen@aalto.fi
"""
import os
import sys
import pdb
from rtl import indent
from rtl.connector import rtl_connector
from rtl.testbench_common import testbench_common

class vhdl_testbench(testbench_common):
    """ vhdl testbench class.

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
        self.header="""library ieee;\nuse ieee.std_logic_1164.all;\nuse ieee.numeric_std.all;\nuse std.textio.all;\n\n"""

    # For some reason unknown to me, overloading he property here is not effective
    #@property
    #def header(self):
    #    """ str : Header line of the VHDL testbench file.
    #    Default: 
    #        library ieee;
    #        use ieee.std_logic_1164.all;
    #        use ieee.numeric_std.all;
    #        use std.textio.all;

    #    """
    #    
    #    if not hasattr (self, '_header'):
    #        self._header="""library ieee;\nuse ieee.std_logic_1164.all;\nuse ieee.numeric_std.all;\nuse std.textio.all;\n\n"""
    #    return self._header
    #@header.setter
    #def header(self,val):
    #    self._header = val
        
    @property
    def parameter_definitions(self):
        """Parameter  and variable definition strings of the testbench

        """
        definitions='--Parameter definitions\n'
        for name, val in self.content_parameters.items():
            if type(val) is not tuple:
                self.print_log(type='F',msg='Parameter %s definition must be given as { \'name\' : (type,value) }' %(name))
            definitions+='constant '+ name + ' : ' + val[0] + ':='+ val[1]+';\n'
        return definitions

    @property
    def content_parameters(self):
        """ Parameters used inside the testbench
            
            Dict :  {name: (type,value)}
            
            Example
            -------

                ::

                {'c_Ts': ('time','1.0/(g_Rs*1.0e-12)*1.0 ps')} 

        """
        if not hasattr(self,'_content_parameters'):
            self._content_parameters={'c_Ts': ('time','1.0/(g_Rs*1.0e-12)*1.0 ps')} 
        return self._content_parameters
    @content_parameters.setter    
    def content_parameters(self,val):
        self._content_parameters=val
    
    @property
    def connector_definitions(self):
        """VHDL signal definition strings

        """
        #Update the language formatting. We are operating in vhdl
        for name, val in self.connectors.Members.items():
            val.lang='vhdl'
        # Registers first
        definitions='-- Driving signal definitions\n'
        for name, val in self.connectors.Members.items():
            if val.cls=='reg':
                definitions=definitions+val.definition

        definitions=(definitions+
                '\n--Driven signal definitions\n--This controls the simulation duration\n'+
                'signal thesdk_file_io_completed : Boolean := False;\n' +
                'signal thesdk_simulation_completed : Boolean := False;\n')
        for name, val in self.connectors.Members.items():
            if val.cls=='wire':
                definitions=definitions+val.definition
        return definitions

    def assignments(self,**kwargs):
        """Signal assingment strings

        """
        matchlist=kwargs.get('matchlist',self.assignment_matchlist)
        assigns='\n--Assignments\n'
        for match in matchlist:
            assigns=assigns+self.connectors.assign(match=match)
        return indent(text=assigns,level=kwargs.get('level',0))

    @property
    def iofile_definitions(self):
        """IOfile definition strings

        For VHDL, this this used to create signals to determine the completion of input file reading.
        These signals are used to set the 'thesdk_file_io_completed' signal to True.

        """
        iofile_defs='--Signals for VHDL io_files to determine end of input file reading\n'
        for name, val in self.iofiles.Members.items():
            if val.dir == 'in':
                iofile_defs+='signal done_%s : Boolean := False;\n' %(val.rtl_fptr)
        return iofile_defs 

    @property
    def clock_definition(self):
        """Clock definition string. By defult the clock is the last process to 
        stop. It runs until thesdk_simulation_completed == True.

        Todo
        Create append mechanism to add more clocks.

        """
        clockdef='--Master clock is omnipresent\n'
        clockdef+='clock_proc : process\n' 
        clockdef+='begin\n'
        clockdef+='wait for c_Ts / 2.0;\n'
        clockdef+='while not thesdk_simulation_completed loop\n'
        clockdef+='    clock <= not clock;\n' 
        clockdef+='    wait for c_Ts / 2.0;\n' 
        clockdef+='end loop;\n' 
        clockdef+='wait;\n' 

        clockdef+='end process;' 
        return clockdef

    @property
    def iofile_close(self):
        """File close procedure for all IO files.

        """
        iofile_close='\n--Close the io_files\n'
        for name, val in self.iofiles.Members.items():
            iofile_close=iofile_close+val.rtl_fclose
        iofile_close=iofile_close+'\n'
        return iofile_close 

    @property
    def end_condition(self):
        """ VHDL structure that sets the thesdk_simulation_completed to true.
        Default: 'thesdk_simulation_completed <= thesdk_file_io_completed;'
        """
        if not hasattr(self,'_end_condition'):
            if hasattr(self.parent, 'end_condition'):
                self._end_condition = self.parent.end_condition
            else:
                self._end_condition ='thesdk_simulation_completed <= thesdk_file_io_completed;'
        return self._end_condition

    @end_condition.setter
    def end_condition(self,value):
        self._end_condition = value

    @property
    def misccmd(self):
        """String
        
        Miscellaneous command string corresponding to self.rtlmisc -list in
        the parent entity.
        """
        if not hasattr(self,'_misccmd'):
            self._misccmd="-- Manual commands\n"
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
        # Dut is created automaticaly, if vhdl file for it exists
        self.connectors.update(bundle=self.dut_instance.io_signals.Members)
        for key,val in  self.connectors.Members.items():
            val.lang=self.lang
        #Assign verilog simulation parameters to testbench
        self.parameters=self.parent.rtlparameters


        # Create clock if nonexistent and reset it
        if 'clock' not in self.dut_instance.ios.Members:
            self.connectors.Members['clock']=rtl_connector(lang=self.parent.lang,
                    name='clock',cls='reg', type='std_logic',init='\'0\'')
        elif self.connectors.Members['clock'].init=='':
            self.connectors.Members['clock'].init='\'0\''

        # Create reset if nonexistent and reset it
        if 'reset' not in self.dut_instance.ios.Members:
            self.connectors.Members['reset']=rtl_connector(lang=self.parent.lang,
                    name='reset',cls='reg', init='\'0\'')
        elif self.connectors.Members['reset'].init=='':
            self.connectors.Members['reset'].init='\'0\''

        ## Start initializations
        #Init the signals connected to the dut input to zero
        for name, val in self.dut_instance.ios.Members.items():
            if val.cls=='input':
                if val.width == 1:
                    val.connect.init='\'0\''
                else:
                    val.connect.init='(others => \'0\')'
    
    # Automate this based in dir
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
        """ This is the method to generate testbench contents. Override if needed
            Contents of the testbench is constructed from attributes in the 
            following order ::
            
                self.parameter_definitions
                self.connector_definitions
                self.assignments()
                self.iofile_definitions
                self.misccmd
                self.dumpfile
                self.dut_instance.instance
                self.verilog_instance_members.items().instance (for all members)
                self.connectors.rtl_inits()
                self.iofiles.Members.items().rtl_io (for all members)
                self.iofile.close (for all members)

             Addtional code may be currently injected by appending desired 
             strings (Verilog sytax) to the relevant string attributes.

        """
    # Start the testbench contents
        contents=("""\narchitecture behavioural of """+ self.name + 
                  """ is\n"""
                  +self.parameter_definitions
                  +self.connector_definitions
                  +self.iofile_definitions
                  + """\nbegin\n"""
                  +self.assignments()
                  +self.misccmd
                  +self.dumpfile+
                  """ -- DUT definition\n"""
                  +self.dut_instance.vhdl_instance
                  )
        for inst, module in self.verilog_instances.Members.items():
            contents+=module.instance

        contents+=self.clock_definition
        contents+=("""\n--Execution of processes and sequential assignments\n"""+
                   self.connectors.rtl_inits(level=0)+"""--IO out\n""")
        for key, member in self.iofiles.Members.items():
            if member.dir=='out':
                contents+=indent(text=member.rtl_io,level=0)
        contents+="""--IO in\n"""
        for key, member in self.iofiles.Members.items():
            if member.dir=='in':
                contents+=indent(text=member.rtl_io, level=0)

        first = True
        for key, member in self.iofiles.Members.items():
            if member.dir == 'in':
                if first: 
                    contents+='thesdk_file_io_completed <= '
                    contents+=' done_%s' %(member.rtl_fptr)
                    first = False
                else:
                    contents+=' and done_%s' %(member.rtl_fptr)
        if not first: 
                contents+=';\n'
        #contents+=self.iofile_close+'\n'
        contents += self.end_condition 
        contents+='\nend architecture;\n'
        self.contents=contents


if __name__=="__main__":
    pass
