from thesdk import *

from rtl.rtl_iofile import rtl_iofile as rtl_iofile
class cocotb_wrapper(thesdk,metaclass=abc.ABCMeta):
    def __init__(self):
        pass
    def write_iofiles(self):
        # Combine IOS with iofile_bundle
        for ioname, io in self.IOS.Members.items():
            # If input is a file, adopt it
            if isinstance(io.Data,rtl_iofile): 
                if io.Data.name is not ioname:
                    self.print_log(type='I', 
                            msg='Unifying file %s name to ioname %s' %(io.Data.name,ioname))
                    io.Data.name=ioname
                io.Data.adopt(parent=self)

            # If input is not a file, look for corresponding file definition
            elif ioname in self.iofile_bundle.Members:
                val=self.iofile_bundle.Members[ioname]
                val.Data = self.IOS.Members[ioname].Data

        # Write input files
        for name, val in self.iofile_bundle.Members.items():
            if val.dir=='in':
                self.iofile_bundle.Members[name].write()
