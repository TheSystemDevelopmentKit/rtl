"""
======================
RTL IOfile module 
======================

Provides Verilog- and VHDL file-io related attributes and methods 
for TheSyDeKick RTL intereface.

Restructured from verilog_iofile by Marko Kosunen, marko.kosunen@aalto.fi 2023
"""
import os
import sys
import pdb
from abc import * 
from thesdk import *
from thesdk.iofile import iofile
import numpy as np
import pandas as pd
import sortedcontainers as sc
from rtl.rtl_iofile_common import rtl_iofile_common
from rtl.sv.verilog_iofile import verilog_iofile
from rtl.sv.verilog_iofile_obsoletes import verilog_iofile_obsoletes
from rtl.connector import indent

class rtl_iofile(verilog_iofile_obsoletes,rtl_iofile_common):
    '''
    Class to provide file IO for rtl simulations. When created, 
    adds a rtl_iofile object to the parents iofile_bundle attribute.
    Accessible as self.iofile_bundle.Members['name'].

    Provides methods and attributes that can be used to construct sections
    in Verilog testbenches, like file io routines, file open and close routines,
    file io routines, file io format strings and read/write conditions.


    Example
    -------
    Initiated in parent as: 
        _=rtl_iofile(self,name='foobar')
    
                
    '''
    def __init__(self,parent=None,**kwargs):
        '''Parameters
        -----------
        parent : object 
            The parent object initializing the 
            rtl_iofile instance. Default None
        
        **kwargs :  
                name : str  
                    Name of the file. Appended with 
                    random string during the simulation.
                param : str,  -g `'g_file_'`
                    The string defining the testbench parameter to be be 
                    passed to the simulator at command line. Sets the paramname attribute.
                ioformat : str, %d
                   sets the ioformat attribute.
        '''
        #This is a redundant check, but does not hurt.to have it here too.
        if parent==None:
            self.print_log(type='F', msg="Parent of RTL input file not given")
        try:  
            super(rtl_iofile_common,self).__init__(parent=parent,**kwargs)
            self.rtlparent=parent
            self.paramname=kwargs.get('param','-g g_file_')

            self._ioformat=kwargs.get('ioformat','%d') #by default, the io values are decimal integer numbers

        except:
            self.print_log(type='F', msg="RTL IO file definition failed")

        self._DictData = None  # data structure for event-based IO data

    @property
    def langmodule(self):
        if not hasattr(self,'_langmodule'):
            if self.parent.lang=='sv': 
                #Here we give self.as a parent. A bit unclear still why it works
                # self.rtlparent should work as well
                # [TODO] figure a mnethod for value inherintace
                self._langmodule = verilog_iofile(self)
                self.langmodule.file=self.file
                self.langmodule.paramname=self.paramname
                self.langmodule.name=self.name
        return self._langmodule
    @property
    def ioformat(self):
        '''Formatting string for verilog file reading
           Default %d, i.e. content of the file is single column of
           integers.
           
        '''
        return self.langmodule.ioformat
    
    @ioformat.setter
    def ioformat(self,value):
        self.langmodule.ioformat=value

    @property
    def rtlparam(self):
        '''Extracts the parameter name and value from simparam attribute. 
        Used to construct the parameter definitions for Verilog testbench. 

        Default {'g_file_<self.name>', ('string',self.file) }

        '''
        #This should be simulators, not lang dependent.
        return self.langmodule.rtlparam
    
    # Status parameter
    @property
    def rtl_stat(self):
        '''Status variable name to be used in verilog testbench.

        '''
        return self.langmodule.rtl_stat

    @rtl_stat.setter
    def rtl_stat(self,value):
        self.langmodule.rtl_stat=value

    #Timestamp integers for control files
    @property
    def rtl_ctstamp(self):
        '''Current time stamp variable name to be used in verilog testbench.
        Used in event type file IO.

        '''
        return self.langmodule.rtl_ctstamp

    @property
    def rtl_pstamp(self):
        '''Past time stamp variable for verilog testbench. Used in event type file IO.

        '''
        return self.langmodule.rtl_pstamp

    @property
    def rtl_tdiff(self):
        '''Verilog time differencec variable. Used in event based file IO.
        '
        '''
        return self.langmodule.rtl_tdiff
    

    # Status integer verilog definitions
    @property
    def verilog_statdef(self):
        '''Verilog file read status integer variable definitions and initializations strings.

        '''
        return self.langmodule.verilog_statdef

    #Status integer verilog definitions

    # File pointer
    @property
    def verilog_fptr(self):
        '''Verilog file pointer name.

        '''
        return self.langmodule.verilog_fptr

    @verilog_fptr.setter
    def verilog_fptr(self,value):
        self.langmodule.verilog_fptr=value

    # File opening, direction dependent 
    @property
    def verilog_fopen(self):
        '''Verilog file open routine string.

        '''
        return self.langmodule.verilog_fopen

    # File close
    @property
    def verilog_fclose(self):
        '''Verilog file close routine sting.

        '''
        return self.langmodule.verilog_fclose
    @property
    def verilog_connectors(self):
        ''' List for verilog connectors.
        These are the verilog signals/regs associated with this file

        '''
        if not hasattr(self,'_verilog_connectors'):
            self._verilog_connectors=[]
        return self._verilog_connectors

    @verilog_connectors.setter
    def verilog_connectors(self,value):
        #Ordered list.
        self._verilog_connectors=value
    
    def connector_datamap(self,**kwargs):
        '''Verilog_connectors is an ordered list. Order defines the assumed order of columns in the 
        file to be read or written. 
        This datamap provides {'name' : index } dictionary to assing data to 
        correct columns. Less use for data files, more for controls

        '''
        name=kwargs.get('name')
        if not self.verilog_connectors:
            self.print_log(type='F', msg='Connector undefined, can\'t access.')
        else:
            if self.iotype=='sample':
                self._verilog_connector_datamap=dict()
            elif self.iotype=='event':
                self._verilog_connector_datamap={'time':0}
            index=0
            for val in self.verilog_connectors:
                index+=1
                self._verilog_connector_datamap.update({'%s' %(val.name): index})
        return self._verilog_connector_datamap[name]

    def set_control_data(self,**kwargs):
        '''Method to define event based data value with name, time, and value.
        Uses a python dictionary instead of a numpy array for more efficient insertions.
        The 'time' column acts as the dictionary key, the remaining columns are stored as the value.

        Parameters
        ----------
        **kwargs :
            time: int, 0
            name: str
            val: type undefined
            init: int, 0
            vector of values to initialize the data. lenght should correpond to `self.verilog_connectors+1`

        '''
        time=kwargs.get('time',int(0))
        name=kwargs.get('name')
        val=kwargs.get('val')
        init=kwargs.get('init',int(0))

        # sanity checks
        assert isinstance(time, int), "Argument 'time' should have the type 'int'"

        # Init Data and add first element
        if self.DictData is None:
            self.DictData = sc.SortedDict()
            if np.isscalar(init):
                self.DictData[0] = (np.ones(len(self.verilog_connectors))*init).astype(int)
            elif init.shape[1] == len(self.verilog_connectors)+1:
                init_array = init.astype(int)
                for row in init_array:
                    self.DictData[row[0]] = row[1:]
        # Add subsequent elements as diffs as follows:
        # None -- no change
        # int -- change signal to the given value
        else:
            # add a new row if the time is not yet in the dictionary
            if time not in self.DictData:
                # init diff as no change
                self.DictData[time] = [None for _ in range(len(self.verilog_connectors))]

            # change corresponding value
            self.DictData[time][self.connector_datamap(name=name)-1] = val

    # Overload self.Data accessors to keep them consistent with the assumption of using numpy arrays
    # To hold IO data. These methods convert to and from the diff-based data structure used in this
    # module. I.e. the self.Data property will look like an numpy array as seen from external modules
    # while in reality it's using the more efficient SortedDict implementation internally.

    # Getter - This takes the difference based format stored in DictData and converts it to a numpy array
    @property
    def Data(self):
        if not hasattr(self, '_Data'):
            self._Data=None

        else: 
            if self.iotype=='event' and hasattr(self, '_DictData'):
                diff_array = np.array([np.insert(signals, 0, time) for (time, signals) in self.DictData.items()])

                # populate None values from previous timestamps
                transposed = np.transpose(diff_array)
                for i in range(1, transposed.shape[0]):
                    for j in range(1, transposed.shape[1]):
                        if transposed[i,j] is None:
                            transposed[i,j] = transposed[i, j-1]
                self._Data = np.transpose(transposed).astype(int)
        return self._Data

    # Setter - Takes a numpy array and converts it to the diff-based SortedDict
    @Data.setter
    def Data(self, value):
        # convert value to equivalent SortedDict representation
        if self.iotype=='event':
            if self.DictData == None:
                self._DictData = sc.SortedDict()
            for row in value:
                self.DictData[row[0]] = row[1:]
            # build a numpy array from the dict and sort it by time column
            diff_array = np.array([np.insert(signals, 0, time) for (time, signals) in self.DictData.items()])

            # populate None values from previous timestamps
            transposed = np.transpose(diff_array)
            for i in range(1, transposed.shape[0]):
                for j in range(1, transposed.shape[1]):
                    if transposed[i,j] is None:
                        transposed[i,j] = transposed[i, j-1]
            self._Data = np.transpose(transposed).astype(int)
        else:
            self._Data=value

    @property
    def DictData(self):
        if not hasattr(self, '_DictData'):
            self._DictData=None
        return self._DictData

    @DictData.setter
    def DictData(self, value):
        self._DictData = value

    # Condition string for monitoring if the signals are unknown
    @property 
    def verilog_io_condition(self):
        '''Verilog condition string that must be true in ordedr to file IO read/write to occur.

        Default for output file: `~$isunknown(connector.name)` for all connectors of the file.
        Default for input file: `'1'` 
        file is always read with rising edge of the clock or in the time of an event defined in the file.

        '''
        return self.langmodule.verilog_io_condition

    @verilog_io_condition.setter
    def verilog_io_condition(self,value):
        self.langmodule.verilog_io_condition=value

    @property 
    def verilog_io_sync(self):
        '''File io synchronization condition for sample type input.
        Default: `@(posedge clock)`

        '''
        return self.langmodule.verilog_io_sync

    @verilog_io_sync.setter
    def verilog_io_sync(self,value):
        self.langmodule.verilog_io_sync=value

    def verilog_io_condition_append(self,**kwargs ):
        '''Append new condition string to `verilog_io_condition`

        Parameters
        ----------
        **kwargs :
           cond : str

        '''
        self.langmodule.verilog_io_condition_append(**kwargs)


    @property
    def verilog_io(self,**kwargs):
        '''Verilog  write/read construct for file IO depending on the direction and file type (event/sample).

        Returns 
        _______
        str
            Verilog code for file IO to read/write the IO file.


        '''
        return self.langmodule.verilog_io
