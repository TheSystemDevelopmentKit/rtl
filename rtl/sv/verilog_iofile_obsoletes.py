"""Verilog iofile obsoletes

Mixin class to collect obsolete verilog properties
Support for these to be removed in Release v1.11

Initially written by Marko Kosunen, marko.kosunen@aalto.fi 20230531
"""

class verilog_iofile_obsoletes():

    # Status parameter
    @property
    def verilog_stat(self):
        '''Status variable name to be used in verilog testbench.

        '''
        self.print_log(type='O', msg='Parameter verilog_stat is obsolete. Use rtl_stat instead' )
        return self.langmodule.rtl_stat

    @verilog_stat.setter
    def verilog_stat(self,value):
        self.langmodule.rtl_stat=value


    #Timestamp integers for control files
    @property
    def verilog_ctstamp(self):
        '''Current time stamp variable name to be used in verilog testbench.
        Used in event type file IO.

        '''
        self.print_log(type='O', msg='Parameter verilog_ctstamp is obsolete. Use rtl_ctstamp instead' )
        return self.langmodule.rtl_ctstamp
#
#    @property
#    def verilog_ptstamp(self):
#        '''Past time stamp variable for verilog testbench. Used in event type file IO.
#
#        '''
#        self.print_log(type='O', msg='Parameter verilog_ptstamp is obsolete. Use rtl_ptstamp instead' )
#        return self.langmodule.rtl_ptstamp
#
#    @property
#    def verilog_tdiff(self):
#        '''Verilog time differencec variable. Used in event based file IO.
#        '
#        '''
#        self.print_log(type='O', msg='Parameter verilog_tdiff is obsolete. Use rtl_tdiff instead' )
#        return self.langmodule.rtl_tdiff
#    
#    # Status integer verilog definitions
#    @property
#    def verilog_statdef(self):
#        '''Verilog file read status integer vari'
#able definitions and initializations strings.
#
#        '''
#        self.print_log(type='O', msg='Parameter verilog_statdef is obsolete. Use rtl_statdef instead' )
#        return self.langmodule.rtl_statdef
#
#
#    # File pointer
#    @property
#    def verilog_fptr(self):
#        '''Verilog file pointer name.
#
#        '''
#        self.print_log(type='O', msg='Parameter verilog_fptr is obsolete. Use rtl_fptr instead' )
#        return self.langmodule.rtl_fptr
#
#    @verilog_fptr.setter
#    def verilog_fptr(self,value):
#        self.langmodule._rtl_fptr=value
#
#    # File opening, direction dependent 
#    @property
#    def verilog_fopen(self):
#        '''Verilog file open routine string.
#
#        '''
#        self.print_log(type='O', msg='Parameter verilog_fopen is obsolete. Use rtl_fopen instead' )
#        return self.langmodule.rtl_fopen
#
#    # File close
#    @property
#    def verilog_fclose(self):
#        '''Verilog file close routine sting.
#
#        '''
#        self.print_log(type='O', msg='Parameter verilog_fclose is obsolete. Use rtl_fclose instead' )
#        return self.langmodule.rtl_fclose
#
#    @property
#    def verilog_connectors(self):
#        ''' List for verilog connectors.
#        These are the verilog signals/regs associated with this file
#
#        '''
#        self.print_log(type='O', msg='Parameter verilog_connectors is obsolete. Use rtl_connectors instead' )
#        return self.rtl_connectors
#
#    @verilog_connectors.setter
#    def verilog_connectors(self,value):
#        #Ordered list.
#        self.rtl_connectors=value

