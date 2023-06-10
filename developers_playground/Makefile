.PHONY: all tb_fileio

all: tb_fileio

tb_fileio: 
	ghdl -a -Wall --std=08 tb_fileio.vhd
	ghdl -e --std=08 tb_fileio
	ghdl -r -v --std=08 tb_fileio --vcd=tb_fileio.vcd

show_tb_fileio:
	gtkwave tb_fileio.vcd

clean:
	ghdl --clean

