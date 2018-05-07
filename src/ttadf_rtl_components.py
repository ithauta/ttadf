import vhdlNetworkGenerator
from vhdlNetworkGenerator import *

class RTLGlobalLockOr:
    def __init__(self, inst_id,numOfInputs):
        self.name = 'globalLockOr'
        self.entity = vhdlNetworkGenerator.VHDLEntity('globalLockOr')
        self.arch = vhdlNetworkGenerator.RtlArchitecture('rtl',self.name)
        self.numOfInputs = numOfInputs
        self.libraries = []

        self.libraries.append('library ieee')
        self.libraries.append('ieee.std_logic_1164.all')
        self.libraries.append('ieee.numeric_std.all')

        port_glocks = vhdlNetworkGenerator.RtlPort('glocks','std_logic_vector(glockinputs-1 downto 0)', 'in')
        generic_glocksinputs = vhdlNetworkGenerator.RtlGeneric('glockinputs','integer',str(numOfInputs))
        port_glock = vhdlNetworkGenerator.RtlPort('glock','std_logic', 'out')

        self.entity.addGeneric(generic_glocksinputs)
        self.entity.addPort(port_glocks)
        self.entity.addPort(port_glock)


        process = vhdlNetworkGenerator.RtlProcess('update_glock')
        process.addToSensitivitylist(port_glocks)
        process.addVariable(vhdlNetworkGenerator.RtlVariable('TMP','std_logic'))

        processcode = 'tmp := \'0\';\n'
        processcode += 'for I in 0 to '+ generic_glocksinputs.getId()+ '-1 loop\n'
        processcode += '    TMP := TMP or '+port_glocks.getId()+'(I);\n'
        processcode += 'end loop;\n'
        processcode += port_glock.getId() + ' <= TMP;\n'

        process.setCode(processcode)

        self.arch.addProcess(process)


    def getEntity(self):
        return self.entity

    def write(self):

        vhdl = ''

        for library in self.libraries:
            vhdl += library +';\n'

        vhdl += self.entity.writeEntity()

        vhdl += self.arch.write()

        return vhdl


