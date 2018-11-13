import os
import sys
import subprocess
import shlex
from abc import * 
from thesdk import *
from verilog import *
import numpy as np
import pandas as pd
from functools import reduce

class testbench(thesdk):
    def __init__(self,parent=None, **kwargs):
        #if parent==None:
        #    self.print_log({'type':'F', 'msg':"Parent of Verilog input file not given"})
        #try:
            #rndpart=os.path.basename(tempfile.mkstemp()[1])

        self.data_file_name=kwargs.get('data_file_name')
        self.ctrl_file_name=kwargs.get('ctrl_file_name')
        self.data_file = []
        self.ctrl_file = []
        self.sys_def_file_name = kwargs.get('sys_def_file_name','sys_def')
        self.sys_def_file = parent._entitypath + '/sv/' + self.sys_def_file_name + '.vh'
        print(self.sys_def_file)
        self._vlogsimpath = parent._vlogsimpath
        self._entitypath = parent._entitypath
        self.block_name = kwargs.get('block_name')
        self.output_port_name = kwargs.get('output_port_name')
        self.output_bitwidth = kwargs.get('output_bitwidth')

        for file_name in self.data_file_name:
            self.data_file.append(parent._vlogsimpath + '/' + file_name + '.txt')#parent._vlogsimpath + '/' + file_name + '_' + rndpart + '.txt'
        for file_name in self.ctrl_file_name:
            self.ctrl_file.append(parent._vlogsimpath + '/' + file_name + '.txt')#parent._vlogsimpath + '/' + file_name + '_' + rndpart + '.txt'

        self.output_file = self._vlogsimpath + '/' + "output.txt"
        #except:
        #    self.print_log({'type':'F', 'msg':"Verilog IO file definition failed"})
        
        self.data = kwargs.get('data',[])
        self.data_name = kwargs.get('data_name',[]) # name of data signals
        self.data_bitwidth = kwargs.get('data_bitwidth',[])
        self.ctrl = kwargs.get('ctrl',[])
        self.ctrl_name = kwargs.get('ctrl_name',[]) # name of control signals
        self.ctrl_bitwidth = kwargs.get('ctrl_bitwidth',[])
        self.datatype = kwargs.get('datatype',[]) # support real, complex

        #TODO: delete file if not needed; fixed point converter; check name and data demension coherence
        ## Input error check
        for i in range(len(self.data)):
            if self.data[i].shape[1] != len(self.data_name[i]):
                msg = 'Number of data names in ' + self.data_file_name[i] + ' is different from the column number of data matrx'
                self.print_log({'type':'F', 'msg':msg}) 
        
        if len(self.datatype) != len(self.data):
            self.print_log({'type':'F', 'msg':"Number of data type is different from the number of data files"})

        for i in range(len(self.ctrl)):
            if self.ctrl[i].shape[1] != len(self.ctrl_name[i])+1:  # the first column is timestamp
                msg = 'Number of ctrl names in ' + self.ctrl_file_name[i] + ' is different from the column number of ctrl matrx'
                self.print_log({'type':'F', 'msg':msg}) 
    
    def run_testbench_generator(self):
        #subprocess.call(["rm","-rf","../../../Sim_files/"])
        #subprocess.call(["mkdir","../../../Sim_files/"])
        self.write_ctrl_file()
        self.write_data_file()
        self.sys_def_generator()
        self.testbench_generator()

    
    def write_data_file(self):
        for i in range(len(self.data)):
            parsed = []
            header_line = []
            for k in range(self.data[i].shape[1]):
                if self.datatype[i] == 'complex':
                    if k == 0:
                        parsed = np.r_['1', np.real(self.data[i][:,k]).reshape(-1,1), np.imag(self.data[i][:,k]).reshape(-1,1)]
                    else:
                        parsed = np.r_['1', parsed, np.real(self.data[i][:,k]).reshape(-1,1), np.imag(self.data[i][:,k].reshape(-1,1))]
                    header_line.append(self.data_name[i][k] + "Real")
                    header_line.append(self.data_name[i][k] + "Imag")
                else:
                    if k == 0:
                        parsed = np.r_['1', self.data[i][:,k].reshape(-1,1)]
                    else:
                        parsed = np.r_['1', parsed, self.data[i][:,k].reshape(-1,1)]
                    header_line.append(self.data_name[i][k])

            df = pd.DataFrame(parsed,dtype=int)
            df.to_csv(path_or_buf=self.data_file[i], sep="\t", index=False, header=header_line)
            time.sleep(2)
    
    def write_ctrl_file(self):
        for i in range(len(self.ctrl)):
            parsed = []
            header_line = []
            for k in range(self.ctrl[i].shape[1]):
                if k == 0:
                    parsed = np.r_['1', self.ctrl[i][:,k].reshape(-1,1)]
                    header_line.append('Timestamp')
                else:
                    parsed = np.r_['1', parsed, self.ctrl[i][:,k].reshape(-1,1)]
                    header_line.append(self.ctrl_name[i][k-1])

            df = pd.DataFrame(parsed,dtype=int)
            df.to_csv(path_or_buf=self.ctrl_file[i], sep="\t", index=False, header=header_line)
            time.sleep(2)

    def sys_def_generator(self):
        #subprocess.call(["cp",self.sys_def_file, self.sys_def_file_name+'_test.vh']) #copy old sys_def_file and create a new one
        sys_def_file = open(self.sys_def_file,'w') # add all the define to the existing sys_def.vh
        print(self.sys_def_file)

        for i in range(len(self.data_name)):
            for k in range(len(self.data_name[i])):
                sys_def_file.write("`define WIDTH_" + self.data_name[i][k] + " " + str(self.data_bitwidth[i][k]) + "\n")
                if i == 0 and k == 0:
                    data_bitwidth_arr = np.array(self.data_bitwidth[i][k])
                else:
                    data_bitwidth_arr = np.append(data_bitwidth_arr,self.data_bitwidth[i][k])
        
        for i in range(len(self.ctrl_name)):
            for k in range(len(self.ctrl_name[i])):
                sys_def_file.write("`define WIDTH_" + self.ctrl_name[i][k] + " " + str(self.ctrl_bitwidth[i][k]) + "\n")
                if i == 0 and k == 0:
                    ctrl_bitwidth_arr = np.array(self.ctrl_bitwidth[i][k])
                else:
                    ctrl_bitwidth_arr = np.append(ctrl_bitwidth_arr,self.ctrl_bitwidth[i][k])
        
        for i in range(len(self.output_port_name)):
            sys_def_file.write("`define WIDTH_" + self.output_port_name[i] + " " + str(self.output_bitwidth[i]) + "\n")

        sys_def_file.write("\n")
        sys_def_file.write("`define INPUT_DATA_FILE_LEN " + str(len(self.data_file)) + "\n")
        sys_def_file.write("`define INPUT_CTRL_FILE_LEN " + str(len(self.ctrl_file)) + "\n")
        sys_def_file.write("\n")
        sys_def_file.write("`define DATA_NUM_PER_FILE {")

        for i in range(len(self.data)):
            if i == 0:
                if self.datatype[i] == 'complex':
                    sys_def_file.write(str(2*self.data[i].shape[1]))
                    data_signal_len = np.array(2*self.data[i].shape[1])
                else:
                    sys_def_file.write(str(self.data[i].shape[1]))
                    data_signal_len = np.array(self.data[i].shape[1])
            else:
                if self.datatype[i] == 'complex':
                    sys_def_file.write(', ' + str(2*self.data[i].shape[1]))
                    data_signal_len = np.append(data_signal_len,2*self.data[i].shape[1])
                else:
                    sys_def_file.write(', ' + str(self.data[i].shape[1]))
                    data_signal_len = np.append(data_signal_len,self.data[i].shape[1])
        sys_def_file.write('}\n')

        sys_def_file.write("`define DATA_NUM " + str(np.max(data_signal_len)) + "\n")
        sys_def_file.write("`define DATA_BITWIDTH " + str(np.max(data_bitwidth_arr)) + "\n")

        sys_def_file.write("`define CTRL_NUM_PER_FILE {")
        for i in range(len(self.ctrl)):
            if i == 0:
                sys_def_file.write(str(self.ctrl[i].shape[1]-1))
                ctrl_signal_len = np.array(self.ctrl[i].shape[1]-1)
            else:
                sys_def_file.write(', ' + str(self.ctrl[i].shape[1]-1))
                ctrl_signal_len = np.append(ctrl_signal_len,self.ctrl[i].shape[1]-1)
        sys_def_file.write('}\n')

        sys_def_file.write("`define CTRL_NUM " + str(np.max(ctrl_signal_len)) + "\n")
        sys_def_file.write("`define CTRL_BITWIDTH " + str(np.max(ctrl_bitwidth_arr)) + "\n")

        sys_def_file.write('\n')

        sys_def_file.write("`define INPUT_DATA_FILE_NAME {")
        for i in range(len(self.data_file)):
            if i == 0:
                sys_def_file.write("\"" + self.data_file[i] + "\"")
            else:
                sys_def_file.write(", \"" + self.data_file[i] + "\"")
        sys_def_file.write('}\n')

        sys_def_file.write("`define INPUT_CTRL_FILE_NAME {")
        for i in range(len(self.ctrl_file)):
            if i == 0:
                sys_def_file.write("\"" + self.ctrl_file[i] + "\"")
            else:
                sys_def_file.write(", \"" + self.ctrl_file[i] + "\"")
        sys_def_file.write('}\n')

        sys_def_file.write("`define OUTPUT_FILE_NAME \"" + self.output_file + "\"\n")

    def testbench_generator(self):
        testbench_file = open(self._entitypath + '/sv/tb_' + self.block_name + '.sv','w')
        abspath = os.path.dirname(os.path.abspath(__file__))
        testbench_skeleton_1 = open(abspath + '/../Testbench_skeleton/testbench_skeleton_1.txt','r') # those two skeleton needs to be put in some fixed place
        testbench_skeleton_2 = open(abspath + '/../Testbench_skeleton/testbench_skeleton_2.txt','r')
        testbench_skeleton_3 = open(abspath + '/../Testbench_skeleton/testbench_skeleton_3.txt','r')
        content_1 = testbench_skeleton_1.read()
        content_2 = testbench_skeleton_2.read()
        content_3 = testbench_skeleton_3.read()
        testbench_file.write(content_3)
        testbench_file.write("module tb_" + self.block_name + " #(\n")
        testbench_file.write(content_1 + "\n\n\n\t")
        testbench_file.write("/**********************************************************/\n\t")
        testbench_file.write("/**********************************************************/\n\t")

        ## initialize wires
        for i in range(len(self.data_name)):
            for k in range(len(self.data_name[i])):
                testbench_file.write("logic [`WIDTH_" + self.data_name[i][k] + "-1:0] " + self.data_name[i][k] + ";\n\t")

        for i in range(len(self.ctrl_name)):
            for k in range(len(self.ctrl_name[i])):
                testbench_file.write("logic [`WIDTH_" + self.ctrl_name[i][k] + "-1:0] " + self.ctrl_name[i][k] + ";\n\t")
        
        for i in range(len(self.output_port_name)):
            testbench_file.write("logic [`WIDTH_" + self.output_port_name[i] + "-1:0] " + self.output_port_name[i] + ";\n\t")

        testbench_file.write("\n\t")

        for i in range(len(self.data_name)):
            for k in range(len(self.data_name[i])):
                testbench_file.write("assign " + self.data_name[i][k] + " = data_input_port[" + str(i) + "][" + str(k) + "];\n\t" )
        
        for i in range(len(self.ctrl_name)):
            for k in range(len(self.ctrl_name[i])):
                testbench_file.write("assign " + self.ctrl_name[i][k] + " = ctrl_input_port[" + str(i) + "][" + str(k) + "];\n\t" )
        
        ## instantiate module
        testbench_file.write(self.block_name + " DUT (\n\t\t")
        testbench_file.write(".clock(clock), .reset(reset),\n\t\t")
        for i in range(len(self.data_name)):
            for k in range(len(self.data_name[i])):
                if(i == (len(self.data_name)-1) and k == (len(self.data_name[i])-1)):
                    testbench_file.write("." + self.data_name[i][k] + "(" + self.data_name[i][k] +"), \n\t\t" )
                else:
                    testbench_file.write("." + self.data_name[i][k] + "(" + self.data_name[i][k] +"), " )
        
        for i in range(len(self.ctrl_name)):
            for k in range(len(self.ctrl_name[i])):
                if(i == (len(self.ctrl_name)-1) and k == (len(self.ctrl_name[i])-1)):
                    testbench_file.write("." + self.ctrl_name[i][k] + "(" + self.ctrl_name[i][k] +"), \n\t\t" )
                else:
                    testbench_file.write("." + self.ctrl_name[i][k] + "(" + self.ctrl_name[i][k] +"), " )

        for i in range(len(self.output_port_name)):
            if i == (len(self.output_port_name)-1):
                testbench_file.write("." + self.output_port_name[i] + "(" + self.output_port_name[i] +") \n\t );\n\t")
            else:
                testbench_file.write("." + self.output_port_name[i] + "(" + self.output_port_name[i] +"), ")

        testbench_file.write("always @(posedge clock) begin \n\t\t$fdisplay( output_file, \"")
        for i in range(len(self.output_port_name)):
            if i == (len(self.output_port_name)-1):
                testbench_file.write("%d\",")
            else:
                testbench_file.write("%d\t")

        for i in range(len(self.output_port_name)):
            if i == (len(self.output_port_name)-1):
                testbench_file.write(self.output_port_name[i]+"); \n\t")
            else:
                testbench_file.write(self.output_port_name[i]+",")
        
        testbench_file.write("end\n\t")

        testbench_file.write("/**********************************************************/\n\t")
        testbench_file.write("/**********************************************************/\n\n")
        testbench_file.write(content_2)


