"""
================
Testbench_common
================
Common properties and methods for RTL testbench creation and manipulation

Initially written by Marko Kosunen 20190108, marko.kosunen@aalto.fi
Refactored from 'testbench' by Marko Kosunen 20221119, marko.kosunen@aalto.fi

"""
import os
import sys
from thesdk import *
from rtl import *
from rtl.module import module
from rtl.sv.verilog_module import verilog_module
from rtl.vhdl.vhdl_entity import vhdl_entity

class testbench_common(module):
    ''' Testbench class. Extends `module`

    '''

    def __init__(self, parent=None,**kwargs):
        '''Parameters
           ----------
           parent: object, None (mandatory to define). TheSyDeKick parent entity object for this testbench.
           **kwargs :
              None

        '''

        if parent==None:
            self.print_log(type='F', msg="Parent of testbench not given")
        else:
            self.parent=parent
        try:  
            # The proper files are determined in rtl based on simulation model
            self.file = self.parent.simtb
            self._dutfile = self.parent.simdut
        except:
            self.print_log(type='F', msg="Testbench file definition failed")
        
        self._name=''
        self._parameters=Bundle()

    @property
    def connectors(self):
        if not hasattr(self,'_connectors'):
            self._connectors=rtl_connector_bundle()
        return self._connectors
    @connectors.setter
    def connectors(self,val):
        self._connectors = val
    @property
    def assignment_matchlist(self):
        if not hasattr(self,'_assignment_matchlist'):
            self._assignment_matchlist=[]
        return self._assignment_matchlist
    @assignment_matchlist.setter
    def assignment_matchlist(self,val):
        self._assignment_matchlist = val

    @property
    def dut_instance(self):
        """RTL module parsed from the verilog or VHDL file of the parent depending on `parent.model`

        """
        if not hasattr(self,'_dut_instance'):
            if self.parent.model in ['sv', 'icarus']:
                self._dut_instance=verilog_module(**{'file':self._dutfile})
            elif self.parent.model=='vhdl':
                self._dut_instance=vhdl_entity(**{'file':self._dutfile})
        return self._dut_instance

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
    def dumpfile(self):
        """String
        
        Code that generates a VCD dumpfile when running the testbench with icarus verilog.
        This dumpfile can be used with gtkwave. 
        """
        dumpStr="// Generates dumpfile with iverilog\n"
        if self.parent.model == 'icarus' and self.parent.interactive_rtl:
            dumpStr += "initial begin\n"
            dumpStr += '  $dumpfile("' + self.parent.name + '_dump.vcd");\n'
            dumpStr += "  $dumpvars(0, tb_" + self.parent.name + ");\nend \n"
        return dumpStr
        
if __name__=="__main__":
    pass