class RtlMemoryArbiter:
    def __init__(self, ports_g, addrw_g, dataw_g):
        self.name = 'tta0_mem_arbiter'
        self.entity = vhdlNetworkGenerator.VHDLEntity('tta0_mem_arbiter')
        self.arch = vhdlNetworkGenerator.RtlArchitecture('rtl',self.name)
        self.ports_g = ports_g
        self.addrw_g = addrw_g
        self.dataw_g = dataw_g
        self.libraries = []

        self.libraries.append('library ieee')
        self.libraries.append('ieee.std_logic_1164.all')
        self.libraries.append('ieee.numeric_std.all')

        self.entity.addGeneric(RtlGeneric('ports_g','integer',str(ports_g)))
        self.entity.addGeneric(RtlGeneric('addrw_g','integer',str(addrw_g)))
        self.entity.addGeneric(RtlGeneric('dataw_g','integer',str(dataw_g)))

        self.entity.addPort(RtlPort('clk','std_logic','in'))
        self.entity.addPort(RtlPort('rst_n','std_logic','in'))
        self.entity.addPort(RtlPort('bit_wr_x','std_logic_vector (ports_g*dataw_g-1 downto 0)', 'in'))
        self.entity.addPort(RtlPort('en_x', 'std_logic_vector (ports_g-1 downto 0)', 'in'))
        self.entity.addPort(RtlPort('wr_x', 'std_logic_vector (ports_g-1 downto 0)', 'in'))
        self.entity.addPort(RtlPort('d', 'std_logic_vector (ports_g*dataw_g-1 downto 0)', 'in'))
        self.entity.addPort(RtlPort('addr', 'std_logic_vector (ports_g*addrw_g-1 downto 0)', 'in'))
        self.entity.addPort(RtlPort('q', 'std_logic_vector (ports_g*dataw_g-1 downto 0)', 'out'))
        self.entity.addPort(RtlPort('waitrequest', 'std_logic_vector (ports_g-1 downto 0)','out'))

        self.entity.addPort(RtlPort('ram_en_x', 'std_logic', 'out'))
        self.entity.addPort(RtlPort('ram_wr_x', 'std_logic', 'out'))
        self.entity.addPort(RtlPort('ram_d', 'std_logic_vector(dataw_g-1 downto 0)', 'out'))
        self.entity.addPort(RtlPort('ram_q', 'std_logic_vector(dataw_g-1 downto 0)', 'in'))
        self.entity.addPort(RtlPort('ram_bit_wr_x', 'std_logic_vector(dataw_g-1 downto 0)','out'))
        self.entity.addPort(RtlPort('ram_addr', 'std_logic_vector(addrw_g-1 downto 0)', 'out'))


        self.arch.addTypedef(RtlTypedef('vec_type', 'is array (ports_g-1 downto 0) of std_logic_vector(dataw_g-1 downto 0)'))
        self.arch.addTypedef(RtlTypedef('addrvec_type', 'is array (ports_g-1 downto 0) of std_logic_vector(addrw_g-1 downto 0)'))

        self.arch.addSignal(RtlSignal('input_latch_load','std_logic'))
        self.arch.addSignal(RtlSignal('latch_en_x','std_logic_vector(ports_g-1 downto 0)'))
        self.arch.addSignal(RtlSignal('latch_en_x_r','std_logic_vector(ports_g-1 downto 0)'))
        self.arch.addSignal(RtlSignal('latch_wr_x', 'std_logic_vector(ports_g-1 downto 0)'))
        self.arch.addSignal(RtlSignal('latch_wr_x_r', 'std_logic_vector(ports_g-1 downto 0)'))
        self.arch.addSignal(RtlSignal('latch_bit_wr_x', 'vec_type'))
        self.arch.addSignal(RtlSignal('latch_bit_wr_x_r', 'vec_type'))
        self.arch.addSignal(RtlSignal('latch_d', 'vec_type'))
        self.arch.addSignal(RtlSignal('latch_d_r', 'vec_type'))
        self.arch.addSignal(RtlSignal('latch_addr', 'addrvec_type'))
        self.arch.addSignal(RtlSignal('latch_addr_r', 'addrvec_type'))

        self.arch.addSignal(RtlSignal('output_latch_load', 'std_logic'))
        self.arch.addSignal(RtlSignal('q_v', 'vec_type'))
        self.arch.addSignal(RtlSignal('q_v_r', 'vec_type'))

        self.arch.addSignal(RtlSignal('selected_port', 'integer range 0 to ports_g-1'))
        self.arch.addSignal(RtlSignal('selected_port_mask_x', 'std_logic_vector(ports_g-1 downto 0)'))
        self.arch.addSignal(RtlSignal('selected_port_mask_x_r', 'std_logic_vector(ports_g-1 downto 0)'))
        self.arch.addSignal(RtlSignal('wait_rq_r_in', 'std_logic_vector(ports_g-1 downto 0)'))
        self.arch.addSignal(RtlSignal('wait_rq_r', 'std_logic_vector(ports_g-1 downto 0)'))


        process = RtlProcess('priority_encoder')
        process.addToSensitivitylist(self.arch.findSignalById('latch_en_x'))
        code = ''
        code += '''ram_en_x <= '1';\n'''
        code += '''selected_port <= 0;\n'''
        code += '''selected_port_mask_x <= (others=>'1');\n'''
        code += '''for i in 0 to ports_g-1 loop\n'''
        code += '''    if latch_en_x(i)='0' then\n'''
        code += '''        ram_en_x <= '0';\n'''
        code += '''        selected_port <= i;\n'''
        code += '''        selected_port_mask_x(i) <= '0';\n'''
        code += '''        exit;\n'''
        code += '''    end if;\n'''
        code += '''end loop;\n'''
        process.setCode(code)
        self.arch.addProcess(process)

        process = RtlProcess('regs')
        process.addToSensitivitylist(self.entity.find('clk'))
        process.addToSensitivitylist(self.entity.find('rst_n'))
        code = ''
        code += '''if rst_n = '0' then \n'''
        code += '''    wait_rq_r <= (others=>'0');\n'''
        code += '''    selected_port_mask_x_r <= (others=>'1');\n'''
        code += '''elsif clk'event and clk = '1' then\n'''
        code += '''    wait_rq_r <= wait_rq_r_in;\n'''
        code += '''    selected_port_mask_x_r <= selected_port_mask_x;\n'''
        code += '''end if;\n'''
        process.setCode(code)
        self.arch.addProcess(process)

        process = RtlProcess('input_latch_seq')
        process.addToSensitivitylist(self.entity.find('clk'))
        process.addToSensitivitylist(self.entity.find('rst_n'))
        code = ''
        code += '''if rst_n = '0' then\n'''
        code += '''    for i in 0 to ports_g-1 loop\n'''
        code += '''        latch_en_x_r(i) <= '1';\n'''
        code += '''        latch_wr_x_r(i) <= '1';\n'''
        code += '''        latch_d_r(i) <= (others = > '0');\n'''
        code += '''        latch_bit_wr_x_r(i) <= (others = > '1');\n'''
        code += '''        latch_addr_r(i) <= (others = > '0');\n'''
        code += '''    end loop;\n'''
        code += '''elsif clk 'event and clk = '1' then\n'''
        code += '''    for i in 0 to ports_g-1 loop\n'''
        code += '''        if wait_rq_r_in(i) = '1' and wait_rq_r(i) = '0' then\n'''
        code += '''            latch_en_x_r(i) <= en_x(i);\n'''
        code += '''            latch_wr_x_r(i) <= wr_x(i);\n'''
        code += '''            latch_d_r(i) <= d((i + 1) * dataw_g - 1 downto i * dataw_g);\n'''
        code += '''            latch_bit_wr_x_r(i) <= bit_wr_x((i + 1) * dataw_g - 1 downto i * dataw_g);\n'''
        code += '''            latch_addr_r(i) <= addr((i + 1) * addrw_g - 1 downto i * addrw_g);\n'''
        code += '''        end if;\n'''
        code += '''    end loop;\n'''
        code += '''end if;\n'''
        process.setCode(code)
        self.arch.addProcess(process)

        process = RtlProcess('input_latch_comb')
        process.addToSensitivitylist(self.arch.findSignalById('wait_rq_r'))
        process.addToSensitivitylist(self.arch.findSignalById('latch_addr_r'))
        process.addToSensitivitylist(self.arch.findSignalById('latch_en_x_r'))
        process.addToSensitivitylist(self.arch.findSignalById('latch_wr_x_r'))
        process.addToSensitivitylist(self.arch.findSignalById('latch_d_r'))
        process.addToSensitivitylist(self.arch.findSignalById('latch_bit_wr_x_r'))
        process.addToSensitivitylist(self.entity.find('addr'))
        process.addToSensitivitylist(self.entity.find('en_x'))
        process.addToSensitivitylist(self.entity.find('wr_x'))
        process.addToSensitivitylist(self.entity.find('d'))
        process.addToSensitivitylist(self.entity.find('bit_wr_x'))
        code = ''
        code += '''for i in 0 to ports_g-1 loop\n'''
        code += '''    if wait_rq_r(i) = '1' then\n'''
        code += '''        latch_en_x(i) <= latch_en_x_r(i);\n'''
        code += '''        latch_wr_x(i) <= latch_wr_x_r(i);\n'''
        code += '''        latch_d(i) <= latch_d_r(i);\n'''
        code += '''        latch_bit_wr_x(i) <= latch_bit_wr_x_r(i);\n'''
        code += '''        latch_addr(i) <= latch_addr_r(i);\n'''
        code += '''    else\n'''
        code += '''        latch_en_x(i) <= en_x(i);\n'''
        code += '''        latch_wr_x(i) <= wr_x(i);\n'''
        code += '''        latch_d(i) <= d((i + 1) * dataw_g - 1 downto i * dataw_g);\n'''
        code += '''        latch_bit_wr_x(i) <= bit_wr_x((i + 1) * dataw_g - 1 downto i * dataw_g);\n'''
        code += '''        latch_addr(i) <= addr((i + 1) * addrw_g - 1 downto i * addrw_g);\n'''
        code += '''    end if;\n'''
        code += '''end loop;\n'''
        process.setCode(code)
        self.arch.addProcess(process)

        process = RtlProcess('output_latch_seq')
        process.addToSensitivitylist(self.entity.find('clk'))
        process.addToSensitivitylist(self.entity.find('rst_n'))
        code = ''
        code += '''if rst_n = '0' then\n'''
        code += '''    for i in 0 to ports_g-1 loop\n'''
        code += '''        q_v_r(i) <= (others=>'0');\n'''
        code += '''    end loop;\n'''
        code += '''elsif clk'event and clk = '1' then\n'''
        code += '''    for i in 0 to ports_g-1 loop\n'''
        code += '''        if selected_port_mask_x_r(i) = '0' then\n'''
        code += '''            q_v_r(i) <= ram_q;\n'''
        code += '''        end if;\n'''
        code += '''    end loop;\n'''
        code += '''end if;\n'''
        process.setCode(code)
        self.arch.addProcess(process)

        process = RtlProcess('output_latch_comb')
        process.addToSensitivitylist(self.arch.findSignalById('selected_port_mask_x_r'))
        process.addToSensitivitylist(self.entity.find('ram_q'))
        process.addToSensitivitylist(self.arch.findSignalById('q_v_r'))
        code = ''
        code += '''for i in 0 to ports_g-1 loop\n'''
        code += '''    if selected_port_mask_x_r(i) = '0' then\n'''
        code += '''        q_v(i) <= ram_q;\n'''
        code += '''    else\n'''
        code += '''        q_v(i) <= q_v_r(i);\n'''
        code += '''    end if;\n'''
        code += '''end loop;\n'''
        process.setCode(code)
        self.arch.addProcess(process)

        process = RtlProcess('pack')
        process.addToSensitivitylist(self.arch.findSignalById('q_v'))
        code = ''
        code += '''for i in 0 to ports_g-1 loop\n'''
        code += '''    q((i+1)*dataw_g-1 downto i*dataw_g) <= q_v(i);\n'''
        code += '''end loop;\n'''
        process.setCode(code)
        self.arch.addProcess(process)

        self.arch.addCodeline('''ram_wr_x <= latch_wr_x(selected_port);''')
        self.arch.addCodeline('''ram_d <= latch_d(selected_port);''')
        self.arch.addCodeline('''ram_bit_wr_x <= latch_bit_wr_x(selected_port);''')
        self.arch.addCodeline('''ram_addr <= latch_addr(selected_port);''')
        self.arch.addCodeline('''wait_rq_r_in <= latch_en_x xor selected_port_mask_x;''')
        self.arch.addCodeline('''waitrequest  <= wait_rq_r;''')

    def getEntity(self):
        return self.entity

    def write(self):

        vhdl = ''

        for library in self.libraries:
            vhdl += library +';\n'

        vhdl += self.entity.writeEntity()

        vhdl += self.arch.write()

        return vhdl