if __name__=="__main__":
    t1 = np.array([1,1,1,0,0,0,0,1,1,1,1]).reshape(-1,1)
    t = [t1]
    print(t)


    s0 = np.array([1]).reshape(-1,1)
    s1 = np.array([1]).reshape(-1,1)
    s_all = np.r_['1',s0,s1]
    s =[s_all]

    print(s_all.shape[1])
    print(s)

    data_file_name = ["io_in"]
    ctrl_file_name = ["CTRL"]
    data_name = [["io_in"]]
    data_bitwidth = [[1]]
    ctrl_name = [["io_en"]]
    ctrl_bitwidth = [[1]]
    output_port_name = ["io_out"]
    output_bitwidth = [1]
    a = testbench(**{'data_file_name':data_file_name, 
                     'data':t, 
                     'datatype':['real'], 
                     'data_name':data_name, 
                     'data_bitwidth':data_bitwidth,
                     'ctrl_file_name':ctrl_file_name, 
                     'ctrl':s, 
                     'ctrl_name':ctrl_name, 
                     'ctrl_bitwidth':ctrl_bitwidth,
                     'sys_def_file_name':"sys_def",
                     'block_name':"DelayChain",
                     'output_port_name':output_port_name,
                     'output_bitwidth':output_bitwidth})
    #a.write_data_file()
    #a.write_ctrl_file()
    #a.sys_def_generator()
    #a.testbench_generator()

    a.run_testbench_generator()

