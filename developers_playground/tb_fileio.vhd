library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.textio.all;


entity tb_fileio is
    generic( filepath :string := "testiofile.txt");
end tb_fileio;

architecture behavioural of tb_fileio is
    signal int_in_vect : std_logic_vector(7 downto 0);
    signal logic_in : std_logic_vector(7 downto 0);

begin
    fileio:process is
    file f_filepath : text open read_mode is filepath;
    variable v_int_in : integer;
    variable v_logic_in : logic_in'subtype;
    variable f_line : line;
    variable read_ok: boolean;
    begin
        report("Starting"); 
        while not endfile(f_filepath) loop
            readline(f_filepath, f_line);
            read(f_line,v_int_in,read_ok);
            if read_ok then
                report("Read in integer: " & to_string(v_int_in) & " which is converted to " & to_string(std_logic_vector(to_signed(v_int_in,int_in_vect'length)))); 
            else
                report("Read in integer failed." & to_string(v_int_in)); 
            end if;
            int_in_vect <= std_logic_vector(to_signed(v_int_in,int_in_vect'length));
            wait for 10 ns;
            read(f_line,v_logic_in, read_ok);
            if read_ok then
                report("Read in logic: " & to_string(v_logic_in) & " which is converted to " & to_string(to_integer(signed(v_logic_in))));
            else
                report("Read in logic failed." & to_string(v_logic_in)); 
            end if;
            logic_in <= v_logic_in;
            wait for 10 ns;
        end loop;
        report("Stopping"); 
        wait;
    end process;
end architecture;

