-------------------------------------------------------------------------------
-- Title      : avalon mem arbiter
-- Project    : 
-------------------------------------------------------------------------------
-- File       : avalon_mem_arbiter.vhd
-- Author     : 
-- Created    : 30.01.2007
-- Last update: 2011-08-22
-- Description: n number of memory ports, n number of slaves
-- read latency 1. register before memory, others combinational
-------------------------------------------------------------------------------
-- Copyright (c) 2007
--
-------------------------------------------------------------------------------
-- Revisions  :
-- Date        Version  Author  Description
-- 30.01.2007  1.0      AK      Created
-- 27.02.2018  1.1      IH      Modified interface
-------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity tta0_mem_arbiter is
  
  generic (
    ports_g       : integer := 8;       -- how many simult accesses
    addrw_g       : integer := 8;
    dataw_g       : integer := 32      --divisable by 8
    );
  port (
    clk               : in  std_logic;
    rst_n             : in  std_logic;
    bit_wr_x          : in  std_logic_vector(ports_g*dataw_g-1 downto 0);
    en_x              : in  std_logic_vector(ports_g-1 downto 0);
    wr_x              : in  std_logic_vector(ports_g-1 downto 0);
    d                 : in  std_logic_vector(ports_g*dataw_g-1 downto 0);
    addr              : in  std_logic_vector(ports_g*addrw_g-1 downto 0);
    q                 : out std_logic_vector(ports_g*dataw_g-1 downto 0);
    waitrequest       : out std_logic_vector(ports_g-1 downto 0);        
    ram_en_x     : out std_logic;
    ram_wr_x     : out std_logic;
    ram_d        : out std_logic_vector(dataw_g-1 downto 0);
    ram_q        : in std_logic_vector(dataw_g-1 downto 0);
    ram_bit_wr_x : out std_logic_vector(dataw_g-1 downto 0);
    ram_addr     : out std_logic_vector(addrw_g-1 downto 0)
    
    );

end tta0_mem_arbiter;

architecture rtl of tta0_mem_arbiter is


  signal input_latch_load : std_logic;

  type vec_type is array (ports_g-1 downto 0) of std_logic_vector(dataw_g-1 downto 0);
  type addrvec_type is array (ports_g-1 downto 0) of std_logic_vector(addrw_g-1 downto 0);
  signal latch_en_x, latch_en_x_r         : std_logic_vector(ports_g-1 downto 0);
  signal latch_wr_x, latch_wr_x_r         : std_logic_vector(ports_g-1 downto 0);
  signal latch_bit_wr_x, latch_bit_wr_x_r : vec_type;
  signal latch_d, latch_d_r               : vec_type;
  signal latch_addr, latch_addr_r         : addrvec_type;

  signal output_latch_load : std_logic;

  signal q_v, q_v_r : vec_type;

  signal selected_port : integer range 0 to ports_g-1;
  signal selected_port_mask_x : std_logic_vector(ports_g-1 downto 0);
  signal selected_port_mask_x_r : std_logic_vector(ports_g-1 downto 0);

  signal wait_rq_r_in, wait_rq_r : std_logic_vector(ports_g-1 downto 0);

begin  -- rtl

  priority_encoder : process(latch_en_x) is
  begin
    ram_en_x <= '1';
    selected_port <= 0;
    selected_port_mask_x <= (others=>'1');
    
    for i in 0 to ports_g-1 loop
      if latch_en_x(i)='0' then
        ram_en_x <= '0';
        selected_port <= i;
        selected_port_mask_x(i) <= '0';
        exit;
      end if;
    end loop;
  end process;

  ram_wr_x     <= latch_wr_x(selected_port);
  ram_d        <= latch_d(selected_port);
  ram_bit_wr_x <= latch_bit_wr_x(selected_port);
  ram_addr     <= latch_addr(selected_port);

  wait_rq_r_in <= latch_en_x xor selected_port_mask_x;
  waitrequest  <= wait_rq_r;

  regs : process(clk, rst_n) is
  begin
    if rst_n = '0' then
      wait_rq_r <= (others=>'0');
      selected_port_mask_x_r <= (others=>'1');
    elsif clk'event and clk = '1' then
      wait_rq_r <= wait_rq_r_in;
      selected_port_mask_x_r <= selected_port_mask_x;
    end if;
  end process;

  input_latch_seq : process (clk, rst_n) is
  begin
    if rst_n = '0' then
      for i in 0 to ports_g-1 loop
        latch_en_x_r(i) <= '1';
        latch_wr_x_r(i) <= '1';
        latch_d_r(i) <= (others=>'0');
        latch_bit_wr_x_r(i) <= (others=>'1');
        latch_addr_r(i) <= (others=>'0');
      end loop;
    elsif clk'event and clk = '1' then
      for i in 0 to ports_g-1 loop
        if wait_rq_r_in(i) = '1' and wait_rq_r(i) = '0' then
          latch_en_x_r(i) <= en_x(i);
          latch_wr_x_r(i) <= wr_x(i);
          latch_d_r(i) <= d((i+1)*dataw_g-1 downto i*dataw_g);
          latch_bit_wr_x_r(i) <= bit_wr_x((i+1)*dataw_g-1 downto i*dataw_g);
          latch_addr_r(i) <= addr((i+1)*addrw_g-1 downto i*addrw_g);
        end if;
      end loop;
    end if;
  end process;

  input_latch_comb : process(wait_rq_r, latch_addr_r, latch_en_x_r, latch_wr_x_r, latch_d_r, latch_bit_wr_x_r, addr, en_x, wr_x, d, bit_wr_x) is
  begin
    for i in 0 to ports_g-1 loop
      if wait_rq_r(i) = '1' then
        latch_en_x(i) <= latch_en_x_r(i);
        latch_wr_x(i) <= latch_wr_x_r(i);
        latch_d(i) <= latch_d_r(i);
        latch_bit_wr_x(i) <= latch_bit_wr_x_r(i);
        latch_addr(i) <= latch_addr_r(i);
      else
        latch_en_x(i) <= en_x(i);
        latch_wr_x(i) <= wr_x(i);
        latch_d(i) <= d((i+1)*dataw_g-1 downto i*dataw_g);
        latch_bit_wr_x(i) <= bit_wr_x((i+1)*dataw_g-1 downto i*dataw_g);
        latch_addr(i) <= addr((i+1)*addrw_g-1 downto i*addrw_g);
      end if;
    end loop;
  end process;

  output_latch_seq : process(clk, rst_n) is
  begin
    if rst_n = '0' then
      for i in 0 to ports_g-1 loop
        q_v_r(i) <= (others=>'0');
      end loop;
    elsif clk'event and clk = '1' then
      for i in 0 to ports_g-1 loop
        if selected_port_mask_x_r(i) = '0' then
          q_v_r(i) <= ram_q;
        end if;
      end loop;
    end if;
  end process;

  output_latch_comb : process(selected_port_mask_x_r, ram_q, q_v_r) is
  begin
    for i in 0 to ports_g-1 loop
      if selected_port_mask_x_r(i) = '0' then
        q_v(i) <= ram_q;
      else
        q_v(i) <= q_v_r(i);
      end if;
    end loop;
  end process;

  pack : process(q_v) is
  begin
    for i in 0 to ports_g-1 loop
      q((i+1)*dataw_g-1 downto i*dataw_g) <= q_v(i);
    end loop;
  end process;

end rtl;

