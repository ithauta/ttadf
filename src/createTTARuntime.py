# /usr/bin/python
# -*- coding: utf-8 -*-

#This file is part of TTADF framework.

#MIT License

#Copyright (c) 2018 Ilkka Hautala, CMVS, University of Oulu, Finland

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

from functools import reduce

from lxml import etree, objectify
from optparse import OptionParser
from subprocess import call, check_output
from shutil import copy2
import os
import math
import copy
import TTADF_Tools


from TTADFParser import TTADFParser

from TTADF_Tools import *
from Network import Network
from Architecture import Architecture
from Mapping import Mapping
from RuntimeCore import RuntimeCore, RuntimeCoreTTA, RuntimeCoreX86
from RuntimeFifo import RuntimeFifo
from RuntimeSystem import RuntimeSystem
from RuntimeMemory import MemoryObject, Arbiter
from RuntimeActor import RuntimeActor
import systemCRuntime
from vhdlNetworkGenerator import VHDLEntityParser
from vhdlTTASystemGenerator import vhdlTTASystemGenerator, vhdlTTACoreWrapper

class RuntimeCreator:
    def __init__(self, parser):

        parser.add_option("-n", "--network", action="store", type="string", dest="networkFilename", \
                          help="Input XML-file for dataflow network")
        parser.add_option("-m", "--mapping", action="store", type="string", dest="mappingFilename", \
                          help="Input XML-file for actor to core mapping")
        parser.add_option("-a", "--architecture", action="store", type="string", dest="architectureFilename", \
                          help="Input XML-file for system architecture description")
        parser.add_option("-o", "--output", action="store", type="string", dest="outputdir", \
                          help="Output directory path. Default is WORKDIR/NETWORKNAME ")
        parser.add_option("-C", "--enable-multiclocks", action="store_true", dest="multiclocks", default = False, \
                          help="Enables different clockfrequencies for cores, might slow down simulation!")

        parser.add_option("-H", "--use-headers", action="store", type="string", dest="headerfiles", default = '', \
                          help="Includes additional headers")

        parser.add_option("-g", "--gcc-path", action="store", type="string", dest="gccpath", default = "gcc", \
                          help="Set path for gcc compiler")


        (self.options,self.args) = parser.parse_args()

        self.globalDefines = None
        self.root = None
        self.runtime = None
        self.rootdir = None
        self.installDir = os.environ['TTADF_INSTALL_DIR']
        if not self.installDir:
            self.installDir = os.curdir()
        print('[INFO] TTADF installation directory is '+self.installDir)


    def getHDLDir(self):
        return self.rootdir+'/hdl'

    def getHDLSharedDir(self):
        return self.getHDLDir()+'/shared'

    def GCD(self,a, b):
        # Gives greatest common divisor using Euclid's Algorithm.
        while b:
            a, b = b, a % b
        return a

    def LCM(self,a, b):
        # gives lowest common multiple of two numbers
        return a * b // self.GCD(a, b)

    def LCMM(self,*args):
        # gives LCM of a list of numbers passed as argument
        return reduce(self.LCM, args)

    def GCDM(self,*args):
        return reduce(self.GCD, args)

    def isPowerOf2(self,x):
        return (x != 0) & ((x & (~x+1)) == x)


    def createFifoSourceFiles(self):

        for core in self.runtime.cores:
            # Determine different addressSpaces
            if core.arch =='TTA':
                asList = []
                for localmem in core.localMems:
                    addrspace = localmem.getAddressSpaceForCore(core)
                    asList.append(addrspace)
                for externalmem in core.externalMems:
                    addrspace = externalmem.getAddressSpaceForCore(core)
                    asList.append(addrspace)

            # generate common.h
            if core.arch == 'X86':
                fh = open(self.rootdir + "/common/common.h", "w")
            else:
                fh = open(core.homedir + "/src/common.h", "w")

            fh.write('/*This file is autogenerated do not modify*/\n')
            fh.write('#ifndef TTA_COMMON_H_\n')
            fh.write('#define TTA_COMMON_H_\n')
            fh.write('#include <stdint.h>\n')


            fh.write('#define SET_AS(x) __attribute__((address_space(x)))\n')
            #fh.write('uintptr_t ttadf_get_population(uintptr_t witem, unsigned int wr_overflow, uintptr_t ritem, unsigned int rd_overflow, unsigned int maxcap);\n')
            fh.write('uintptr_t ttadf_get_population(uintptr_t witem, uintptr_t ritem, unsigned int maxcap);\n')
            fh.write('__attribute__((noinline)) void ttadf_compiler_barrier();\n')
            fh.write('uintptr_t ttadf_rw_end(uintptr_t witem, unsigned int token_size, unsigned int bufCap); \n')

            fh.write('#endif\n')
            fh.close()

            # generate common.c
            if core.arch == 'X86':
                fh = open(self.rootdir + "/common/common.c", "w")
            else:
                fh = open(core.homedir + "/src/common.c", "w")

            fh.write('#include "common.h"\n')
            fh.write('#include <stdint.h>\n')

            #fh.write('uintptr_t ttadf_get_population(uintptr_t witem,  unsigned int wr_overflow, uintptr_t ritem,  unsigned int rd_overflow, unsigned int maxcap) {\n')
            #fh.write('    if(witem > ritem){ return witem-ritem; }\n')
            #fh.write('    else if(witem < ritem){ return witem-ritem-1;}\n')
            #fh.write('    else{return (wr_overflow ^ rd_overflow)*maxcap;} \n')
            #fh.write('}\n\n')

            fh.write('uintptr_t ttadf_get_population(uintptr_t witem, uintptr_t ritem, unsigned int maxcap) {\n')
            if core.isTTA() and core.hasHwFifoExtensionPopulation():
                fh.write('    uintptr_t out;\n')
                fh.write('    _TCE_TTADF_POPULATION(witem,ritem,maxcap,out);\n')
                #fh.write('    printf("witem: %u, ritem: %u, maxcap: %u\t population: %u\\n",witem, ritem, maxcap, out);\n')
                #fh.write('    printf("_TCE_TTADF_POPULATION CHECK %d\\n",out);\n')
                fh.write('    return out;\n')
            else:
                fh.write('    uintptr_t rd_of, wr_of, w , r;\n')
                fh.write('    rd_of = (ritem >> 31) & 1;\n')
                fh.write('    wr_of = (witem >> 31) & 1;\n')
                fh.write('    r = ritem & (~(1 << 31));\n')
                fh.write('    w = witem & (~(1 << 31));\n')
                fh.write('    if(w > r){ return (w-r); }\n')
                fh.write('    else if(w < r){ return (maxcap-r+w);}\n')
                fh.write('    else{return ((wr_of == rd_of) ? 0: maxcap);} \n')

            fh.write('}\n\n')

            fh.write('uintptr_t ttadf_rw_end(uintptr_t witem, unsigned int token_size, unsigned int bufCap) \n')
            fh.write('{\n')
            fh.write('    unsigned int ttadf_t_rw;\n')
            fh.write('    ttadf_t_rw = (witem & ~(1 << 31UL)) + token_size;\n')
            fh.write('    ttadf_t_rw |= witem & 0x80000000UL;\n')
            fh.write('    if ((ttadf_t_rw & ~(1 << 31UL)) == bufCap){\n')
            fh.write('        ttadf_t_rw = witem & 0x80000000UL;\n')
            fh.write('        ttadf_t_rw ^= (1 << 31UL);\n')
            fh.write('    }\n')
            fh.write('    return  0x00000000FFFFFFFFUL & ttadf_t_rw;\n')
            fh.write('}\n\n')

            fh.write('__attribute__((noinline)) void ttadf_compiler_barrier() \n')
            fh.write('{\n')
            fh.write('''    asm volatile("" : : : "memory");\n''')
            fh.write('}\n\n')



            fh.close()

            # generate fifo.h
            if core.arch == 'X86':
                fh = open(self.rootdir + "/common/fifo.h", "w")
            else:
                fh = open(core.homedir + "/src/fifo.h", "w")

            fh.write('/*This file is autogenerated do not modify*/\n')

            fh.write('#ifndef FIFO_H_\n')
            fh.write('#define FIFO_H_\n')

            fh.write('#include "common.h"\n')
            #fh.write('#include "mutex.h"\n')
            fh.write('#include <stdint.h>\n')

            fh.write('typedef struct s_fifo_struct fifoType;\n')

            #fh.write('''struct s_fifo_struct{\n''')
            #fh.write('''    int capacity;\n''')
            #fh.write('''    char *buffer_start;\n''')
            #fh.write('''    char *buffer_end;\n''')
            #fh.write('''    volatile int population;\n''')
            #fh.write('''    char *read_pointer;\n''')
            #fh.write('''    int read_item_no;\n''')
            #fh.write('''    char *write_pointer;\n''')
            #fh.write('''    int write_item_no;\n''')
            #fh.write('''    int token_size;\n''')
            #fh.write('''    tta_mutex fifo_mutex;\n''')
            #fh.write('''    volatile int consuming_stopped;\n''')
            #fh.write('''    volatile int production_stopped;\n''')
            #fh.write('''    unsigned int starving;\n''')
            #fh.write('''    unsigned int full;\n''')
            #fh.write('''};\n''')

            if core.arch == 'TTA':
                fh.write('struct s_fifo_struct{\n')
                fh.write('    unsigned int capacity;\n')
                fh.write('    uintptr_t buffer_start;\n')
                fh.write('    uintptr_t pad0;\n')
                fh.write('    uintptr_t buffer_end;\n')
                fh.write('    uintptr_t pad1;\n')
                fh.write('    volatile uintptr_t read_item_no;\n')
                fh.write('    volatile uintptr_t pad2;\n')
                fh.write('    volatile uintptr_t write_item_no;\n')
                fh.write('    volatile uintptr_t pad3;\n')
                fh.write('    volatile int consuming_stopped;\n')
                fh.write('    volatile int production_stopped;\n')
                fh.write('    volatile unsigned int rd_overflow;\n')
                fh.write('    volatile unsigned int wr_overflow;\n')
                fh.write('    unsigned int starving;\n')
                fh.write('    unsigned int full;\n')
                fh.write('};\n')
            else:
                if core.getWordSize() == 32:
                    fh.write('struct s_fifo_struct{\n')
                    fh.write('    unsigned int capacity;\n')
                    fh.write('    uintptr_t buffer_start;\n')
                    fh.write('    uintptr_t pad0;\n')
                    fh.write('    uintptr_t buffer_end;\n')
                    fh.write('    uintptr_t pad1;\n')
                    fh.write('    volatile uintptr_t read_item_no;\n')
                    fh.write('    volatile uintptr_t pad2;\n')
                    fh.write('    volatile uintptr_t write_item_no;\n')
                    fh.write('    volatile uintptr_t pad3;\n')
                    fh.write('    volatile int consuming_stopped;\n')
                    fh.write('    volatile int production_stopped;\n')
                    fh.write('    volatile unsigned int rd_overflow;\n')
                    fh.write('    volatile unsigned int wr_overflow;\n')
                    fh.write('    unsigned int starving;\n')
                    fh.write('    unsigned int full;\n')
                    fh.write('};\n')

                elif core.getWordSize() == 64:
                    fh.write('struct s_fifo_struct{\n')
                    fh.write('    unsigned int capacity;\n')
                    fh.write('    uintptr_t buffer_start;\n')
                    fh.write('    uintptr_t buffer_end;\n')
                    fh.write('    volatile uintptr_t read_item_no;\n')
                    fh.write('    volatile uintptr_t write_item_no;\n')
                    fh.write('    volatile int consuming_stopped;\n')
                    fh.write('    volatile int production_stopped;\n')
                    fh.write('    volatile unsigned int rd_overflow;\n')
                    fh.write('    volatile unsigned int wr_overflow;\n')
                    fh.write('    unsigned int starving;\n')
                    fh.write('    unsigned int full;\n')
                    #fh.write('}__attribute__((aligned (64)));\n')
                    fh.write('}__attribute__((packed));\n')
                else:
                    print('[ERROR] ' + core.coreId + ' has unsupported wordsize!\n')
                    exit()

            fh.write('''typedef fifoType *p_fifo;\n\n''')

            if core.arch == 'TTA':
                for asNo in asList:
                    fh.write('typedef fifoType SET_AS(' + str(asNo) + ')* p_fifo_as' + str(asNo) + ';\n\n')


            fh.write('''\n\n#endif\n''')
            fh.close()

            # Generate mutex.h
            # fh = open(core.homedir + "/src/mutex.h", "w")
            #
            # fh.write('''/*This file is autogenerated do not modify*/ \n''')
            # fh.write('''#ifndef TTA_MUTEX_H_\n''')
            # fh.write('''#define TTA_MUTEX_H_\n''')
            # fh.write('''#include "common.h"\n''')
            # fh.write('''#define TTA_MUTEX_UNLOCK -1\n''')
            # fh.write('''typedef volatile int tta_mutex;\n''')
            # fh.write('''typedef unsigned int tta_id;\n''')
            # fh.write('''tta_id id;\n''')
            # fh.write('''void mutex_set_tta_id(tta_id id);\n''')
            # fh.write('''#endif\n''')
            # fh.close()



    def createRuntimeDirs(self, rootdir=None):
        self.rootdir = rootdir

        if self.rootdir == None:
            self.rootdir = self.runtime.networkName
        try:
            os.mkdir(self.rootdir)
        except OSError:
            print("[Warning] Directory " + self.runtime.networkName + " cannot be created, already exists?")

        os.mkdir(self.rootdir + "/common")


        pt_file = open(self.rootdir + '/common/pt.h','w')
        pt_file.write(TTADF_Tools.ptFile())
        pt_file.close()

            #copy2(self.options.protothreads + '/pt.h', self.rootdir + '/common/')

        for core in self.runtime.cores:

            core.homedir = self.rootdir + "/" + core.coreId

            # Copy TTA architecture definition file
            try:
                os.mkdir(self.rootdir + "/" + core.coreId)
            except OSError:
                print("[Warning] Directory " + self.rootdir + "/" + core.coreId + " cannot be created, already exists?")
            try:
                os.mkdir(self.rootdir + "/" + core.coreId + "/src")
            except OSError:
                print("[Warning] Directory " + self.rootdir + "/" + core.coreId + "/src cannot be created, already exists?")

            if core.arch == 'TTA':

                core.writeOutArchDef(self.rootdir + '/' + core.coreId + '/')
                #copy2(str(core.deffile), self.rootdir + '/' + core.coreId + '/')


                pt_file = open(self.rootdir + '/' + core.coreId + '/src/pt.h', 'w')
                pt_file.write(TTADF_Tools.ptFile())
                pt_file.close()



    def createActorSourceFiles(self):

        ttadfparser = TTADFParser()

        for core in self.runtime.cores:
            for actor in core.actors:
                # Take ACTOR INIT, FIRE and FINISH functions

                print('[INFO] Processing sourcefiles of actor: ' + actor.actorId)

                preDirectives = ttadfparser.parseDirectives(actor)
                stateStruct = ttadfparser.parseStateStruct(actor)
                initFunction = ttadfparser.parseInitFunction(actor)
                fireFunction = ttadfparser.parseFireFunction(actor)
                finishFunction = ttadfparser.parseFinishFunction(actor)
                helperFunctions = ttadfparser.parseHelperFunctions(actor)

                if not (preDirectives):
                    print('[INFO] ' + actor.name + " Actor directives not found from " + actor.mainSourceFile + ".")
                else:
                    actor.setPreDirectives(preDirectives)

                if not (preDirectives):
                    print('[INFO] ' + actor.name + " Actor helperfunctions not found from " + actor.mainSourceFile + ".")
                else:
                    actor.setHelperFunctions(helperFunctions)

                if not (stateStruct):
                    print('[INFO] ' + actor.name + " Actor stateStruct function not found from " + actor.mainSourceFile + ".")
                else:
                    actor.setStateStruct(stateStruct)

                if not (initFunction):
                    print('[INFO] ' + actor.name + "_ACTOR_INIT - Actor initialising function not found from " + actor.mainSourceFile + ".")
                else:
                    actor.setInit(initFunction)
                if not (fireFunction):
                    print('[INFO] ' +actor.name + "_ACTOR_FIRE - Actor firing function not found from " + actor.mainSourceFile + ".")
                else:
                    actor.setFire(fireFunction)

                if not (finishFunction):
                    print('[INFO] ' +actor.name + "_ACTOR_FINISH - Actor finishing function not found from " + actor.mainSourceFile + ".")
                else:
                    actor.setFinish(finishFunction)


                actor.writeActorCfile(core.homedir + '/src/' + actor.actorId + '.c')
                actor.writeActorHeaderFile(core.homedir + '/src/' + actor.actorId + '.h',self.options)

                for sourcefile in actor.sourceFiles:
                    if core.arch == 'TTA':
                        copy2(sourcefile, core.homedir + '/src/')
                    if core.arch == 'X86':
                        copy2(sourcefile, self.rootdir + '/common/')

    def createCoreMainSourceFiles(self):

        for core in self.runtime.cores:
            if core.actors:
                if core.arch == 'X86':
                    core.writeCoreMainCSource(core.homedir +'/src/'+core.coreId+'_main.c',self.options)
                    core.writeCoreMainHeader(core.homedir +'/src/'+core.coreId+'_main.h',self.options)
                else:
                    core.writeCoreMainCSource(core.homedir + '/src/main.c',self.options)

    def codeMergeMemories(self):

        ttaCoreList = self.runtime.getAllTTACores()

        mergeMemoriesAS = ''
        for i in range(0, len(ttaCoreList)):
            mergeMemoriesAS += '    memorySystem = &(simFronts[' + str(i) + ']->memorySystem());\n'
            for j in range(i + 1, len(ttaCoreList)):
                mergeMemoriesAS += '    memorySystem->shareMemoriesWith(simFronts[' + str(j) + ']->memorySystem());\n'
        return mergeMemoriesAS

    def codeMergeSharedAS(self):

        ttaCoreList = self.runtime.getAllTTACores()

        cppCode = ''

        for mem in self.runtime.memories:
            memoryownerId = 0
            for i,core in enumerate(ttaCoreList):
                if ttaCoreList[i].coreId == mem.owner.coreId:
                    memoryownerId = i
                    break

            for connection in mem.connections:
                for i, core in enumerate(ttaCoreList):
                    if(connection.coreId != mem.owner.coreId and connection.coreId == core.coreId ):
                        cppCode += '    memorySystem = &(simFronts[' + str(i) + ']->memorySystem());\n'
                        cppCode += '    memorySystem->shareMemoryWith(simFronts[' + str(memoryownerId) + ']->memorySystem(),"'+mem.name+'");\n'

        return cppCode

    def codeCreateSharedMemories(self):

        cppCode = ''
        ttaCoreList = self.runtime.getAllTTACores()

        for mem in self.runtime.memories:
            cppCode +='    unsigned int *p_storage_'+mem.name+';\n'
            cppCode +='    p_storage_'+mem.name+' = new unsigned int ['+str( (mem.maxAddress-mem.minAddress)/4)+'];\n'

            for connection in mem.connections:
                for i, core in enumerate(ttaCoreList):
                    if(connection.coreId == core.coreId ):
                        cppCode += '    memorySystem = &(simFronts[' + str(i) + ']->memorySystem());\n'
                        cppCode += '    memorySystem->memory("'+mem.name+'")->setStoragePointer(p_storage_'+mem.name+');\n'
                        cppCode += '    cout << "pointer " << p_storage_'+mem.name+' << endl;\n'

        cppCode += '\n'
        return cppCode

    def codeSimulationGuide(self):
        # SUPPORT FOR DIFFERENT TTA CLOCK FREQUENCYS IN SIMULATION
        ttaCoreList = self.runtime.getAllTTACores()
        simulationGuide = ''
        if len(ttaCoreList):
            clockList = []
            clockListDiv= []
            for core in ttaCoreList:
                clockList.append(core.clkf)

            gcd = self.GCDM(*clockList)
            for clock in clockList:
                clockListDiv.append(clock/gcd)

            lcm = self.LCMM(*clockListDiv)
            #print(lcm)
            #print(clockListDiv)
            steppingFreqList = []
            for clock in clockListDiv:
                steppingFreqList.append(lcm/clock)
            #print(steppingFreqList)

            simulationGuide = 'int coreSimulationGuide[] = { '
            for item in steppingFreqList:
                simulationGuide += str(int(item)) +', '
            simulationGuide = simulationGuide[:len(simulationGuide)-2]
            simulationGuide += ' };\n'
        return simulationGuide

    def getInitSharedMemoriesCode(self):

        code = ''

        if len(self.runtime.getAllTTACores()):
            code += 'char * curMemPtr;\n'
            code += 'MemorySystem * curMemSys;\n'

        for mem in self.runtime.memories:
            if mem.onlyX86Connections():
                code += 'initSharedMem("'+mem.name+'.mif", sharedStorage_'+mem.name+');\n'
            else:
                code += 'curMemSys = &(simFronts['+ mem.owner.coreId.upper() +']->memorySystem());\n'
                code += 'curMemPtr = (char *)curMemSys->memory("'+mem.name+'")->getStoragePointer();\n'
                code += 'initSharedMem("'+mem.name+'.mif", curMemPtr);\n'

        return code;


    def createRuntimeSimulatorSource(self):


        ttaCoreList = self.runtime.getAllTTACores()
        numberOfTTACores = len(ttaCoreList)
        x86CoreList = self.runtime.getAllX86Cores()

        clockList = []
        for core in ttaCoreList:
            clockList.append(core.clkf)

        setMachCode = ''

        for i,core in enumerate(ttaCoreList):
            setMachCode += '''    machineFiles[''' + str(i) + '''] << "''' + core.coreId + '/' + core.coreId + '''.adf";\n'''

        setProgCode = ''

        for i, core in enumerate(ttaCoreList):
            setProgCode += '''    programFiles[''' + str(i) + '''] << "''' + core.coreId + '/' + core.coreId + '''.tpef";\n'''


        #FIFOS BETWEEN X86 HOST and TTA cores
        x86InterfaceFifos = []
        x86InterfaceMems = []
        x86InterfaceCores = []

        #FIFOS BETWEEN X86 CORES
        x86_x86InterfaceFifos = []
        x86_x86InterfaceMems = []
        x86_x86InterfaceCores = []


        for memory in self.runtime.memories:
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


        getHostInterfaceFifoAddresses = ''
        freeStorageArraysCode = ''
        if(x86InterfaceFifos):
            getHostInterfaceFifoAddresses += '    MemorySystem *tempMem;\n'
        for i, fifo in enumerate(x86InterfaceFifos):
            getHostInterfaceFifoAddresses += '    tempMem = &(simFronts[' +x86InterfaceCores[i].coreId.upper() +']->memorySystem());\n'
            getHostInterfaceFifoAddresses += '    ' + fifo.fifoId.upper()+'_BASEADDR = (char *) tempMem->memory("'+ x86InterfaceMems[i].name+'")->getStoragePointer();\n'
            getHostInterfaceFifoAddresses += '    cout << "pointer " << tempMem->memory("'+ x86InterfaceMems[i].name+'")->getStoragePointer() << endl;\n'
            #getHostInterfaceFifoAddresses += '    tempMem->memory("' + x86InterfaceMems[i].name+ '")->enableLittleEndian();\n'

        for i, mem in enumerate(x86_x86InterfaceMems):
            maxAddress = mem.fifos[len(mem.fifos)-1].endAddr
            getHostInterfaceFifoAddresses += '    char * sharedStorage_'+mem.name+';\n'
            getHostInterfaceFifoAddresses += '    sharedStorage_' + mem.name + ' = new char['+str(maxAddress+1)+'];\n'
            freeStorageArraysCode         += '    delete [] sharedStorage_' + mem.name +';\n'

            for j, fifo in enumerate(mem.fifos):
                getHostInterfaceFifoAddresses += '    ' + fifo.fifoId.upper() + '_BASEADDR = sharedStorage_' + mem.name +';\n'


        initSharedMemFunctions = '''
//https://stackoverflow.com/questions/236129/split-a-string-in-c
template<typename Out>
void split(const std::string &s, char delim, Out result) {
    std::stringstream ss;
    ss.str(s);
    std::string item;
    while (std::getline(ss, item, delim)) {
        *(result++) = item;
    }
}

std::vector<std::string> split(const std::string &s, char delim) {
    std::vector<std::string> elems;
    split(s, delim, std::back_inserter(elems));
    return elems;
}


//assumes hex address format and binary data format
int parseMIFline(std::string line, unsigned int *address, unsigned int *data){

    std::vector<std::string> x = split(line, ':');
    std::vector<std::string> y;

    if(x.size()>1){
        y = split(x[1],';');
    }

    if(y.size()>1){
        std::string::iterator end_pos = std::remove(x[0].begin(), x[0].end(), ' ');
        x[0].erase(end_pos, x[0].end());

        end_pos = std::remove(y[0].begin(), y[0].end(), ' ');
        y[0].erase(end_pos, y[0].end());

        std::stringstream ss;
        ss << std::hex <<x[0];
        ss >> *address;

        *data = (unsigned int) bitset<32>(y[0]).to_ulong();
        return 0;
    }

    return 1;
}


int initSharedMem(const char *initfname, char *baseaddress){

    std::ifstream fin;
    fin.open(initfname);

    string line;

    unsigned int address = 0;
    unsigned int data = 0;
    int nvalid;
    unsigned int * ptr;


    if(fin.is_open()){
        while(getline(fin,line)){
            nvalid = parseMIFline(line,&address,&data);
            if(!nvalid){
                ptr = (unsigned int *) (baseaddress+address);
                *ptr = data;
            }
        }
        fin.close();

        return 0;
    }
    else{
        cout << "Cannot open memory initialization file!\\n";
        return 1;
    }
}
\n\n'''

        content = ''

        content += TTADF_Tools.mitLicense()
        content += '#include <iostream>\n'
        if numberOfTTACores:
            content += '#include <DataflowSimulatorFrontend.hh>\n'
            content += '#include <Memory.hh>\n'
            content += '#include <MemorySystem.hh>\n'
            content += '#include <IdealSRAM_DF.hh>\n'
            content += '#include <TCEString.hh>\n'
            content += '#include <AddressSpace.hh>\n'
            content += '#include <Machine.hh>\n'
        content += '#include <string>\n'
        content += '#include <fstream>\n'
        content += '#include <sstream>\n'
        content += '#include <cstdio>\n'
        content += '#include <thread>\n'
        content += '#include <malloc.h>\n'
        content += '#include <sys/time.h>\n'
        content += '#include <vector>\n'
        content += '#include <iterator>\n'
        content += '#include <algorithm>\n'
        content += '#include <bitset>\n'
        content += '\n'

        content += 'typedef struct {\n'
        content += '    struct timeval tvs;\n'
        content += '    unsigned long long cal;\n'
        content += '    unsigned int execTime;\n'
        content += '    unsigned int totalTime;\n'
        content += '} prof_data;\n'

        content += 'void oulu_profile_init(prof_data* data){\n'
        content += '    data->totalTime = 0;\n'
        content += '    data->execTime = 0;\n'
        content += '}\n'

        content += 'void oulu_profile_start(prof_data* data)\n'
        content += '{\n'
        content += '    struct timezone tz;		// dummy time zone\n'
        content += '    struct timeval tve;		// end time\n'

        content += '    // find out how long two repeated gettimeofdays take\n'
        content += '    gettimeofday(&data->tvs, &tz);\n'
        content += '    gettimeofday(&tve, &tz);\n'
        content += '    data->cal = (tve.tv_sec * 1000000L + tve.tv_usec) - (data->tvs.tv_sec * 1000000L + data->tvs.tv_usec);\n'

        content += '    // start actual profiling\n'
        content += '    gettimeofday(&data->tvs, &tz);	\n'
        content += '}\n'

        content += 'void oulu_profile_end(prof_data* data)\n'
        content += '{\n'
        content += '    unsigned long long uss;	\n'
        content += '    unsigned long long use;\n'
        content += '    struct timeval tve;\n'
        content += '    struct timezone tz;\n'

        content += '    // stop profiling\n'
        content += '    gettimeofday(&tve,&tz);\n'

        content += '    // compute start and end times in microseconds\n'
        content += '    uss = data->tvs.tv_sec * 1000000L + data->tvs.tv_usec;\n'
        content += '    use = tve.tv_sec * 1000000L + tve.tv_usec;\n'

        content += '    data->execTime = (unsigned int) (use - uss - data->cal);\n'
        content += '    data->totalTime += data->execTime;\n'
        content += '}\n'

        for i, core in enumerate(ttaCoreList) :
            content += '#define '+ core.name.upper() + ' ' + str(i) +'\n'

        for i, core in enumerate(ttaCoreList) :
            content += '#define '+ core.coreId.upper() + ' ' + str(i) +'\n'

        for fifo in x86InterfaceFifos:
            content += 'char * ' + fifo.fifoId.upper() + '_BASEADDR;\n'
        for fifo in x86_x86InterfaceFifos:
            content += 'char * ' + fifo.fifoId.upper() + '_BASEADDR;\n'

        content += 'volatile int KILLNETWORK = 0;\n'

        content += '\n'
        content += 'using namespace std;\n'
        content += '\n'
        content += '#define NBTTACORES ' + str(numberOfTTACores) + '\n\n'

        if len(x86CoreList):
            content += 'extern "C" {\n'
            for core in x86CoreList:
                content += '    #include "'+core.coreId+'/src/'+core.coreId+'_main.h"\n'
            content += '}\n'

        content += '\n'

        #content += 'void ttaSimulation_thr(DataflowSimulatorFrontend *simFront){\n'
        #content += '    cout << "thread started\\n" ;\n'
        #content += '    while(!simFront->isFinished()){\n'
        #content += '        simFront->step();\n'
        #content += '    }\n'
        #content += '}\n'
        #content += '\n'

        content += initSharedMemFunctions

        content += 'int main(int argc, char *argv[]){\n'
        content += '\n'
        if numberOfTTACores:
            content += '    DataflowSimulatorFrontend ** simFronts;\n'
            content += '    TCEString * machineFiles = new TCEString [NBTTACORES];\n'
            content += '    TCEString * programFiles = new TCEString [NBTTACORES];\n'
            content += setMachCode + setProgCode
            content += '    simFronts = new DataflowSimulatorFrontend*[NBTTACORES];\n'
            content += '    std::ofstream * outputs = new std::ofstream[NBTTACORES]; '
            content += '\n'
            content += '    const char* outputFiles[NBTTACORES];\n'
            content += '\n'
            content += '    stringstream oFilename;\n'
            content += '\n'
            content += '    int i;\n'
            content += '    for(i=0; i<NBTTACORES; i++){\n'
            content += '        oFilename.str("");\n'
            content += '        oFilename << "core_" << i << ".txt";\n'
            content += '        const string& tmp =oFilename.str();\n'
            content += '        outputFiles[i] = tmp.c_str();\n'
            content += '        outputs[i].open(outputFiles[i], std::ofstream::out | std::ofstream::app);\n'
            content += '        simFronts[i] = new DataflowSimulatorFrontend(machineFiles[i],false);\n'
            content += '\n'
            content += '    }\n'
            content += '\n'
            content += '    /*PRINT SOME DATA OF MEMORIES AND SET SHARED MEMORIES*/\n'
            content += '    MemorySystem * memorySystem;\n'
            content += '    unsigned int numberOfMemories;\n'
            content += '    for(i=0; i<NBTTACORES; i++){\n'
            content += '        memorySystem = &(simFronts[i]->memorySystem());\n'
            content += '        numberOfMemories = memorySystem->memoryCount();\n'
            content += '        #ifdef TTADF_DEBUG\n'
            content += '        cout << "Memories in core " << i << ": " << numberOfMemories << endl;\n'
            content += '        #endif\n'
            content += '\n'
            content += '        unsigned int j;\n'
            content += '        const TTAMachine::AddressSpace * addressSpace;\n'
            content += '        string addressSpaceName;\n'
            content += '        for(j = 0; j<numberOfMemories; j++){\n'
            content += '            addressSpace = &(memorySystem->addressSpace(j));\n'
            content += '            addressSpaceName = addressSpace->name();\n'
            content += '            set<unsigned> numericalIds = addressSpace->numericalIds();\n'
            content += '            #ifdef TTADF_DEBUG\n'
            content += '            cout << "\tAddressSpace " << *numericalIds.begin() << " name : " << addressSpaceName ;\n'
            content += '\n'
            content += '            cout << ", shared: " << addressSpace->isShared() << endl;\n'
            content += '            #endif\n'
            content += '        }\n'
            content += '\n'
            content += '    }\n'

            content += '    /*MERGE SHARED ADDRESS SPACES*/\n'

            content += self.codeMergeSharedAS()

            content += '\n'
            content += '    for(i=0; i<NBTTACORES; i++){\n'
            content += '        cout << "Loading program " << programFiles[i] << "\\n";'
            content += '        simFronts[i]->loadProgram(programFiles[i]);\n'
            content += '    }\n'
            content += '\n'
            content += '    for(i=0; i<NBTTACORES; i++){\n'
            content += '        if(!simFronts[i]->isInitialized()){\n'
            content += '            cout << "core " << i << " not initialized" << endl;\n'
            content += '        }\n'
            content += '       if(simFronts[i]->isStopped()){\n'
            content += '            cout << "core " << i << " is stopped" << endl;\n'
            content += '        }\n'
            content += '    }\n'
            content += '\n'

        #content += self.codeCreateSharedMemories()

        content += getHostInterfaceFifoAddresses
        content += '\n'

        content += addTab('/*INITIALIZE SHARED MEMORIES*/', 1 )
        content += '\n'
        content += addTab(self.getInitSharedMemoriesCode(), 1)
        content += '\n'

        content += '    prof_data profiling;\n'
        content += '    oulu_profile_init(&profiling);\n'
        content += '    oulu_profile_start(&profiling);\n'

        for x86core in x86CoreList:
            content += '    std::thread '+ x86core.coreId+'_thread('+x86core.coreId +'_main);\n'

        #for index, ttaCore in enumerate (ttaCoreList):
        #    content += '    std::thread ' + ttaCore.coreId + '_thread(ttaSimulation_thr,simFronts['+str(index)+']);\n'

        if numberOfTTACores:
            content += '    /*RUN CORES STEP BY STEP*/\n'
            content += '    '+ self.codeSimulationGuide() +'\n'

            content += '    int stopflag = 1;\n'
            content += '    int loopcounters[NBTTACORES] = {0};\n'

            content += '    while(stopflag && !KILLNETWORK){\n'
            content += '\n'
            content += '        stopflag = 0;\n'
            content += '        for(i=0; i<NBTTACORES; i++){\n'
            content += '            if(!simFronts[i]->isFinished()){\n'
            content += '                if(loopcounters[i] == 0){\n'
            content += '                    simFronts[i]->step();\n'
            content += '                    simFronts[i]->step();\n'
            content += '                    simFronts[i]->step();\n'
            content += '                    simFronts[i]->step();\n'
            content += '                    simFronts[i]->step();\n'
            content += '                    simFronts[i]->step();\n'
            content += '                }\n'
            content += '                stopflag = 1;\n'
            content += '                loopcounters[i] = (loopcounters[i]+1)%coreSimulationGuide[i];\n'
            content += '            }\n'
            content += '        }\n'
            content += '\n'
            content += '    }\n'
            content += '\n'


        for x86core in x86CoreList:
            content += '    '+x86core.coreId+'_thread.join();\n'
        #for ttaCore in ttaCoreList:
        #    content += '    '+ttaCore.coreId+'_thread.join();\n'

        content += '    oulu_profile_end(&profiling);\n'

        content += '    double elapsed_secs = double(profiling.totalTime)/1000000;\n'
        if numberOfTTACores:
            content += '    unsigned int max = 0;\n'
            content += '    for(i=0; i<NBTTACORES; i++){\n'
            content += '        cout << "Cyclecount core " << i << ": " << simFronts[i]->cycleCount() << endl;\n'
            content += '        if (simFronts[i]->cycleCount() > max) max = simFronts[i]->cycleCount();\n'
            content += '        outputs[i].close();'
            content += '    }\n'
            content += '    cout << "Real execution time is " << ((double) max) / ((double) '+ str(max(clockList)*1000000) + ')<< " seconds" << endl;\n'
        content += '    cout << "Simulation time is " << elapsed_secs << " s" << endl;\n'
        content += '\n'
        content += freeStorageArraysCode

        if numberOfTTACores:
            content += '    delete [] machineFiles;\n'
            content += '    delete [] programFiles;\n'
            content += '    delete [] simFronts;\n'
            content += '    delete [] outputs;'
        content += '\n'
        content += '}\n'

        with open(self.rootdir + '/multicoreSimulation.cpp', 'w') as content_sourcefile:
            content_sourcefile.write(content)

    def createSharedMemoryMif(self):

        for memory in self.runtime.getAllMemories():
            memory.createMifFile(self.rootdir)

    def createSharedMemoryMTI(self):
        for memory in self.runtime.getAllMemories():
            memory.createMTIFile(self.getHDLDir())

    def createTpefs(self):

        for index, core in enumerate(self.runtime.getAllTTACores()):

            sourcefiles = ''
            sourcefiles += core.homedir + '/src/main.c '
            sourcefiles += core.homedir + '/src/common.c '


            for actor in core.actors:
                sourcefiles += core.homedir + '/src/' + actor.actorId + '.c '

                for source in actor.sourceFiles:
                    filename = source.split('/')[-1]
                    if filename.split('.')[-1] == 'c':
                        if core.homedir + '/src/' + filename not in sourcefiles:
                            sourcefiles += core.homedir + '/src/' + filename + ' '

            if core.actors:
                print('Compiling TTA "'+ core.coreId+'" program code. (' + str(index+1) + '/' + str(len(self.runtime.getAllTTACores()))+')')
                #os.system('tcecc -O1 --unroll-threshold=1000 -a ' + core.homedir + '/'+ core.coreId + '.adf ' + sourcefiles + ' -o ' + core.homedir + '/' +core.coreId+'.tpef')

                cmd = 'tcecc ' + core.getCompilerFlags() + ' -a ' + core.homedir + '/'+ core.coreId + '.adf ' + sourcefiles + ' -o ' + core.homedir + '/' +core.coreId+'.tpef'
                print(cmd)
                os.system(cmd)

                curDir = os.getcwd()

                os.chdir(os.getcwd()+'/'+core.homedir + '/')
                cmd = 'generatebits  -d -o "ascii" -w 4 -p ' +core.coreId+'.tpef '+ core.coreId + '.adf '
                print(cmd)
                #os.system(cmd)
                os.chdir(curDir)

                print('')
                print('INFO '+core.coreId+':')
                print('-------------------------------------------------------------------------------')
                os.system('createbem -o '+ core.homedir + '/'+ core.coreId + '.bem ' + core.homedir + '/'+ core.coreId + '.adf ')

                #os.system('viewbem '+ core.homedir + '/'+ core.coreId + '.bem  | grep -E "Total instruction.*|Move Slot:.*|Width:.*|src field:.*" | sed "s/^Move Slot:/\\n&/g"')
                instructionW = check_output('viewbem ' + core.homedir + '/' + core.coreId + '.bem  | grep -E "Total instruction.*"', shell=True)
                instructionW = int(instructionW.split()[-1])
                core.getInstructionMem().setWidth(instructionW)

                insMemLen = check_output('dumptpef -m ' + core.homedir + '/' +core.coreId+'.tpef  | grep -E "CODE: .*"', shell=True)
                insMemLen = int(insMemLen.split()[2])

                #print core.getInstructionMem().getLen()
                #core.getInstructionMem().setLen(insMemLen)

                dataMemLen = check_output('dumptpef -m ' + core.homedir + '/' + core.coreId + '.tpef  | grep -E "DATA: .*"', shell=True)
                dataMemLen = int(dataMemLen.split()[2])

                print('    Instruction Width: ' + str(instructionW) + ' bits')
                print('    Instruction Memory length: ' + str(insMemLen) + ' MAU')
                print('    Instruction Memory size: ' + str(insMemLen*instructionW/8/1024) + 'KB')
                print('    Local DATA Memory size ' + str(dataMemLen) + ' MAU')
                print('-------------------------------------------------------------------------------')
                print('')

            else:
                print('[INFO] Core "'+core.coreId+'" has no actors!')

            #print('INSTRUCTION MEMORY INFO '+core.coreId+':')
            #print('-------------')
            #os.system('dumptpef -m ' + core.homedir + '/' +core.coreId+'.tpef')

            print('')
            print('')


    def createHDLfiles(self):

        listOfCreatedProcessors = []

        ##curDir = os.getcwd()

        hdlDir = self.rootdir+'/hdl'
        hdlSharedDir = hdlDir+'/shared'

        print('[INFO] Creating hardware description files:')

        error = os.system('mkdir '+hdlDir)
        error = os.system('mkdir '+hdlSharedDir)

        for index, core in enumerate(self.runtime.getAllTTACores()):

            print('\tTTA "'+ core.coreId+'" (' + str(index+1) + '/' + str(len(self.runtime.getAllTTACores()))+')')

            if not core.getHWDefFile():
                print('[WARNING] NO IDF defined cannot create hdl files\n')
            else:

                #os.system('tcecc -O1 --unroll-threshold=1000 -a ' + core.homedir + '/'+ core.coreId + '.adf ' + sourcefiles + ' -o ' + core.homedir + '/' +core.coreId+'.tpef')

                coreOutputDir = hdlDir+'/'+core.getCoreId()
                core.setHdlFileDir(coreOutputDir)
                #error = os.system('mkdir '+coreOutputDir)

                if os.path.isfile(core.getHWDefFile()):
                    cmd = 'generateprocessor -i ' + core.getHWDefFile() + ' -e ' + core.getCoreId() \
                          + ' -s '+ hdlSharedDir + ' -c '+ str(core.getClkf()) +' -o ' + coreOutputDir +' '+ os.getcwd()+'/'+core.homedir + '/' +core.coreId+'.adf '
                    print(cmd)
                    os.system(cmd)


                    curdir = os.getcwd()
                    os.chdir(self.getHDLDir()+'/'+core.getCoreId())
                    print('\n[INFO] GENERATING INSTRUCTION MEMORY IMAGE - ' +core.getCoreId())
                    cmd = 'generatebits -f \'vhdl\' -e ' + core.getCoreId() + ' -p '+curdir+'/'+core.homedir + '/' +core.coreId+'.tpef ' + curdir+'/'+core.homedir + '/' +core.coreId+'.adf '
                    print(cmd)
                    os.system(cmd)
                    cmd = 'generatebits -f \'ascii\' -e ' + core.getCoreId() + ' -p '+curdir+'/'+core.homedir + '/' +core.coreId+'.tpef ' + curdir+'/'+core.homedir + '/' +core.coreId+'.adf '
                    print(cmd)
                    os.system(cmd)


                    print('\n[INFO] GENERATING DATA MEMORY IMAGE - '+core.getCoreId())
                    cmd = 'generatebits -d -w 4 -f \'ascii\' -e ' + core.getCoreId() + ' -p ' + curdir + '/' + core.homedir + '/' + core.coreId + '.tpef ' + curdir+'/'+core.homedir + '/' +core.coreId+'.adf '
                    print(cmd)
                    os.system(cmd)
                    cmd = 'rm *_imem_mau_pkg.vh'
                    os.system(cmd)

                    os.chdir(curdir)

                    core.setRTLEntity(VHDLEntityParser().parseFile(core.getHdlMainFile()))

                    print('[INFO] Creating Wrapper for "' + core.getCoreId()+'"')

                    f = open(core.getHdlFileDir() + '/wrapper_' + core.getCoreId() + '.vhdl', 'w')
                    f.write(vhdlTTACoreWrapper('wrapper_'+core.getCoreId(),core).write())
                    f.close()

                else:
                    print('[WARNING] IDF defined: '+ core.getHWDefFile() +', but file not found, cannot create hdl files!\n')

        print('[INFO] Creating Toplevel of TTA CPS for "' + hdlDir+'/'+self.runtime.getName()+'_CPS.vhd' + '"')
        f=open(hdlDir+'/'+self.runtime.getName()+'_CPS.vhd','w')
        f.write(vhdlTTASystemGenerator(self.runtime,self.rootdir).write())
        f.close()

        for mem in self.runtime.getCPSMems():
            rtlCode = mem.createVerilog('bitmask')
            f = open(hdlDir+'/mem_' + mem.getName() + '.v', 'w')
            f.write(rtlCode)
            f.close()

        if len(self.runtime.getAllArbiters()):
            os.system('cp '+self.installDir+'/vhdl/tta0_mem_arbiter.vhd '+hdlDir+'/')
        os.system('cp '+self.installDir+'/vhdl/globalLockOR.vhd ' + hdlDir + '/')


        self.createModelsimTclScript()


    def createModelsimTclScript(self):


        tcl = ''
        curDir = os.getcwd()
        absDir = curDir+'/'+ self.rootdir

        tcl +='project new ' + absDir + '/modelsim ' + 'cps_'+self.runtime.getName() +'\n'

        os.chdir(self.getHDLDir())
        projectfiles = check_output('find $PWD -type f', shell=True)


        libs = '../common/*.o '
        for core in self.runtime.getAllHostCores():
            libs += '../'+core.getCoreId()+'/src/*.o '

        for i,file in enumerate(projectfiles.split()):
            tcl += 'project addfile '+ file +'\n'


        tcl += 'project calculateorder \n'
        tcl += 'set fp [open compileorder.txt w]\n'
        tcl += 'puts $fp [project compileorder]\n'
        tcl += 'close $fp\n'

        tcl += 'project compileall\n'
        tcl += 'set fp [open tta_cps_'+self.runtime.getName()+'.h w]\n'
        tcl += 'puts $fp [scgenmod -map "std_logic=bool" -map "std_logic_vector=sc_bv" -createtemplate tta_cps_'+self.runtime.getName()+']\n'
        tcl += 'close $fp\n'

        tcl += 'project addfile ' +absDir+ '/testbench_'+self.runtime.getName()+'.cc\n'

        tcl += 'sccom -64 -work work -std=c++11 -I./ -I../common -I../../../../systemClib ../testbench_'+self.runtime.getName()+'.cc\n'
        tcl += 'sccom -64 -work work -link '+libs+'\n'
        tcl += 'vopt testbench_'+self.runtime.getName()+' -o opt_testbench_'+self.runtime.getName()+' +acc\n'
        tcl += 'vsim opt_testbench_'+self.runtime.getName()+' -t 100ps\n'

        for index, core in enumerate(self.runtime.getAllTTACores()):
            dir = self.getHDLDir() + '/' + core.getCoreId()
            tcl += 'mem load -infile ../../'+dir+'/'+core.getCoreId()+'.img -format bin /testbench_'+self.runtime.getName()+'/tta_cps/inst_'+core.getCoreId()+'/inst_instructions/mem\n'
            tcl += 'mem load -filldata 0 /testbench_' + self.runtime.getName() + '/tta_cps/inst_' + core.getCoreId() + '/inst_data/mem\n'
            tcl += 'mem load -infile ../../' + dir + '/' + core.getCoreId() + '_data.img -format bin /testbench_' + self.runtime.getName() + '/tta_cps/inst_' + core.getCoreId() + '/inst_data/mem\n'

        for mem in self.runtime.getCPSMems():
            dir = self.getHDLDir()
            tcl += 'mem load -filldata 0 /testbench_' + self.runtime.getName() + '/tta_cps/inst_' + mem.getName() + '/mem\n'
            tcl += 'mem load -infile ../../' + dir + '/' + mem.getName() + '.mti -format mti /testbench_' + self.runtime.getName() + '/tta_cps/inst_' + mem.getName() + '/mem\n'

        f = open('modelsim_cps_'+self.runtime.getName()+'.tcl','w')
        f.write(tcl)
        f.close()

        os.chdir(curDir)


    def createX86depencies(self):

        dir = os.getcwd()
        os.chdir(self.rootdir + '/common/')

        cmd = self.options.gccpath +' -c -O3 -I' + self.options.headerfiles + ' -fPIC -g *.c'
        print(cmd)
        os.system(cmd)
        os.chdir(dir)

        for index, core in enumerate(self.runtime.getAllX86Cores()):

            sourcefiles = []
            sourcefiles.append(core.homedir + '/src/'+core.coreId+'_main.c ')
            sourcefiles.append(core.homedir + '/src/common.c ')

            print('Creating object files of X86 actors')
            dir = os.getcwd()
            os.chdir(core.homedir+'/src/')
            print(os.getcwd())

            if(self.options.headerfiles):
                cmd = self.options.gccpath +' -fPIC -c -I'+self.options.headerfiles +' -I../../common/ ' + core.getCompilerFlags() + ' -g *.c'
                print(cmd)
                error = os.system(cmd)
            else:
                cmd = self.options.gccpath +' -fPIC -c -I../../common/ ' + core.getCompilerFlags() + ' -g  *.c'
                print(cmd)
                error = os.system(cmd)

            if(error):
                print('[ERROR] When compiling object files of X86 actors!')
                exit()

            os.chdir(dir)


    def createSystemCFiles(self):

        sc = systemCRuntime.systemCRuntimeGenerator(self.runtime, self.rootdir)
        sc.createSource('sc_simulation.c')

        sc = systemCRuntime.systemCTestbench(self.runtime, self.rootdir)
        sc.create('testbench_'+self.runtime.getName()+'.cc')

    def run(self):

        if not (self.options.networkFilename):
            print("Network file not defined, use -h for help!")
            return 1
        if not (self.options.mappingFilename):
            print("Mapping file not defined, use -h for help!")
            return 1
        if not (self.options.architectureFilename):
            print("Architecture file not defined, use -h for help!")
            return 1

        network = Network(self.options.networkFilename)
        arch = Architecture(self.options.architectureFilename)
        mapping = Mapping(self.options.mappingFilename)

        self.globalDefines = network.getDefines()

        self.runtime = RuntimeSystem(arch.architecture.get("name"), network.network.get("name"))

        arch.addCoresToRuntime(self.runtime)
        arch.addMemoriesToRuntime(self.runtime)


        mapping.addActorsToRuntimeCores(self.runtime, network)
        mapping.addFifosToRuntimeMemories(self.runtime, network)

        self.createRuntimeDirs()
        self.createActorSourceFiles()
        self.createFifoSourceFiles()
        self.createCoreMainSourceFiles()

        print('CREATING dotgraph ' + self.rootdir +'/')
        self.runtime.createDotGraph(self.rootdir + '/')

        #for core in self.runtime.cores:
        #    core.printInfo()

        self.createRuntimeSimulatorSource()

        self.createSharedMemoryMif()

        self.createTpefs()


        if self.runtime.getAllX86Cores():
            self.createX86depencies()

        if self.runtime.getAllTTACores():
            self.createSystemCFiles()
            self.createHDLfiles()

        self.createSharedMemoryMTI()

if __name__ == "__main__":
    parser = OptionParser()
    application = RuntimeCreator(parser)
    application.run()
