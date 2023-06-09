"""
======================
Verilog IOfile module 
======================

Provides vhdl- file-io related attributes and methods 
for TheSyDeKick RTL intereface.

Initially written by Marko Kosunen, marko.kosunen@aalto.fi,
Yue Dai, 2018

"""
import os
import sys
import pdb
from abc import * 
from thesdk import *
#from thesdk.iofile import iofile
from rtl.rtl_iofile_common import rtl_iofile_common
import numpy as np
import pandas as pd
import sortedcontainers as sc
from rtl.connector import indent

class vhdl_iofile(rtl_iofile_common):
    """
    Class to provide file IO for rtl simulations. When created, 
    adds a rtl_iofile object to the parents iofile_bundle attribute.
    Accessible as self.iofile_bundle.Members['name'].

    Provides methods and attributes that can be used to construct sections
    in VHDL testbenches, like file io routines, file open and close routines,
    file io routines, file io format strings and read/write conditions.
    """

    @property
    def ioformat(self):
        '''Formatting string for vhdl file reading
           Default %d, i.e. content of the file is single column of
           integers.
           
        '''
        if not hasattr(self,'_ioformat'):
            self._ioformat='%d'
        return self._ioformat
    
    @ioformat.setter
    def ioformat(self,value):
        self._ioformat=value

    @property
    def rtlparam(self):
        '''Extracts the parameter name and value from simparam attribute. 
        Used to construct the parameter definitions for Verilog testbench. 

        Default {'g_file_<self.name>', ('string',self.file) }

        '''
        if not hasattr(self,'_rtlparam'):
            key=re.sub(r"-g ",'',self.simparam).split('=')[0]
            val=re.sub(r"-g ",'',self.simparam).split('=')[1]
            self._rtlparam={key:('string','\"%s\"'%(val))}
        return self._rtlparam

    # Status parameter
    @property
    def rtl_stat(self):
        '''Status variable name to be used in vhdl testbench.

        '''
        if not hasattr(self,'_rtl_stat'):
            self._rtl_stat='status_%s' %(self.name)
        return self._rtl_stat

    @rtl_stat.setter
    def rtl_stat(self,value):
        self._rtl_stat=value

    #Timestamp integers for control files
    @property
    def rtl_ctstamp(self):
        '''Current time stamp variable name to be used in vhdl testbench.
        Used in event type file IO.

        '''
        if not hasattr(self,'_rtl_ctstamp'):
            self._rtl_ctstamp='ctstamp_%s' %(self.name)
        return self._rtl_ctstamp

    @property
    def rtl_pstamp(self):
        '''Past time stamp variable for vhdl testbench. Used in event type file IO.

        '''
        if not hasattr(self,'_rtl_pstamp'):
            self._rtl_pstamp='ptstamp_%s' %(self.name)
        return self._rtl_pstamp

    @property
    def rtl_tdiff(self):
        '''Verilog time differencec variable. Used in event based file IO.
        '
        '''
        if not hasattr(self,'_rtl_diff'):
            self._rtl_tdiff='tdiff_%s' %(self.name)
        return self._rtl_tdiff

    # File pointer
    @property
    def rtl_fptr(self):
        '''VHDL file pointer name.

        '''
        self._rtl_fptr='f_%s' %(self.name)
        return self._rtl_fptr

    @rtl_fptr.setter
    def rtl_fptr(self,value):
        self._rtl_fptr=value


    @property
    def rtl_statdef(self):
        '''Verilog file read status integer variable definitions and initializations strings.

        '''
        if self.parent.iotype=='sample':
            self._rtl_statdef=''
            for connector in self.parent.rtl_connectors:
                self._rtl_statdef+='variable status_%s : Boolean := False;\n' %(connector.name)
        elif self.parent.iotype=='event':
            for connector in self.parent.rtl_connectors:
                self._rtl_statdef='variable status_%s : Boolean := False;\n' %(connector.name)
            self._rtl_statdef='variable status_%s : Boolean := False;\n' %(self.rtl_ctstamp)
            self._rtl_statdef+='--Time is presented as integers of time units\n'
            for stamp in [ self.rtl_ctstamp, self.rtl_pstamp]:
                self._rtl_statdef+='variable %s : integer := 0;\n' %(stamp)
            self._rtl_statdef+='variable %s : time := 0.0 ps;\n' %(self.rtl_tdiff)
            for connector in self.parent.rtl_connectors:
                self._rtl_statdef+='variable status_%s : Boolean := False;\n' %(connector.name)
        return self._rtl_statdef

    # File opening, direction dependent 
    @property
    def rtl_fopen(self):
        '''Verilog file open routine string.

        '''
        if self.parent.dir=='in':
            mode='read'
        if self.parent.dir=='out':
            mode='write'
        self._rtl_fopen=('file %s : text open %s_mode is %s;\n' 
                         %(self.rtl_fptr,mode,next(iter(self.rtlparam))))
        self._rtl_fopen+='variable line_%s : line;\n' %(self.rtl_fptr)
        return self._rtl_fopen

    # File close
    @property
    def rtl_fclose(self):
        '''Verilog file close routine sting.

        '''
        self._rtl_fclose='file_close(%s);\n' %(self.rtl_fptr)
        return self._rtl_fclose

    # Condition string for monitoring if the signals are unknown
    @property 
    def rtl_io_condition(self):
        '''VHDL condition string that must be true in order to file IO read/write to occur.

        Default for output file: `not is_x(connector.name)` for all connectors of the file.
        Default for input file: `'True'` 
        file is always read with rising edge of the clock or in the time of an event defined in the file.

        '''
        if not hasattr(self,'_rtl_io_condition'):
            if self.parent.dir=='out':
                first=True
                for connector in self.parent.rtl_connectors:
                    if first:
                        self._rtl_io_condition='not is_x(%s)' %(connector.name)
                        first=False
                    else:
                        self._rtl_io_condition='%s \n and not is_x(%s)' \
                                %(self._rtl_io_condition,connector.name)
            elif self.parent.dir=='in':
                self.rtl_io_condition= 'True'
        return self._rtl_io_condition

    @rtl_io_condition.setter
    def rtl_io_condition(self,value):
        self._rtl_io_condition=value

    @property 
    def rtl_io_sync(self):
        '''File io synchronization condition for sample type input.
        Default: `rising_edge(clock)`

        '''

        if not hasattr(self,'_rtl_io_sync'):
            if self.iotype=='sample':
                self._rtl_io_sync= 'rising_edge(clock)'
        return self._rtl_io_sync

    @rtl_io_sync.setter
    def rtl_io_sync(self,value):
        self._rtl_io_sync=value

    def rtl_io_condition_append(self,**kwargs ):
        '''Append new condition string to `rtl_io_condition`

        Parameters
        ----------
        **kwargs :
           cond : str

        '''
        cond=kwargs.get('cond', '')
        if not (not cond ):
            self._rtl_io_condition='%s \n%s' \
            %(self.rtl_io_condition,cond)

    @property
    def rtl_io(self):
        '''VHDL  write/read construct for file IO depending on the direction 
        and file type (event/sample).

        Returns 
        _______
        str
            VHDL code for file IO to read/write the IO file.


        '''
        first=True
        if self.parent.dir == 'out':
            self._rtl_io='file_'+self.name+' : process\n'
        elif self.parent.dir == 'in':
            if self.parent.iotype == 'sample':
                self._rtl_io='file_'+self.name+' : process\n'
            if self.parent.iotype == 'event':
                self._rtl_io='file_'+self.name+' : process\n'

        self._rtl_io+=indent(text=self.rtl_statdef,level=1)
        self._rtl_io+=indent(text=self.rtl_fopen,level=1)
        for connector in self.parent.rtl_connectors:
            if connector.width == 1:
                if connector.ioformat == '%d':
                    self._rtl_io+=indent(text='variable v_%s : integer;' 
                                         %(connector.name),level=1)
                elif connector.ioformat == '%s':
                        self._rtl_io+=indent(text='variable v_%s : std_logic;' 
                                             %(connector.name),level=1)
            else:
                if connector.ioformat == '%d':
                    self._rtl_io+=indent(text='variable v_%s : integer;' 
                                         %(connector.name),level=1)
                elif connector.ioformat == '%s':
                    self._rtl_io+=indent(text='variable v_%s : std_logic_vector( %s downto %s);' 
                                         %(connector.name, connector.ll, 
                                           connector.rl),level=1)

        if self.parent.iotype=='sample':
            if self.parent.dir=='out':
                self._rtl_io+='begin\n'
                self._rtl_io+=indent(text='while not simdone loop\n',level=1)
                self._rtl_io+=indent(text='wait until %s;\n'%(self.rtl_io_sync),level=1)
                self._rtl_io+=indent(text='if ( %s ) then\n' %(self.rtl_io_condition), level=2)
                first = True
                for connector in self.parent.rtl_connectors:
                    #verilog-like formatting
                    if connector.width == 1:
                        if connector.ioformat =='%d':
                            self._rtl_io+=indent(text='v_%s := to_integer(unsigned\'(\"0\" & %s));\n' 
                                                 %(connector.name,connector.name),level=3)
                        elif connector.ioformat== '%s':
                            self._rtl_io+='v_%s := to_string(%s)' %(connector.name,connector.name)
                        else:
                            self.print_log(type='F', 
                                           msg='Connector format %s not supported' %(connector.ioformat))
                    else:
                        if connector.ioformat =='%d':
                            self._rtl_io+=indent(text='v_%s := to_integer(signed(%s));\n' 
                                                 %(connector.name,connector.name),level=3)
                        elif connector.ioformat== '%s':
                            self._rtl_io+='v_%s := to_string(%s)' %(connector.name,connector.name)
                        else:
                            self.print_log(type='F', 
                                           msg='Connector format %s not supported' %(connector.ioformat))

                    if first:
                        self._rtl_io+=indent(text='write(line_%s,v_%s);' 
                                         %(self.rtl_fptr,connector.name), level=3)
                        first = False
                    else:
                        self._rtl_io+=indent(text='write(line_%s, HT);'%(self.rtl_fptr), level=3)
                        self._rtl_io+=indent(text='write(line_%s,v_%s);' 
                                         %(self.rtl_fptr,connector.name), level=3)

                self._rtl_io+=indent(text='writeline(%s,line_%s);\n' %(self.rtl_fptr,self.rtl_fptr), level=3)
                self._rtl_io+=indent(text='end if;',level=2)
                self._rtl_io+=indent(text='end loop;',level=1)
                self._rtl_io+=indent(text='%s'%(self.rtl_fclose),level=1)
            elif self.parent.dir=='in':
                self._rtl_io+='begin\n'
                self._rtl_io+=indent(text=('while not endfile(%s) loop\n' 
                                      %(self.rtl_fptr)),level=1)
                self._rtl_io+=indent(text='wait until %s;\n' %(self.rtl_io_sync),level=2)
                self._rtl_io+=indent(text='if ( %s ) then \n' %(self.rtl_io_condition), level=3)
                for connector in self.parent.rtl_connectors:
                    self._rtl_io+=indent(text='readline(%s,line_%s);\n'
                                         %(self.rtl_fptr,self.rtl_fptr,), level=4)
                    self._rtl_io+=indent(text='read(line_%s,v_%s,status_%s);\n' 
                                         %(self.rtl_fptr,connector.name,connector.name), level=4)
                    #verilog-like formatting
                    if connector.ioformat =='%d':
                        # All integers are assumed to be signed
                        if connector.width == 1:
                            self._rtl_io+=indent(text=('%s <= std_logic(to_unsigned(v_%s,1)(0));\n'
                                                    %(connector.name,connector.name)
                                                   ),level=3)
                        else:
                            self._rtl_io+=indent(text=('%s <= std_logic_vector(to_signed(v_%s,%s));\n'
                                                    %(connector.name,connector.name,connector.width)
                                                   ),level=3)
                    elif connector.ioformat== '%s':
                        # String is assumed to be logic
                        self._rtl_io+=indent(text='%s <= v_%s;\n',level=4)
                    else:
                        self.print_log(type='F', 
                                       msg='Connector format %s not supported' %(connector.ioformat))
                self._rtl_io+=indent(text='end if;',level=3)
                self._rtl_io+=indent(text='end loop;',level=1)
                self._rtl_io+=indent(text='done_%s <= True;' %(self.rtl_fptr),level=1)
                self._rtl_io+=indent(text='%s' %(self.rtl_fclose),level=1)
                self._rtl_io+=indent(text='wait;',level=1)
            self._rtl_io+='end process;\n\n'

        #Control files are handled differently
        elif self.parent.iotype=='event':
            if self.parent.dir=='out':
                self.print_log(type='F', msg='Output writing for control files not supported')
            elif self.parent.dir=='in':
                self._rtl_io+='begin\n'
                self._rtl_io+=indent(text=('while not endfile(%s) loop\n' 
                                      %(self.rtl_fptr)),level=1)
                self._rtl_io+=indent(text=('%s := %s;\n' 
                                           %(self.rtl_pstamp, self.rtl_ctstamp))
                                     ,level=2)
                self._rtl_io+=indent(text='readline(%s,line_%s);\n'
                                     %(self.rtl_fptr,self.rtl_fptr,), level=3)
                self._rtl_io+=indent(text='read(line_%s,%s,status_%s);\n' %(self.rtl_fptr,self.rtl_ctstamp,self.rtl_ctstamp), level=3) 
                for connector in self.parent.rtl_connectors:
                    self._rtl_io+=indent(text='read(line_%s,v_%s,status_%s);\n' 
                                         %(self.rtl_fptr,connector.name,connector.name), level=2)
                self._rtl_io+=indent(text=('%s := ( %s - %s ) * 1.0 ps;\n' 
                                           %(self.rtl_tdiff, self.rtl_ctstamp,
                                             self.rtl_pstamp)),
                                     level=2)
                self._rtl_io+=indent(text=('wait for %s ;\n' %(self.rtl_tdiff)), level=2);

                for connector in self.parent.rtl_connectors:
                    #verilog-like formatting
                    if connector.ioformat =='%d':
                        # All integers are assumed to be signed
                        if connector.width == 1:
                            self._rtl_io+=indent(text=('%s <= std_logic(to_unsigned(v_%s,1)(0));\n'
                                                    %(connector.name,connector.name)
                                                   ),level=3)
                        else:
                            self._rtl_io+=indent(text=('%s <= std_logic_vector(to_signed(v_%s,%s));\n'
                                                    %(connector.name,connector.name,connector.name,connector.width)
                                                   ),level=3)
                    elif connector.ioformat== '%s':
                        # String is assumed to be logic
                        self._rtl_io+=indent(text='%s <= v_%s;\n',level=4)
                    else:
                        self.print_log(type='F', 
                                       msg='Connector format %s not supported' %(connector.ioformat))
                self._rtl_io+=indent(text='end loop;',level=1)
                self._rtl_io+=indent(text='done_%s <= True;' %(self.rtl_fptr),level=1)
                self._rtl_io+=indent(text='%s' %(self.rtl_fclose),level=1)
                self._rtl_io+=indent(text='wait;',level=1)
                self._rtl_io+='end process;\n\n'
        else:
            self.print_log(type='F', msg='Iotype not defined')
        return self._rtl_io



    
