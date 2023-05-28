.PHONY: all tb_fileio

all: tb_fileio

tb_fileio: 
	ghdl -a --std=08 tb_fileio.vhd
	ghdl -e --std=08 tb_fileio
	ghdl -r -v --std=08 tb_fileio

clean:
	ghdl --clean

