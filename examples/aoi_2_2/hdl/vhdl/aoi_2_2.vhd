-- AOI (AND-OR-INVERT) Module for Basys3 Board
-- Filename: aoi_2_2.vhd
-- Implements: Y = NOT((A AND B) OR (C AND D))
-- Maps to Basys3 switches and 7-segment display

library ieee;
use ieee.std_logic_1164.all;

entity aoi_2_2 is
  port(
    SWT : in  std_logic_vector(3 downto 0);  -- 4 switches: SWT[3:0] for inputs a,b,c,d
    SEG : out std_logic_vector(6 downto 0);  -- 7-segment display segments
    AN  : out std_logic_vector(3 downto 0)   -- 7-segment display anodes (digit enable)
  );
end aoi_2_2;

architecture rtl of aoi_2_2 is
  -- Internal signals
  signal a, b, c, d : std_logic;
  signal y          : std_logic;

begin
  -- Map switches to inputs
  a <= SWT(0);
  b <= SWT(1);
  c <= SWT(2);
  d <= SWT(3);

  -- AOI logic: NOT of ((A AND B) OR (C AND D))
  y <= not((a and b) or (c and d));

  -- Enable only the rightmost digit (AN(0))
  -- Active low, so '0' enables digit 0
  AN <= "1110";

  -- Display output on 7-segment display
  -- Show '0' if y='0', show '1' if y='1'
  -- 7-segment encoding: (g, f, e, d, c, b, a)
  -- Display is active low ('0' = segment ON)

  -- Display '0': segments a,b,c,d,e,f on (g off) = "1000000"
  -- Display '1': segments b,c on (others off)    = "1111001"
  seg_display: process(y)
  begin
    case y is
      when '0' =>
        SEG <= "1000000";  -- Display '0'
      when '1' =>
        SEG <= "1111001";  -- Display '1'
      when others =>
        SEG <= "1111111";  -- All segments off (shouldn't happen)
    end case;
  end process seg_display;

end rtl;
