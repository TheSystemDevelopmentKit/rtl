library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.textio.all;


entity tb_fileio is
    generic( filepath :string := "testiofile.txt");
end tb_fileio;

architecture behavioural of tb_fileio is

begin
    fileio:process is
    file f_filepath : text open read_mode is filepath;
    variable f_line : line;
    variable int_in : integer;
    variable logic_in : std_logic_vector(7 downto 0);
    variable read_ok: boolean;
    begin
        report("Starting"); 
        while not endfile(f_filepath) loop
            readline(f_filepath, f_line);
            read(f_line,int_in,read_ok);
            if read_ok then
                report("Read in integer: " & to_string(int_in) & " which is converted to " & to_string(std_logic_vector(to_signed(int_in,8)))); 
            else
                report("Read in integer failed." & to_string(int_in)); 
            end if;
            wait for 10 ns;
            read(f_line,logic_in, read_ok);
            if read_ok then
                report("Read in logic: " & to_string(logic_in) & " which is converted to " & to_string(to_integer(signed(logic_in))));
            else
                report("Read in logic failed." & to_string(logic_in)); 
            end if;
        end loop;
        report("Stopping"); 
        wait;
    end process;
end architecture;

