"""
=========
Testbench
=========

Testbench utility module for TheSyDeKick. Contains attributes and methods to
construct a Verilog or VHDL testbench for a provided DUT module/entity, parse 
its IO and parameter definitions and construct a structured testbench with clock and file IO.

Utilizes logging method from thesdk.

Initially written by Marko Kosunen 20190108, marko.kosunen@aalto.fi
Refactored from 'testbench' by Marko Kosunen 20221119, marko.kosunen@aalto.fi
"""
import os
import sys
import pdb
from rtl.testbench_common import testbench_common
from rtl.sv.verilog_testbench import verilog_testbench
from rtl.vhdl.vhdl_testbench import vhdl_testbench
from rtl.verilator.verilator_testbench import verilator_testbench

class testbench(testbench_common):
    """ Testbench class. Extends `module` through 'testbench_commom'

    """

    def __init__(self, parent=None, **kwargs):
        """ Executes init of testbench_common, thus having the same attributes and 
        parameters.

        Parameters
        ----------
            **kwargs :
               See module testbench_common
        
        """

        #This should be language specific.
        super().__init__(parent=parent,**kwargs)

    @property
    def langmodule(self):
        """The language specific operation is defined with an instance of 
        language specific class. Properties and methods return values from that class.
        """
        if not hasattr(self,'_langmodule'):
            if self.lang == 'sv':
                self._langmodule=verilog_testbench(
                        parent=self.parent,
                        file=self.file, name=self.name, 
                        instname=self.instname)
            elif self.lang == 'vhdl':  
                self._langmodule=vhdl_testbench(
                        parent=self.parent,
                        file=self.file, name=self.name, 
                        instname=self.instname)
            elif self.lang == 'verilator':  
                self._langmodule=verilator_testbench(
                        parent=self.parent,
                        file=self.file, name=self.name, 
                        instname=self.instname)
        return self._langmodule
    @property
    def iofiles(self):
        return self.langmodule.iofiles
    @iofiles.setter
    def iofiles(self,val):
        self.langmodule.iofiles = val

    @property
    def connectors(self):
        """Overload to pass values to langmodule.
        """
        if not hasattr(self.langmodule,'_connectors'):
            self.langmodule.connectors=rtl_connector_bundle(lang=self.lang)
        return self.langmodule.connectors
    @connectors.setter
    def connectors(self,val):
        self.langmodule.connectors = val

    @property
    def assignment_matchlist(self):
        if not hasattr(self.langmodule,'_assignment_matchlist'):
            self.langmodule.assignment_matchlist=[]
        return self.langmodule.assignment_matchlist
    @assignment_matchlist.setter
    def assignment_matchlist(self,val):
        self.langmodule.assignment_matchlist = val

    @property
    def content_parameters(self):
        """ Parameters used inside the testbench
            
            Dict of name: (type,value)
        """
        return self.langmodule.content_parameters
    @content_parameters.setter    
    def content_parameters(self,val):
        self.langmodule.content_parameters=val


    @property
    def verilog_instances(self):
        """Verilog instances Bundle to be added to tesbench
        
        Todo 
        Need to handle VHDL instance too.

        """
        if not hasattr(self,'_verilog_instances'):
            self._verilog_instances=Bundle()
        return self._verilog_instances

    def verilog_instance_add(self,**kwargs):
        """Add verilog instance to the Bundle fro a file

        Parameters
        ----------
        **kwargs:
           name : str
             name of the module
           file :
               File defining the module

        """
        # TODO: need to handle vhdl instances too
        name=kwargs.get('name')
        file=kwargs.get('file')
        self.verilog_instances.Members[name]=verilog_module(file=file,instname=name)
        # Addc connectors from the imported instance 
        self.connectors.update(bundle=self.verilog_instances.Members[name].io_signals.Members)
    
    @property
    def parameter_definitions(self):
        """Parameter  and variable definition strings of the testbench

        """

        return self.langmodule.parameter_definitions
    
    @property
    def connector_definitions(self):
        """Verilog register and wire definition, VHDL signal strings.

        """
        return self.langmodule.connector_definitions

    def assignments(self,**kwargs):
        """Wire/signal assingment strings

        """
        return self.langmodule.assignments
     
    @property
    def iofile_definitions(self):
        """IOfile definition strings

        """
        return self.langmodule.iofile_definitions

    @property
    def clock_definition(self):
        """Clock definition string

        Todo
        Create append mechanism to add more clocks.

        """
        return self.langmodule.clock_definitions

    @property
    def iofile_close(self):
        """File close procedure for all IO files.

        """
        return self.langmodule.iofile_close

    @property
    def end_condition(self):
        """ RTL structure that sets the thesdk_simulation_completed to true.
        Default for VHDL: 'thesdk_simulation_completed <= thesdk_file_io_completed;'
        """
        return self.langmodle._end_condition
    @end_condition.setter
    def end_condition(self,value):
        self.langmodule._end_condition = value

    @property
    def misccmd(self):
        """String
        
        Miscellaneous command string corresponding to self.rtlmisc -list in
        the parent entity.
        """
        return self.langmodule.misccmd
    
    @misccmd.setter
    def misccmd(self,value):
        self.langmodule.misccmd=value
    @misccmd.deleter
    def misccmd(self,value):
        self.langmodule.misccmd=None

    # This method 
    def define_testbench(self):
        """Defines the tb connectivity, creates reset and clock, and initializes them to zero

        """
        self.langmodule.define_testbench()
    
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

    @property
    def definition(self):
        '''Entity definition part extracted for the file. Contains generics and 
        IO definitions.

        Overloads the property inherited from 'module', as wish to control whan we generate the headers.
        '''

    def generate_contents(self):
        """Call language specific contents generator.
        """
        self.langmodule.generate_contents()

if __name__=="__main__":
    pass
