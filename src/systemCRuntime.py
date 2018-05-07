# /usr/bin/python
# -*- coding: utf-8 -*-

# Ilkka Hautala
# ithauta@ee.oulu.fi
# Center for Machine Vision and Signal Analysis (CMVS)
# University of Oulu, Finland
#

import RuntimeSystem, RuntimeCore
import math
import TTADF_Tools

class systemCTestbench():


    def __init__(self, system,rootdir):

        self.rootdir = rootdir
        self.toplevelSourceFile = ''
        self.headerList = ['<systemc.h>',
                           '<iostream>',
                           '<fstream>',
                           '<thread>',
                           '<signal.h>',
                           '<stdio.h>',
                           '<stdlib.h>',
                           '<unistd.h>',
                           '"host_fifo_interface.h"',
                           '"tta_cps_'+system.getName()+'.h"'
                           ]

        self.system = system

        self.sc_ctor_list = []

        self.main_body_lines = []


    def addTab(self,string, nbtabs):
        string = '\t' + string
        return string.replace("\n", "\n"+"\t"*nbtabs)


    def hostActorInclude(self):

        if len(self.system.getAllX86Cores()):
            source = 'volatile int KILLNETWORK = 0;\n'
            source += 'extern "C" {\n'
            for core in self.system.getAllX86Cores():
                source += '    #include "'+core.coreId+'/src/'+core.coreId+'_main.h"\n'
            source += '}\n'

        return source

    def hostActorThreads(self):

        content = ''
        for x86core in self.system.getAllX86Cores():
            content += 'std::thread '+ x86core.coreId+'_thread('+x86core.coreId +'_main);\n'
        return content

    def joinHostActorThreads(self):
        content = ''
        for x86core in self.system.getAllX86Cores():
            content += x86core.coreId+'_thread.join();\n'
        return content


    def declareClockSignals(self):

        clkSourceCode = '\n//Declare clocks \n'
        maxClock = 0
        for i,ttaCore in enumerate(self.system.getAllTTACores()):
            clkSourceCode += 'sc_clock '+ttaCore.coreId+'_clk;\n'
            if ttaCore.clkf > maxClock:
                maxClock = ttaCore.clkf

            self.sc_ctor_list.append(
                ttaCore.coreId+'_clk("'+ttaCore.coreId+'_clk",'+str(1000.0 / ttaCore.clkf)+', SC_NS, 0.5,0.0,SC_NS,false)')

        for i,x86Core in enumerate(self.system.getAllX86Cores()):
            if x86Core.clkf > maxClock:
                maxClock = x86Core.clkf

        clkSourceCode += 'sc_clock main_clk;\n'
        clkSourceCode += 'sc_signal<bool> rstx;\n'

        self.sc_ctor_list.append('main_clk("main_clk",'+str(1000.0 / ttaCore.clkf)+', SC_NS, 0.5, 0.0,SC_NS,false)')
        self.sc_ctor_list.append('rstx("rstx")')


        return clkSourceCode


    def createGlobalLockSignals(self):
        sourceCode = '\n//Create global lock signals for TTA Cores\n'

        for i,ttaCore in enumerate(self.system.getAllTTACores()):
            sourceCode += 'sc_signal<bool> s_glock_'+ttaCore.coreId+';\n'
            self.sc_ctor_list.append('s_glock_'+ttaCore.coreId+'("s_glock_'+ttaCore.coreId+'")')

        return sourceCode

    def declareInterfaceMemories(self):
        source = '\n//Create shared memories and memory arbiters\n'
        for i,smem in enumerate(self.system.memories):

            nbMemPorts = len(smem.getDirectConnections())
            if smem.getArbiter():
                nbMemPorts = nbMemPorts + 1


            portsg = str(len(smem.getArbiterConnections()))
            addrw_g = str(int(math.ceil(math.log((smem.maxAddress+1)/4,2))))
            dataw_g = str(32)
            memLen = str(int(((smem.maxAddress+1)/4)))

            ramName = smem.name+'_ram'

            for memory in self.system.getAllHostInterfaceMemories():
                for core in memory.getHostConnections():
                    source += 'sc_signal <bool> w_'+smem.name+'_'+core.getCoreId()+'_mem_en_x;\n'
                    source += 'sc_signal <bool> w_'+smem.name+'_'+core.getCoreId()+'_wr_en_x;\n'
                    source += 'sc_signal <sc_bv <'+dataw_g+'>> w_'+smem.name+'_'+core.getCoreId()+'_data_in;\n'
                    source += 'sc_signal <sc_bv <'+dataw_g+'>> w_'+smem.name+'_'+core.getCoreId()+'_data_out;\n'
                    source += 'sc_signal <sc_bv <'+dataw_g+'>> w_'+smem.name+'_'+core.getCoreId()+'_wr_mask_x;\n'
                    source += 'sc_signal <sc_bv <'+addrw_g+'>> w_'+smem.name+'_'+core.getCoreId()+'_addr;\n'
                    source += 'sc_signal <bool> w_' + smem.name + '_' + core.getCoreId() + '_waitReq;\n'

            self.sc_ctor_list.append('w_'+smem.name+'_'+core.getCoreId()+'_mem_en_x("w_'+smem.name+'_'+core.getCoreId()+'_mem_en_x")')
            self.sc_ctor_list.append('w_'+smem.name+'_'+core.getCoreId()+'_wr_en_x("w_'+smem.name+'_'+core.getCoreId()+'_wr_en_x")')
            self.sc_ctor_list.append('w_'+smem.name+'_'+core.getCoreId()+'_data_in("w_'+smem.name+'_'+core.getCoreId()+'_d")')
            self.sc_ctor_list.append('w_'+smem.name+'_'+core.getCoreId()+'_data_out("w_'+smem.name+'_'+core.getCoreId()+'_q")')
            self.sc_ctor_list.append('w_'+smem.name+'_'+core.getCoreId()+'_wr_mask_x("w_'+smem.name+'_'+core.getCoreId()+'_wr_mask_x")')
            self.sc_ctor_list.append('w_'+smem.name+'_'+core.getCoreId()+'_addr("w_'+smem.name+'_'+core.getCoreId()+'_addr")')
            self.sc_ctor_list.append('w_' + smem.name + '_' + core.getCoreId() + '_waitReq("w_' + smem.name + '_' + core.getCoreId() + '_waitReq")')


            for connection in smem.connections:
                if connection.arch == 'X86':

                    source += 'unsigned int *hostIntermediateMem_'+smem.name+' = new unsigned int ['+memLen+'];\n'
                    hostInputFifo = []
                    hostOutputFifo = []

                    for fifo in smem.fifos:
                        if fifo.source.owner.arch == 'X86' and fifo.target.owner.arch == 'TTA':
                            self.main_body_lines.append(fifo.fifoId.upper() + '_BASEADDR = (unsigned char *) hostIntermediateMem_'+smem.name+';\n')
                            hostOutputFifo.append(fifo)
                        if fifo.source.owner.arch == 'TTA' and fifo.target.owner.arch == 'X86':
                            self.main_body_lines.append(fifo.fifoId.upper() + '_BASEADDR = (unsigned char *) hostIntermediateMem_' + smem.name + ';\n')
                            hostInputFifo.append(fifo)
                    break

            for i, c in enumerate(self.system.getAllX86Cores()):
                for mem in c.externalMems:
                    addrw_g = str(int(math.ceil(math.log((mem.maxAddress + 1) / 4, 2))))
                    dataw_g = str(32)
                    memLen = str(int(((mem.maxAddress + 1) / 4)))

                    hostInputFifo = []
                    hostOutputFifo = []

                    for fifo in mem.fifos:
                        if fifo.source.owner.arch == 'X86' and fifo.target.owner.arch == 'TTA':
                            hostOutputFifo.append(fifo)
                        if fifo.source.owner.arch == 'TTA' and fifo.target.owner.arch == 'X86':
                            hostInputFifo.append(fifo)

                    source += 'unsigned int input_fifo_addrs_' + mem.name + ' = {'
                    for i, fifo in enumerate(hostInputFifo):
                        source += (str(fifo.startAddr))
                        source += ','
                    source += '};\n'

                    source += 'unsigned int  output_fifo_addrs_' + mem.name + ' = {'
                    for i, fifo in enumerate(hostOutputFifo):
                        source +=(str(fifo.startAddr))
                        source += ','
                    source += '};\n'

                    ifaceInstance = 'fifo_iface_' + c.coreId + '_' + mem.name

                    source += 'host_fifo_interface<' + memLen + ', ' + addrw_g + ', ' + dataw_g + ',32> ' + ifaceInstance +';\n'

                    self.sc_ctor_list.append(ifaceInstance + '("hostMemInterface_' + mem.name + '", hostIntermediateMem_' + mem.name + ', ' + str(
                        len(hostOutputFifo)) + ', &output_fifo_addrs_' + mem.name + ', '+str(len(hostInputFifo)) + ', &input_fifo_addrs_' + mem.name + ')')

                    #source += 'host_fifo_interface<' + memLen + ', ' + addrw_g + ', ' + dataw_g + '> ' + ifaceInstance + '('
                    #source += '"hostMemInterface_' + mem.name + '", hostIntermediateMem_' + mem.name + ', ' + str(
                    #    len(hostOutputFifo)) + ', output_fifo_addrs_' + mem.name + ', '
                    #source += str(len(hostInputFifo)) + ', input_fifo_addrs_' + mem.name + ');\n\n'


        return source



    def hostMemoryInterfaces(self):

        source = ''

        #FIFOS BETWEEN X86 HOST and TTA cores
        x86InterfaceFifos = []
        x86InterfaceMems = []
        x86InterfaceCores = []

        #FIFOS BETWEEN X86 CORES
        x86_x86InterfaceFifos = []
        x86_x86InterfaceMems = []
        x86_x86InterfaceCores = []


        for memory in self.system.memories:
            for fifo in memory.fifos:
                if (fifo.source.owner.arch == 'X86' and fifo.target.owner.arch == 'TTA') or (fifo.source.owner.arch == 'TTA'and fifo.target.owner.arch == 'X86'):
                    x86InterfaceFifos.append(fifo)
                    x86InterfaceMems.append(memory)
                    x86InterfaceCores.append(memory.owner)
                if (fifo.source.owner.arch == 'X86' and fifo.target.owner.arch == 'X86') and (fifo.source.owner.coreId != fifo.target.owner.coreId):
                    x86_x86InterfaceFifos.append(fifo)
                    if memory not in x86_x86InterfaceMems:
                        x86_x86InterfaceMems.append(memory)
                    x86_x86InterfaceCores.append(memory.owner)

        for fifo in x86InterfaceFifos:
            source += 'unsigned char * ' + fifo.fifoId.upper() + '_BASEADDR;\n'
        for fifo in x86_x86InterfaceFifos:
            source += 'unsigned char * ' + fifo.fifoId.upper() + '_BASEADDR;\n'




        return source


    def create(self, filename):
        sf = open(self.rootdir+'/'+filename, "w")

        sf.write(TTADF_Tools.mitLicense())

        for header in self.headerList:
            sf.write('#include ' + header + '\n')

        sf.write('\n')
        sf.write(self.hostActorInclude())
        sf.write('\n')
        sf.write(self.hostMemoryInterfaces())
        sf.write('\n')

        sf.write('#ifdef MTI_SYSTEMC //Modelsim, sccom compiles this\n')
        sf.write('SC_MODULE(testbench_'+self.system.getName()+'){\n')

        sf.write(self.addTab('tta_cps_'+self.system.getName()+' tta_cps;',1))

        sf.write('\n')

        sf.write('\n')
        sf.write(self.addTab(self.declareClockSignals(),1))
        sf.write('\n')
        sf.write(self.addTab(self.createGlobalLockSignals(),1))
        sf.write('\n')
        sf.write(self.addTab(self.declareInterfaceMemories(),1))
        sf.write('\n')
        sf.write('\tvoid sc_main_body();\n')
        for core in self.system.getAllHostCores():
            sf.write('\t void thread_'+core.getCoreId()+'();\n')
        sf.write('\n')

        sf.write('\tSC_CTOR(testbench_'+self.system.getName()+'):\n')

        for elem in self.sc_ctor_list:
            sf.write('\t\t'+elem+',\n')

        sf.write('\t\ttta_cps("tta_cps","work.TTA_CPS_'+self.system.getName()+'")\n')
        sf.write('\t\t{\n')

        sf.write('\t\t\ttta_cps.clk(main_clk);\n')
        sf.write('\t\t\ttta_cps.rst_x(rstx);\n')

        for i, ttaCore in enumerate(self.system.getAllTTACores()):
            sf.write('\t\t\ttta_cps.clk_'+ttaCore.getCoreId()+'('+ttaCore.getCoreId()+'_clk);\n')
            sf.write('\t\t\ttta_cps.busy_'+ttaCore.getCoreId()+'(s_glock_'+ttaCore.getCoreId()+');\n')
            sf.write('\t\t\ttta_cps.rst_' + ttaCore.getCoreId() + '(rstx);\n')

        for memory in self.system.getAllHostInterfaceMemories():
            for core in memory.getHostConnections():
                for suffix in memory.rtlIfaceSuffix:
                    sf.write('\t\t\ttta_cps.' + memory.getName() + '_'+core.getCoreId()+'_p0_'+suffix+'(w_'+ memory.getName() + '_'+core.getCoreId()+'_'+suffix+ ');\n')

                for i,suffix in enumerate(memory.rtlIfaceSuffix):
                    signals = ['mem_en_x', 'wr_en_x', 'bytemask', 'addr','d','q','waitReq']
                    sf.write('\t\t\tfifo_iface_'+core.getCoreId()+'_'+memory.getName()+'.'+signals[i]+'(w_'+ memory.getName() + '_'+core.getCoreId()+'_'+suffix+ ');\n')

                sf.write('\t\t\tfifo_iface_'+core.getCoreId()+'_'+memory.getName()+'.waitReq(w_' + memory.getName() + '_' + core.getCoreId() + '_waitReq);\n')
                sf.write('\t\t\tfifo_iface_' + core.getCoreId() + '_' + memory.getName() + '.clk(main_clk);\n')

                sf.write('\t\t\tSC_THREAD(sc_main_body);\n')
                for core in self.system.getAllHostCores():
                    sf.write('\t\t\t SC_THREAD(thread_' + core.getCoreId() + ');\n')
                sf.write('\n')

        sf.write('\t\t}\n')

        sf.write('};\n')
        sf.write('#endif')

        sf.write('\n')

        sf.write('void testbench_'+self.system.getName()+'::sc_main_body(){\n\n')

        for line in self.main_body_lines:
            sf.write('\t'+line)

        sf.write('\trstx.write(0);\n')
        sf.write('\twait(100.0,SC_NS);\n')
        sf.write('\trstx.write(1);\n')
        sf.write('\twait(100,SC_NS);\n')
        sf.write('\tcout << "Simulation starts!\\n";\n')
        sf.write('\n}\n')

        for core in self.system.getAllHostCores():
            sf.write('void testbench_' + self.system.getName() + '::thread_'+core.getCoreId()+'(){\n\n')

            for line in self.main_body_lines:
                sf.write('\t' + line)

            sf.write('\twait(1000,SC_NS);\n')
            sf.write('\tcout << "Creating host thread thr_'+core.getCoreId()+'!\\n";\n')
            sf.write('\tstd::thread thr_'+core.getCoreId()+'('+core.getCoreId()+'_main);\n')
            sf.write('\twhile(!KILLNETWORK){\n')
            sf.write('\t\twait(1000.0,SC_NS);\n')
            sf.write('\t}\n')
            sf.write('\tthr_'+core.getCoreId()+'.join();\n')
            sf.write('\tcout << "Host thread thr_' + core.getCoreId() + ' closed!\\n";\n')

            #sf.write(self.addTab(self.hostActorThreads(), 1))
            #sf.write('\n')
            #sf.write(self.addTab(self.joinHostActorThreads(), 1))

            sf.write('\n}\n')

        sf.write('SC_MODULE_EXPORT(testbench_'+self.system.getName()+')')

        sf.close()


