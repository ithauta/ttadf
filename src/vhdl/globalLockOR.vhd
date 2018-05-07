library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity globalLockOr is

    generic (
        glockinputs : integer := 1
    );

    port (
        glocks : in std_logic_vector(glockinputs-1 downto 0);
        glock : out std_logic
    );

end globalLockOr;

architecture rtl of globalLockOr is

    begin

    process (glocks)
        variable TMP : std_logic;
    begin
        TMP := '0';
        for I in 0 to glockinputs-1 loop
            TMP := TMP or glocks(I);
        end loop;

        glock <= TMP;
    end process;

end rtl;
