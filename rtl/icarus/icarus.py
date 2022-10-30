from thesdk import *
class icarus(thesdk,metaclass=abc.ABCMeta):
    def icarus_rtlcmd(self):
        submission=self.verilog_submission
        os.mkdir(self.rtlworkpath)
        vlogmodulesstring=' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vlogmodulefiles])
        vhdlmodulesstring=' '.join([ self.rtlsimpath + '/'+ 
            str(param) for param in self.vhdlentityfiles])
        vlogcompcmd = ( 'iverilog -Wall -v -g2012 -o ' + self.rtlworkpath + '/' + self.name + vlogmodulesstring
                + ' ' + self.simdut + ' ' + self.simtb )
        gstring=' '.join([ ('-g ' + str(param) +'='+ str(val)) 
            for param,val in iter(self.rtlparameters.items()) ])
        vlogsimargs = ' '.join(self.vlogsimargs)

        fileparams=''
        for name, file in self.iofile_bundle.Members.items():
            fileparams+=' '+file.simparam

        dofile=self.interactive_controlfile
        if os.path.isfile(dofile):
            dostring=' -do "'+dofile+'"'
            self.print_log(type='I',msg='Using interactive control file %s' % dofile)
        else:
            dostring=''
            self.print_log(type='I',msg='No interactive control file set.')

        if not self.interactive_rtl:
            rtlsimcmd = ('vvp -v ' + self.rtlworkpath + '/' + self.name + fileparams + ' ' + gstring)
        else:
            submission="" #Local execution
            rtlsimcmd = ('vvp -v ' + self.rtlworkpath + '/' + self.name
                    + ' && gtkwave -S' + dofile + ' ' + self.name + '_dump.vcd')

        self._rtlcmd =  vlogcompcmd +\
                ' && sync ' + self.rtlworkpath +\
                ' && ' + submission +\
                rtlsimcmd

        return self._rtlcmd

