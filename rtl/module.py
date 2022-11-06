"""
======
Module
======
Module import features for RTL simulation package of 
The System Development Kit. 'Module' represents verilog 
module or VHDL entity.

Provides utilities to import Verilog modules to 
python environment.

Initially written by Marko Kosunen, 2017

"""
import os
from thesdk import *
from rtl import *
from copy import deepcopy
from rtl.connector import verilog_connector
from rtl.connector import verilog_connector_bundle
from rtl.sv.verilog_module import verilog_module

class module(verilog_module,thesdk):
    """ Currently module class is just an alias for verilog_module.

    """

if __name__=="__main__":
    pass

