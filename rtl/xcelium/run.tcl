# This is a minimum working example of an Xcelium input tcl file
# The file is input line by line into the simulator console at the start of the simulation

# To test with your own design:
# 1) Replace tb_acorechip with your own testbench
# 2) Replace acorechip with your own module
# 3) Move this file to Entities/<your_module>/interactive_control_files/run.tcl

# Opening an SHM database with the name 'waves', which we are using to store the signal changes
# -default makes it the default database
database -open -shm waves -default

# This probes everything inside the module acorechip
# Note: check Cadence support for the syntax of this command
# This was developed with a flattened gate level netlist therefore the depth is pretty shallow
# If you find signals missing this probe command is the reason
probe -create tb_acorechip.acorechip

# Opens a waveform window and adds signals to it
# Everything inside the simvision block is executed in the
# simulator frontend/environment/whatever you want to call it.
simvision {
    waveform new -name "Waves"
    waveform add -cdivider "Clocks and resets"
    waveform add -signals tb_acorechip.acorechip.clock
    waveform add -signals tb_acorechip.acorechip.reset

    waveform add -cdivider "IOs"
    waveform add -signals tb_acorechip.acorechip.io_jtag_TCK
    waveform add -signals tb_acorechip.acorechip.io_jtag_TDI
    waveform add -signals tb_acorechip.acorechip.io_jtag_TDO_data
    waveform add -signals tb_acorechip.acorechip.io_jtag_TMS
    waveform add -signals tb_acorechip.acorechip.io_jtag_TRSTn
    waveform add -signals tb_acorechip.acorechip.io_tx
}

# Runs the simulator
run