class systemCRuntimeGenerator():

    def __init__(self, system, rootdir):

        self.rootdir = rootdir
        self.toplevelSourceFile = ''
        self.headerList = ['<systemc.h>',
                           '<iostream>',
                           '<fstream>',
                           '<thread>',
                           '<signal.h>',
                           '<stdio.h>',
                           '<stdlib.h>',
                           '<unistd.h>',
                           '<tce_systemc.hh>',
                           '"tta_mem_arbiter.h"',
                           '"lsu_be.h"',
                           '"lsu.h"',
                           '"globalLockOR.h"',
                           '"host_fifo_interface.h"',
                           '"n_port_ram_module.h"'
                           ]

        self.system = system
        self.tracedebugalias = 'TTADF_DEBUG_TRACES'

    def addTab(self,string, nbtabs):
        string = '\t' + string
        return string.replace("\n", "\n"+"\t"*nbtabs)


    def hostActorInclude(self):

        if len(self.system.getAllX86Cores()):
            source = 'volatile int KILLNETWORK = 0;\n'
            source += 'extern "C" {\n'
            for core in self.system.getAllX86Cores():
                source += '    #include "'+core.coreId+'/src/'+core.coreId+'_main.h"\n'
            source += '}\n'

        return source

    def hostActorThreads(self):

        content = ''
        for x86core in self.system.getAllX86Cores():
            content += 'std::thread '+ x86core.coreId+'_thread('+x86core.coreId +'_main);\n'

        return content

    def joinHostActorThreads(self):
        content = ''
        for x86core in self.system.getAllX86Cores():
            content += x86core.coreId+'_thread.join();\n'

        return content

    def hostMemoryInterfaces(self):

        source = ''

        #FIFOS BETWEEN X86 HOST and TTA cores
        x86InterfaceFifos = []
        x86InterfaceMems = []
        x86InterfaceCores = []

        #FIFOS BETWEEN X86 CORES
        x86_x86InterfaceFifos = []
        x86_x86InterfaceMems = []
        x86_x86InterfaceCores = []


        for memory in self.system.memories:
            for fifo in memory.fifos:
                if (fifo.source.owner.arch == 'X86' and fifo.target.owner.arch == 'TTA') or (fifo.source.owner.arch == 'TTA'and fifo.target.owner.arch == 'X86'):
                    x86InterfaceFifos.append(fifo)
                    x86InterfaceMems.append(memory)
                    x86InterfaceCores.append(memory.owner)
                if (fifo.source.owner.arch == 'X86' and fifo.target.owner.arch == 'X86') and (fifo.source.owner.coreId != fifo.target.owner.coreId):
                    x86_x86InterfaceFifos.append(fifo)
                    if memory not in x86_x86InterfaceMems:
                        x86_x86InterfaceMems.append(memory)
                    x86_x86InterfaceCores.append(memory.owner)

        for fifo in x86InterfaceFifos:
            source += 'unsigned char * ' + fifo.fifoId.upper() + '_BASEADDR;\n'
        for fifo in x86_x86InterfaceFifos:
            source += 'unsigned char * ' + fifo.fifoId.upper() + '_BASEADDR;\n'

        return source

    def keyboardInterruptHandlerCode(self):
        code =  ''
        code += 'void kbdIntHandler(int s, siginfo_t *siginfo, void *context){\n'
        code += '    printf("\\nCaught signal %d\\n",s);\n'
        code += '    printf("Stopping simulation!\\n");\n'
        code += '    sc_stop();\n'
        code += '    #ifdef ' + self.tracedebugalias + '\n'
        code += '    printf("Closing trace file!\\n");\n'
        code += '    sc_close_vcd_trace_file(Tf);\n'
        code += '    #endif\n'
        code += '    printTTAdata(global_tta_core_list, global_tta_core_nb);\n'
        code += '    exit(1);\n'
        code += '}\n'

        return code


    def setKbdHandlerCode(self):
        code = ''
        code += 'struct sigaction sigIntHandler;\n'
        code += 'sigIntHandler.sa_sigaction  = &kbdIntHandler;\n'
        code += 'sigemptyset(&sigIntHandler.sa_mask);\n'
        code += 'sigIntHandler.sa_flags = SA_SIGINFO;\n'
        code += 'sigaction(SIGINT, &sigIntHandler, NULL);\n'

        return code

    def printTTAcoresStatus(self):
        code = 'void printTTAdata(TTACore **listCores, unsigned int nbCores){\n'
        code += '   unsigned int i;\n'
        code += '   for(i=0;i<nbCores;i++){\n'
        #code += '       cout << "Core name : " << listCores[i]name << "\\n";\n'
        code += '       cout << "instructions cycles: " << listCores[i]->instructionCycles() << "\\n";\n'
        code += '       cout << "lock cycles: " << listCores[i]->lockCycles() << "\\n\\n";\n'
        code += '       cout << "Total cycles: " << listCores[i]->lockCycles()+listCores[i]->instructionCycles() << "\\n\\n";\n'
        code += '   }'
        code += '}'
        return code

    def createSource(self, filename):
        sf = open(self.rootdir+'/'+filename, "w")

        for header in self.headerList:
            sf.write('#include ' + header + '\n')


        sf.write('\n')
        sf.write('#ifdef '+ self.tracedebugalias+ '\n')
        sf.write('sc_trace_file * Tf;\n')
        sf.write('#endif\n')

        sf.write('TTACore **global_tta_core_list;\n')
        sf.write('unsigned int global_tta_core_nb;\n')
        sf.write('\n')

        sf.write('\n')
        sf.write(self.printTTAcoresStatus())
        sf.write('\n')
        sf.write('\n')
        sf.write(self.keyboardInterruptHandlerCode())
        sf.write('\n')
        sf.write(self.hostActorInclude())

        sf.write('\n')
        sf.write(self.hostMemoryInterfaces())
        sf.write('\n')

        sf.write('\n\nint sc_main(int argc, char* argv[]){')


        sf.write('\n')
        sf.write('\n')
        sf.write(self.addTab(self.setKbdHandlerCode(),1))
        sf.write('\n')

        sf.write('#ifdef '+ self.tracedebugalias+ '\n')
        sf.write('\tTf = sc_create_vcd_trace_file("traces");\n')
        sf.write('\tTf->set_time_unit(1, SC_PS);\n')
        sf.write('#endif\n')

        sf.write('\n')
        sf.write(self.addTab(self.createClockSignals(),1))
        sf.write('\n')
        sf.write(self.addTab(self.createGlobalLockSignals(),1))
        sf.write('\n')
        sf.write(self.addTab(self.createSharedMemories(),1))
        sf.write('\n')
        sf.write(self.addTab(self.createWiresCoreMemory(),1))
        sf.write('\n')
        sf.write(self.addTab(self.createCores(),1))
        sf.write('\n')
        sf.write(self.addTab(self.connectCoreMemory(),1))
        sf.write('\n')


        sf.write('\trstx = 0;\n')
        sf.write('\tsc_start(sc_time(10.0,SC_NS));\n')
        sf.write('\trstx = 1;\n')
        sf.write('\tsc_start(sc_time(1000.0,SC_NS));\n')
        sf.write('\tcout << "Simulation starts!\\n";\n')
        sf.write(self.addTab(self.hostActorThreads(),1))
        sf.write('\n')

        sf.write('\tunsigned long timer = 0;\n')

        sf.write('\twhile(!KILLNETWORK){\n')
        sf.write('\t\tsc_start(sc_time(10,SC_US));\n')
        sf.write('\t\ttimer++;\n')
        sf.write('\t}\n')

        sf.write(self.addTab(self.joinHostActorThreads(),1))
        sf.write('#ifdef '+ self.tracedebugalias+ '\n')
        sf.write('\n\tsc_close_vcd_trace_file(Tf);\n')
        sf.write('\t#endif\n')

        sf.write('\tprintTTAdata(global_tta_core_list, global_tta_core_nb);\n')
        sf.write('\tprintf("real time was %lu microseconds\\n", timer*10);\n')

        sf.write('\treturn EXIT_SUCCESS;\n')

        sf.write('}\n')

        sf.close()

    def createClockSignals(self):


        clkSourceCode = '\n//Create clocks for TTA Cores\n'

        maxClock = 0
        for i,ttaCore in enumerate(self.system.getAllTTACores()):
            clkSourceCode += 'sc_clock '+ttaCore.coreId+'_clk("'+ttaCore.coreId+'_clk", '+ str(1.0/ttaCore.clkf)+', SC_US);\n'
            if ttaCore.clkf > maxClock:
                maxClock = ttaCore.clkf

        for i,x86Core in enumerate(self.system.getAllX86Cores()):
            if x86Core.clkf > maxClock:
                maxClock = x86Core.clkf

        clkSourceCode += 'sc_clock main_clk("main_clk", '+str(1.0/maxClock)+', SC_US);\n'

        clkSourceCode += '#ifdef '+ self.tracedebugalias+ '\n'
        clkSourceCode += 'sc_trace(Tf, main_clk, "main_clk");\n'
        clkSourceCode += '#endif\n'

        clkSourceCode += 'sc_signal<bool> rstx;\n'

        #clkSourceCode += '\n//Create clocks for other cores\n'

        #for i,ttaCore in enumerate(self.system.getAllTTACores()):
        #    clkSourceCode += 'sc_clock '+ttaCore.coreId+'_clk("'+ttaCore.coreId+'_clk", '+ str(1.0/ttaCore.clkf)+', SC_US);\n'

        return clkSourceCode

    def createGlobalLockSignals(self):
        sourceCode = '\n//Create global lock signals for TTA Cores\n'

        for i,ttaCore in enumerate(self.system.getAllTTACores()):
            sourceCode += 'sc_signal<bool> s_glock_'+ttaCore.coreId+';\n'
        return sourceCode

    def createSharedMemories(self):
        sourceCode = '\n//Create shared memories and memory arbiters\n'
        for i,smem in enumerate(self.system.memories):

            nbMemPorts = len(smem.getDirectConnections())
            if smem.getArbiter():
                nbMemPorts = nbMemPorts + 1


            portsg = str(len(smem.getArbiterConnections()))
            addrw_g = str(int(math.ceil(math.log((smem.maxAddress+1)/4,2))))
            dataw_g = str(32)
            memLen = str(int(((smem.maxAddress+1)/4)))

            ramName = smem.name+'_ram'


            sourceCode += 'sc_signal <bool> ram_en_x_'+smem.name+'['+str(nbMemPorts) +'];\n'
            sourceCode += 'sc_signal <bool> ram_wr_x_'+smem.name+'['+str(nbMemPorts) +'];\n'
            sourceCode += 'sc_signal <sc_bv <'+dataw_g+'>> ram_d_'+smem.name+'['+str(nbMemPorts) +'];\n'
            sourceCode += 'sc_signal <sc_bv <'+dataw_g+'>> ram_q_'+smem.name+'['+str(nbMemPorts) +'];\n'
            sourceCode += 'sc_signal <sc_bv <'+dataw_g+'/8>> ram_bit_wr_x_'+smem.name+'['+str(nbMemPorts) +'];\n'
            sourceCode += 'sc_signal <sc_bv <'+addrw_g+'>> ram_addr_'+smem.name+'['+str(nbMemPorts) +'];\n'

            sourceCode += 'n_port_ram_module<'+memLen+', '+addrw_g+', '+dataw_g+', '+str(nbMemPorts)+', true > '+ ramName+'("'+ramName+'", "'+smem.name+'.mif");\n'
            sourceCode += ramName+'.clk(main_clk);\n'

            if smem.arbiter:
                sourceCode += ramName+'.addr[0](ram_addr_'+smem.name+'[0]);\n'
                sourceCode += ramName+'.bytemask[0](ram_bit_wr_x_'+smem.name+'[0]);\n'
                sourceCode += ramName+'.dataOut[0](ram_q_'+smem.name+'[0]);\n'
                sourceCode += ramName+'.wr_en_x[0](ram_wr_x_'+smem.name+'[0]);\n'
                sourceCode += ramName+'.mem_en_x[0](ram_en_x_'+smem.name+'[0]);\n'
                sourceCode += ramName+'.dataIn[0](ram_d_'+smem.name+'[0]);\n'


                sourceCode += 'tta_mem_arbiter<' + portsg +', '+addrw_g+', '+dataw_g+', '+ memLen +'> ' + smem.name+'("'+smem.name+'");\n'
                sourceCode += smem.name+'.clk(main_clk);\n'
                sourceCode += smem.name+'.rst_n(rstx);\n'
                sourceCode += smem.name + '.ram_addr(ram_addr_' + smem.name + '[0]);\n'
                sourceCode += smem.name + '.ram_bit_wr_x(ram_bit_wr_x_' + smem.name + '[0]);\n'
                sourceCode += smem.name + '.ram_q(ram_q_' + smem.name + '[0]);\n'
                sourceCode += smem.name + '.ram_wr_x(ram_wr_x_' + smem.name + '[0]);\n'
                sourceCode += smem.name + '.ram_en_x(ram_en_x_' + smem.name + '[0]);\n'
                sourceCode += smem.name + '.ram_d(ram_d_' + smem.name + '[0]);\n'



            for connection in smem.connections:
                if connection.arch == 'X86':
                    print('[INFO] FOUND HOST INTERFACE MEMORY ')
                    sourceCode += '//Create intermediate memory storage for host and connect them\n'
                    sourceCode += 'unsigned int *hostIntermediateMem_'+smem.name+' = new unsigned int ['+memLen+'];\n'


                    hostInputFifo = []
                    hostOutputFifo = []

                    for fifo in smem.fifos:
                        if fifo.source.owner.arch == 'X86' and fifo.target.owner.arch == 'TTA':
                            sourceCode += fifo.fifoId.upper() + '_BASEADDR = (unsigned char *) hostIntermediateMem_'+smem.name+';\n'
                            hostOutputFifo.append(fifo)
                        if fifo.source.owner.arch == 'TTA' and fifo.target.owner.arch == 'X86':
                            sourceCode += fifo.fifoId.upper() + '_BASEADDR = (unsigned char *) hostIntermediateMem_' + smem.name + ';\n'
                            hostInputFifo.append(fifo)
                    break

        return sourceCode
    def createWiresCoreMemory(self):

        sourceCode = '\n//\n'
        for i,core in enumerate(self.system.getAllTTACores()):
            for j,mem in enumerate(core.externalMems):
                sourceCode += 'sc_signal<sc_bv<'+str(int(math.ceil(math.log((mem.maxAddress+1)/4,2))))+'> > addr_'+core.coreId+'_'+mem.name+';\n'
                sourceCode += 'sc_signal<sc_bv<32> > data_'+core.coreId+'_'+mem.name+';\n'
                sourceCode += 'sc_signal<sc_bv<32> > data_' + mem.name + '_' + core.coreId + ';\n'
                sourceCode += 'sc_signal<sc_bv<4> > bytemask_'+core.coreId+'_'+mem.name+';\n'
                sourceCode += 'sc_signal<bool> wr_en_x_'+core.coreId+'_'+mem.name+';\n'
                sourceCode += 'sc_signal<bool> mem_en_x_' + core.coreId + '_' + mem.name + ';\n'
                sourceCode += 'sc_signal<bool> mem_wait_' +  mem.name + '_' + core.coreId + ';\n\n'
                sourceCode += '#ifdef '+ self.tracedebugalias+ '\n'
                sourceCode += 'sc_trace(Tf, addr_'+core.coreId+'_'+mem.name+', "addr_'+core.coreId+'_'+mem.name+'");\n'
                sourceCode += 'sc_trace(Tf, data_'+core.coreId+'_'+mem.name+', "data_'+core.coreId+'_'+mem.name+'");\n'
                sourceCode += 'sc_trace(Tf, data_'+mem.name+'_'+core.coreId+', "data_'+ mem.name+'_'+core.coreId+'");\n'
                sourceCode += 'sc_trace(Tf, bytemask_'+core.coreId+'_'+mem.name+', "bytemask_'+core.coreId+'_'+mem.name+'");\n'
                sourceCode += 'sc_trace(Tf, wr_en_x_'+core.coreId+'_'+mem.name+', "wr_en_x_'+core.coreId+'_'+mem.name+'");\n'
                sourceCode += 'sc_trace(Tf, mem_en_x_'+core.coreId+'_'+ mem.name + ', "mem_en_x_' + core.coreId + '_' + mem.name + '");\n'
                sourceCode += 'sc_trace(Tf, mem_wait_'+ mem.name+'_'+core.coreId + ', "mem_wait_' +  mem.name + '_' + core.coreId + '");\n'
                sourceCode += '#endif\n\n'



        for i, core in enumerate(self.system.getAllX86Cores()):
            for j, mem in enumerate(core.externalMems):
                sourceCode += 'sc_signal<sc_bv<' + str(
                    int(math.ceil(math.log((mem.maxAddress+1)/4, 2)))) + '> > addr_' + core.coreId + '_' + mem.name + ';\n'
                sourceCode += 'sc_signal<sc_bv<32> > data_' + core.coreId + '_' + mem.name + ';\n'
                sourceCode += 'sc_signal<sc_bv<32> > data_' + mem.name + '_' + core.coreId + ';\n'
                sourceCode += 'sc_signal<sc_bv<4> > bytemask_' + core.coreId + '_' + mem.name + ';\n'
                sourceCode += 'sc_signal<bool> wr_en_x_' + core.coreId + '_' + mem.name + ';\n'
                sourceCode += 'sc_signal<bool> mem_en_x_' + core.coreId + '_' + mem.name + ';\n'
                sourceCode += 'sc_signal<bool> mem_wait_' + mem.name + '_' + core.coreId + ';\n\n'

                sourceCode += '#ifdef '+ self.tracedebugalias+ '\n'
                sourceCode += 'sc_trace(Tf, addr_'+core.coreId+'_'+mem.name+', "addr_'+core.coreId+'_'+mem.name+'");\n'
                sourceCode += 'sc_trace(Tf, data_'+core.coreId+'_'+mem.name+', "data_'+core.coreId+'_'+mem.name+'");\n'
                sourceCode += 'sc_trace(Tf, data_'+mem.name+'_'+core.coreId+', "data_'+ mem.name+'_'+core.coreId+'");\n'
                sourceCode += 'sc_trace(Tf, bytemask_'+core.coreId+'_'+mem.name+', "bytemask_'+core.coreId+'_'+mem.name+'");\n'
                sourceCode += 'sc_trace(Tf, wr_en_x_'+core.coreId+'_'+mem.name+', "wr_en_x_'+core.coreId+'_'+mem.name+'");\n'
                sourceCode += 'sc_trace(Tf, mem_en_x_'+core.coreId+'_'+ mem.name + ', "mem_en_x_' + core.coreId + '_' + mem.name + '");\n'
                sourceCode += 'sc_trace(Tf, mem_wait_'+ mem.name+'_'+core.coreId + ', "mem_wait_' +  mem.name + '_' + core.coreId + '");\n'
                sourceCode += '#endif\n\n'


        return sourceCode
    def createCores(self):
        sourceCode = '\n'

        sourceCode = 'TTACore *tta_core_list['+ str(len(self.system.getAllTTACores())) +'];\n'
        sourceCode += 'global_tta_core_list = tta_core_list;\n'
        sourceCode += 'global_tta_core_nb = '+ str(len(self.system.getAllTTACores())) + ';\n'


        for i,c in enumerate(self.system.getAllTTACores()):
            coreADFFile = c.coreId + '/' + c.coreId +'.adf'
            coreProgram = c.coreId +  '/' + c.coreId+'.tpef'
            sourceCode += 'TTACore ' + c.coreId + '("' +c.coreId+'", "'+ coreADFFile + '", "' +coreProgram+ '"); \n'
            sourceCode += 'tta_core_list['+str(i)+'] = &'+ c.coreId +';\n'
            sourceCode += c.coreId+'.clock('+ c.coreId+'_clk);\n'
            #sourceCode += c.coreId + '.rstx(rstx);\n'
            sourceCode += c.coreId+'.global_lock(s_glock_' + c.coreId+');\n'
            if len(c.externalMems):
                sourceCode += 'globalLockOR<' + str(len(c.externalMems)) + '> glock_modules_'+ c.coreId +'("glock_module_'+c.coreId+'"); \n'
                sourceCode += 'glock_modules_' + c.coreId + '.glock(s_glock_' + c.coreId + ');\n'
                for i,mem in enumerate(c.externalMems):
                    sourceCode += 'glock_modules_' + c.coreId + '.glocks['+str(i)+'](mem_wait_' + mem.name +'_'+ c.coreId +');\n'
            sourceCode += '\n'
        return sourceCode

    def connectCoreMemory(self):
        sourceCode = '\n'


        for i, c in enumerate(self.system.getAllX86Cores()):
            for mem in c.externalMems:

                startIndex = 0
                if mem.arbiter:
                    startIndex = 1


                if c in mem.getArbiterConnections():
                    connection_index = str(mem.getArbiterConnections().index(c))
                    sourceCode += mem.name + '.bit_wr_x['+connection_index+'](bytemask_'+c.coreId+'_'+mem.name+');\n'
                    sourceCode += mem.name + '.en_x[' + connection_index + '](mem_en_x_' + c.coreId + '_' + mem.name + ');\n'
                    sourceCode += mem.name + '.wr_x[' + connection_index + '](wr_en_x_' + c.coreId + '_' + mem.name + ');\n'
                    sourceCode += mem.name + '.addr[' + connection_index + '](addr_' + c.coreId + '_' + mem.name + ');\n'
                    sourceCode += mem.name + '.d[' + connection_index + '](data_' + c.coreId + '_' + mem.name + ');\n'
                    sourceCode += mem.name + '.q[' + connection_index + '](data_' + mem.name + '_' + c.coreId + ');\n'
                    sourceCode += mem.name + '.waitrequest[' + connection_index + '](mem_wait_' + mem.name + '_' + c.coreId + ');\n\n'



                if c in mem.getDirectConnections():
                    connection_index = str(mem.getDirectConnections().index(c)+startIndex)
                    sourceCode += mem.name + '_ram.bytemask['+connection_index+'](bytemask_'+c.coreId+'_'+mem.name+');\n'
                    sourceCode += mem.name + '_ram.mem_en_x[' + connection_index + '](mem_en_x_' + c.coreId + '_' + mem.name + ');\n'
                    sourceCode += mem.name + '_ram.wr_en_x[' + connection_index + '](wr_en_x_' + c.coreId + '_' + mem.name + ');\n'
                    sourceCode += mem.name + '_ram.addr[' + connection_index + '](addr_' + c.coreId + '_' + mem.name + ');\n'
                    sourceCode += mem.name + '_ram.dataIn[' + connection_index + '](data_' + c.coreId + '_' + mem.name + ');\n'
                    sourceCode += mem.name + '_ram.dataOut[' + connection_index + '](data_' + mem.name + '_' + c.coreId + ');\n'




                addrw_g = str(int(math.ceil(math.log((mem.maxAddress+1)/4, 2))))
                dataw_g = str(32)
                memLen = str(int(((mem.maxAddress + 1) / 4)))

                hostInputFifo = []
                hostOutputFifo = []

                for fifo in mem.fifos:
                    if fifo.source.owner.arch == 'X86' and fifo.target.owner.arch == 'TTA':
                        hostOutputFifo.append(fifo)
                    if fifo.source.owner.arch == 'TTA' and fifo.target.owner.arch == 'X86':
                        hostInputFifo.append(fifo)

                sourceCode += 'unsigned int * input_fifo_addrs_' + mem.name + ' = new unsigned int [' + str(len(hostInputFifo))+'];\n'
                for i,fifo in enumerate (hostInputFifo):
                    sourceCode += 'input_fifo_addrs_' + mem.name + '[' +str(i)+ '] = ' + str(fifo.startAddr) + ';\n'


                sourceCode += 'unsigned int * output_fifo_addrs_' + mem.name + ' = new unsigned int [' + str(len(hostOutputFifo)) +'];\n'
                for i,fifo in enumerate (hostOutputFifo):
                    sourceCode += 'output_fifo_addrs_' + mem.name + '[' +str(i) + '] = ' + str(fifo.startAddr) + ';\n'


                ifaceInstance = 'fifo_iface_' + c.coreId+ '_' + mem.name

                sourceCode += 'host_fifo_interface<' + memLen + ', ' + addrw_g + ', ' + dataw_g + ',4> ' + ifaceInstance + '('
                sourceCode += '"hostMemInterface_' + mem.name + '", hostIntermediateMem_' + mem.name + ', ' + str(
                    len(hostOutputFifo)) + ', output_fifo_addrs_' + mem.name + ', '
                sourceCode += str(len(hostInputFifo)) + ', input_fifo_addrs_' + mem.name + ');\n\n'

                sourceCode += ifaceInstance + '.clk(main_clk);\n'
                sourceCode += ifaceInstance + '.bytemask(bytemask_' + c.coreId + '_' + mem.name + ');\n'
                sourceCode += ifaceInstance + '.mem_en_x(mem_en_x_' + c.coreId + '_' + mem.name + ');\n'
                sourceCode += ifaceInstance + '.wr_en_x(wr_en_x_' + c.coreId + '_' + mem.name + ');\n'
                sourceCode += ifaceInstance + '.addr(addr_' + c.coreId + '_' + mem.name + ');\n'
                sourceCode += ifaceInstance + '.d(data_' + c.coreId + '_' + mem.name + ');\n'
                sourceCode += ifaceInstance + '.q(data_' + mem.name + '_' + c.coreId + ');\n'
                sourceCode += ifaceInstance + '.waitReq(mem_wait_' + mem.name + '_' + c.coreId + ');\n\n'



        for i, c in enumerate(self.system.getAllTTACores()):

            # DATA MEM
            '''
            lsuInstance = c.coreId + '_lsu_DATA'

            addrw_g = str(18)
            memLen =str( 2**int(addrw_g))
            nbMemPorts = 1

            dmem_name = 'LSU_DATAMEM'
            lsuname = dmem_name
            ramName = dmem_name+'_ram'
            mem_init_filename = c.coreId+'/'+c.coreId+'_data.img'


            sourceCode += 'sc_signal <bool> ram_en_x_'+dmem_name+'['+str(nbMemPorts) +'];\n'
            sourceCode += 'sc_signal <bool> ram_wr_x_'+dmem_name+'['+str(nbMemPorts) +'];\n'
            sourceCode += 'sc_signal <sc_bv <'+dataw_g+'>> ram_d_'+dmem_name+'['+str(nbMemPorts) +'];\n'
            sourceCode += 'sc_signal <sc_bv <'+dataw_g+'>> ram_q_'+dmem_name+'['+str(nbMemPorts) +'];\n'
            sourceCode += 'sc_signal <sc_bv <'+dataw_g+'/8>> ram_bit_wr_x_'+dmem_name+'['+str(nbMemPorts) +'];\n'
            sourceCode += 'sc_signal <sc_bv <'+addrw_g+'>> ram_addr_'+dmem_name+'['+str(nbMemPorts) +'];\n'

            sourceCode += 'n_port_ram_module<'+memLen+', '+addrw_g+', '+dataw_g+', '+str(nbMemPorts)+',true> '+ ramName+'("'+ramName+'","'+mem_init_filename+'");\n'
            sourceCode += ramName+'.clk(main_clk);\n'

            sourceCode += ramName + '.addr[0](ram_addr_' + dmem_name + '[0]);\n'
            sourceCode += ramName + '.bytemask[0](ram_bit_wr_x_' + dmem_name + '[0]);\n'
            sourceCode += ramName + '.dataOut[0](ram_q_' + dmem_name + '[0]);\n'
            sourceCode += ramName + '.wr_en_x[0](ram_wr_x_' + dmem_name + '[0]);\n'
            sourceCode += ramName + '.mem_en_x[0](ram_en_x_' + dmem_name + '[0]);\n'
            sourceCode += ramName + '.dataIn[0](ram_d_' + dmem_name + '[0]);\n'

            sourceCode += 'lsu_be<' + addrw_g + '> ' + lsuInstance + '("' + lsuInstance + '");\n'
            sourceCode += '//'+c.coreId + '.setOperationSimulator("'+lsuname+'",' + lsuInstance + ');\n'
            sourceCode += lsuInstance + '.bit_wr_x(ram_bit_wr_x_' + dmem_name + '[0]);\n'
            sourceCode += lsuInstance + '.en_x(ram_en_x_' + dmem_name + '[0]);\n'
            sourceCode += lsuInstance + '.wr_x(ram_wr_x_' + dmem_name + '[0]);\n'
            sourceCode += lsuInstance + '.addr(ram_addr_' + dmem_name + '[0]);\n'
            sourceCode += lsuInstance + '.d(ram_d_' + dmem_name + '[0]);\n'
            sourceCode += lsuInstance + '.q(ram_q_' + dmem_name + '[0]);\n\n'
            '''

            for mem in c.externalMems:

                startIndex = 0
                if mem.arbiter:
                    startIndex = 1

                if c in mem.getArbiterConnections():
                    connection_index = str(mem.getArbiterConnections().index(c))
                    sourceCode += mem.name + '.bit_wr_x['+connection_index+'](bytemask_'+c.coreId+'_'+mem.name+');\n'
                    sourceCode += mem.name + '.en_x[' + connection_index + '](mem_en_x_' + c.coreId + '_' + mem.name + ');\n'
                    sourceCode += mem.name + '.wr_x[' + connection_index + '](wr_en_x_' + c.coreId + '_' + mem.name + ');\n'
                    sourceCode += mem.name + '.addr[' + connection_index + '](addr_' + c.coreId + '_' + mem.name + ');\n'
                    sourceCode += mem.name + '.d[' + connection_index + '](data_' + c.coreId + '_' + mem.name + ');\n'
                    sourceCode += mem.name + '.q[' + connection_index + '](data_' + mem.name + '_' + c.coreId + ');\n'
                    sourceCode += mem.name + '.waitrequest[' + connection_index + '](mem_wait_' + mem.name + '_' + c.coreId + ');\n\n'



                if c in mem.getDirectConnections():
                    connection_index = str(mem.getDirectConnections().index(c)+startIndex)
                    sourceCode += mem.name + '_ram.bytemask['+connection_index+'](bytemask_'+c.coreId+'_'+mem.name+');\n'
                    sourceCode += mem.name + '_ram.mem_en_x[' + connection_index + '](mem_en_x_' + c.coreId + '_' + mem.name + ');\n'
                    sourceCode += mem.name + '_ram.wr_en_x[' + connection_index + '](wr_en_x_' + c.coreId + '_' + mem.name + ');\n'
                    sourceCode += mem.name + '_ram.addr[' + connection_index + '](addr_' + c.coreId + '_' + mem.name + ');\n'
                    sourceCode += mem.name + '_ram.dataIn[' + connection_index + '](data_' + c.coreId + '_' + mem.name + ');\n'
                    sourceCode += mem.name + '_ram.dataOut[' + connection_index + '](data_' + mem.name + '_' + c.coreId + ');\n'


            for lsu in c.loadStoreUnit:
                lsuInstance = c.coreId + '_lsu_' + lsu[1]



                try:
                    if c.getMemory(lsu[0].name).type == 'shared':

                        addrw_g = str(int(math.ceil(math.log((c.getMemory(lsu[0].name).maxAddress+1)/4, 2))))

                        con_idx = str(c.getMemory(lsu[0].name).connections.index(c))
                        sourceCode += 'lsu<' +addrw_g+ '> ' + lsuInstance + '("'+lsuInstance+'");\n'
                        sourceCode += c.coreId + '.setOperationSimulator("'+lsu[1]+'",'+lsuInstance+');\n'
                        sourceCode += lsuInstance + '.bit_wr_x(bytemask_'+c.coreId+'_'+lsu[0].name+');\n'
                        sourceCode += lsuInstance + '.en_x(mem_en_x_' + c.coreId + '_' + lsu[0].name + ');\n'
                        sourceCode += lsuInstance + '.wr_x(wr_en_x_' + c.coreId + '_' + lsu[0].name + ');\n'
                        sourceCode += lsuInstance + '.addr(addr_' + c.coreId + '_' + lsu[0].name + ');\n'
                        sourceCode += lsuInstance + '.d(data_' + c.coreId + '_' + lsu[0].name + ');\n'
                        sourceCode += lsuInstance + '.q(data_' + lsu[0].name + '_' + c.coreId + ');\n\n'
                except AttributeError:
                    pass

        return sourceCode
