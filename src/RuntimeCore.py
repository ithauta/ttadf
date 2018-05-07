
from functools import reduce

from lxml import etree, objectify
from optparse import OptionParser
from subprocess import call, check_output
from shutil import copy2
import os
import re
import TTADF_Tools

class RuntimeCore:
    def __init__(self, coreId, name, clkf):
        self.coreId = coreId
        self.numericId = 0
        self.name = name
        self.deffile = None
        self.defObj = None
        self.hwdeffile = None
        self.hdlFileDir = None
        self.externalMems = []
        self.localMems = []
        self.loadStoreUnit = [] #tuple container External memoryname/address-space name and LSU name in adf file
        self.nb_loadStoreUnits = 2; #0 reserved for data, 1 reserved for instructions
        self.actors = []
        self.homedir = ''
        self.clkf = clkf
        self.arch = None
        self.compilerFlags = ''
        self.rtlEntity = None
        self.wrapperRtlEntity = None
        self.instructionWidth = 0
        self.instructionMemLen = 0


    def getExternalMemories(self):
        return self.externalMems

    def setWrapperRtlEntity(self,entity):
        self.wrapperRtlEntity = entity

    def getWrapperRtlEntity(self):
        return self.wrapperRtlEntity

    def getInstructionMem(self):
        return self.localMems[1]

    def getDefaultDataMem(self):
        return self.localMems[0]

    def getArbiters(self):
        arbiters = []

        for mem in self.getExternalMemories():
            arbiter = mem.getArbiter()
            if arbiter:
                arbiters.append(arbiter)

        return arbiters

    def setInstructionWidth(self,w):
        self.instructionWidth = w

    def getInstructionWidth(self):
        return self.instructionWidth

    def getLocalMems(self):
        return self.localMems

    def getLoadStoreUnits(self):
        return self.loadStoreUnit

    def setRTLEntity(self,entity):
        self.rtlEntity = entity

    def getRTLEntity(self):
        return self.rtlEntity

    def setClkf(self,f):
        self.clkf = f

    def getClkf(self):
        return self.clkf

    def setHdlFileDir(self,dir):
        self.hdlFileDir = dir

    def getHdlMainFile(self):
        return self.getHdlFileDir()+'/vhdl/'+self.getCoreId()+'.vhdl'

    def getHdlFileDir(self):
        return self.hdlFileDir

    def getAdfFilePath(self):
        return self.deffile

    def getCoreId(self):
        return self.coreId

    def setHWDefFile(self, defFilePath):
        self.hwdeffile = defFilePath

    def getHWDefFile(self):
        return self.hwdeffile

    def setCompilerFlags(self,flags):
        self.compilerFlags = flags

    def getCompilerFlags(self):
        return self.compilerFlags

    def getArch(self):
        return self.arch

    def isTTA(self):
        if self.arch == 'TTA':
            return True
        else:
            return False

    def addExternalLoadStoreUnit(self, memory, lsuname):
        self.loadStoreUnit.append((memory,lsuname,self.nb_loadStoreUnits))
        self.nb_loadStoreUnits += 1

        return  self.nb_loadStoreUnits-1

    def addActor(self, actor):
        self.actors.append(actor)

    def addExternalMem(self, mem):
        # TODO Check mem that mem is valid
        self.externalMems.append(mem)

    def addLocalMem(self, mem):
        # TODO Check mem that mem is valid
        self.localMems.append(mem)

    def getMemory(self, name):
        for memory in self.externalMems:
            if memory.name == name:
                return memory

        for memory in self.localMems:
            if memory.name == name:
                return memory

        return None


    def getLSUNameByMemName(self,memname):
        for lsu in self.loadStoreUnit:
            if memname == lsu[0]:
                return lsu[1]

        return None


    def getActorById(self, actorId):
        for actor in self.actors:
            if actor.actorId == actorId:
                return actor
        return None

    def getFifoById(self, fifoId):
        for memory in self.externalMems:
            for fifo in memory.fifos:
                if fifo.fifoId == fifoId:
                    return fifo

        for memory in self.localMems:
            for fifo in memory.fifos:
                if fifo.fifoId == fifoId:
                    return fifo

        return None

    def getFifoByPortVar(self,varName,actor):
        for memory in self.externalMems:
            for fifo in memory.fifos:
                for index, variable in enumerate(fifo.variableNames):
                    if variable == varName and fifo.variableOwner[index] == actor:
                        return fifo
        for memory in self.localMems:
            for fifo in memory.fifos:
                for index, variable in enumerate(fifo.variableNames):
                    if variable == varName and fifo.variableOwner[index] == actor:
                        return fifo
        return None

    def printInfo(self):
        print("Core Info " + self.coreId)
        print("\tcoreId: " + self.coreId)
        print("\tname: " + self.name)
        print("\tarch: " + self.arch)
        print("\tclkf: " + str(self.clkf) + ' MHz')
        if self.deffile:
            print("\tdeffile: " + self.deffile)
        print("\tLocal Memories : ")

        if len(self.localMems):
            for mem in self.localMems:
                if self.arch == 'TTA':
                    print("\t\tMEM: " + mem.name + ", as: " + str(mem.getAddressSpaceForCore(self)))

                if len(mem.fifos):
                    for fifo in mem.fifos:
                        if fifo.target.owner.coreId == self.coreId or fifo.source.owner.coreId == self.coreId:
                            fifo.prinfInfo()
                else:
                    print("\t\t\t No fifos")
        else:
            print("\t\t No local memories")

        print("\tExternal Memories : ")
        if len(self.externalMems):
            for mem in self.externalMems:
                if self.arch == 'TTA':
                    print("\t\tMEM: " + mem.name + ", as: " + str(mem.getAddressSpaceForCore(self)))
                else:
                    print("\t\tMEM: " + mem.name )

                if len(mem.fifos):
                    for fifo in mem.fifos:
                        if fifo.target.owner.coreId == self.coreId or fifo.source.owner.coreId == self.coreId:
                            fifo.prinfInfo()

                else:
                    print("\t\t\t No fifos")
        else:
            print("\t\t No external memories")

        print("\tActors: ")
        if len(self.actors):
            for actor in self.actors:
                print("\t\t" + actor.name + " (" + actor.actorId + ")")
                print("\t\t\tmainsourcefile: " + actor.mainSourceFile)
                for sourcefile in actor.sourceFiles:
                    print("\t\t\tsourcefile: " + sourcefile)

                print("\t\t\tInput connections:")
                if actor.inputs:
                    for port,inputconnection in actor.inputs.items():
                        print("\t\t\t\t" + inputconnection.fifoId)
                else:
                    print("\t\t\t\tNo connections")
                print("\t\t\tOutput connections:")
                if actor.outputs:
                    for port,outputconnection in actor.outputs.items():
                        print("\t\t\t\t" + outputconnection.fifoId)
                else:
                    print("\t\t\t\tNo connections")

        else:
            print("\t\tNo actors")


class RuntimeCoreTTA(RuntimeCore):
    def __init__(self,coreId, name, clkf, deffile):
        RuntimeCore.__init__(self,coreId, name, clkf)
        self.arch = 'TTA'
        self.archDef = None
        self.deffile = deffile
        self.hwFifoExtensionPopulation = False
        self.hwFifoExtensionWREnd = False

        try:
            with open(self.deffile) as f:
                self.archDef = f.read()
        except IOError:
            print('[ERROR] Core "'+ self.name +'" TTA Architecture defination file ' + self.deffile +' not found!')
            exit()
        self.archDef = objectify.fromstring(self.archDef.encode('utf8'))


    def setHwFifoExtensionPopulation(self):
        print('[INFO] '+ self.coreId +': FIFO opset extension found: ttadf_population')
        self.hwFifoExtensionPopulation = True

    def setHwFifoExtensionWREnd(self):
        print('[INFO] '+ self.coreId +': FIFO opset extension found: ttadf_wr_end')
        self.hwFifoExtensionWREnd = True

    def hasHwFifoExtensionPopulation(self):
        return self.hwFifoExtensionPopulation

    def hasHwFifoExtensionWREnd(self):
        return self.hwFifoExtensionWREnd

    def checkHwFifoExtensionSupport(self):
        for functionUnit in self.archDef['function-unit']:
            for operation in functionUnit['operation']:
                if operation.name == 'ttadf_population':
                    self.setHwFifoExtensionPopulation()
                if operation.name == 'ttadf_rw_end':
                    self.setHwFifoExtensionWREnd()


    def writeOutArchDef(self,filepath):
        f = open(filepath+self.coreId+'.adf', 'wb')
        f.write(etree.tostring(self.archDef, pretty_print=True))
        f.close()

    def writeCoreMainCSource(self, filename,options):
        mainsource = open(filename, "w")

        for actor in self.actors:
            mainsource.write('#include "' + actor.actorId + '.h"\n')
        mainsource.write('#include "pt.h"\n''')

        mainsource.write('#include <tceops.h>\n')

        mainsource.write('\nstatic struct pt pt_handler;\n')
        for actor in self.actors:
            mainsource.write('static struct pt pt_' + actor.actorId + ';\n')
            '''
            for key, fifo in actor.inputs.items():
                mainsource.write('static struct pt pt_input_' + fifo.fifoId + ';\n')
            for key, fifo in actor.outputs.items():
                mainsource.write('static struct pt pt_output_' + fifo.fifoId + ';\n')
            '''

        mainsource.write('\n')

        for localmem in self.localMems:
            for fifo in localmem.fifos:
                mainsource.write('unsigned char '+fifo.fifoId+'_storage['+str(fifo.capacity*fifo.tokenSizeInBytes)+'];\n')

            mainsource.write('\n')
        for localmem in self.localMems:
            for fifo in localmem.fifos:
                mainsource.write('fifoType '+fifo.fifoId+' = ' + fifo.codeActionFifoStaticInit('&'+fifo.fifoId+'_storage', self) +';\n')
                       #mainsource.write('fifoType ' + fifo.fifoId+';\n')

        mainsource.write('\n')




        mainsource.write('\n/*Declare state structures for actors*/\n')
        for actor in self.actors:
            core = self

            mainsource.write('static '+actor.actorId + '_STATE s_' + actor.actorId + ' = { .ttadf_actor_name = "' + actor.actorId + '", .ttadf_empty = 0, .ttadf_full = 0, .ttadf_stop = 0, .ttadf_nb_firings = 0, .ttadf_id =' + str(actor.owner.numericId) + ',\n')
            for key, fifo in actor.inputs.items():
                mem = fifo.owner
                fifoId = fifo.fifoId
                if mem.type == "local":
                    mainsource.write('\t.' + fifoId + ' = (p_fifo) &' + fifoId + ',\n')
                else:
                    addrs = mem.getAddressSpaceForCore(core)
                    mainsource.write('\t.' + fifoId + ' = (volatile p_fifo_as' + str(addrs) + ') ' + str(fifo.startAddr) + ',\n')

            for key, fifo in actor.outputs.items():
                mem = fifo.owner
                fifoId = fifo.fifoId
                if mem.type == "local":
                    mainsource.write('\t.' + fifoId + ' = (p_fifo) &' + fifoId + ',\n')
                else:
                    addrs = mem.getAddressSpaceForCore(core)
                    mainsource.write('\t.' + fifoId + ' = (volatile p_fifo_as' + str(addrs) + ') ' + str(fifo.startAddr) + ',\n')

            mainsource.write('};\n')

        mainsource.write('\n\nPT_THREAD(handler(struct pt *pt)){\n')



        mainsource.write('    PT_BEGIN(pt);\n')
        mainsource.write('    static int stop;\n')
        mainsource.write('    while(1){\n\n')
        mainsource.write('        stop = 1;\n')
        for actor in self.actors:
            mainsource.write('        if(!s_'+actor.actorId + '.ttadf_stop){\n')
            mainsource.write('            PT_SCHEDULE('+actor.actorId+'_FIRE(&pt_'+actor.actorId+',&s_'+actor.actorId+'));\n')
            mainsource.write('            stop = 0;\n')
            mainsource.write('        }\n')
        mainsource.write('        if(stop) break;\n')
        mainsource.write('    }\n\n')
        mainsource.write('    PT_END(pt);\n')
        mainsource.write('}\n')

        mainsource.write('\n\nPT_THREAD(handler_init_' + self.coreId + '(struct pt *pt)){\n')
        mainsource.write('    PT_BEGIN(pt);\n')
        for actor in self.actors:
            mainsource.write('    int ready_' + actor.actorId + ' = 1;\n')
        mainsource.write('    int exitLoop = 1;\n')
        mainsource.write('    while(exitLoop){\n')
        for actor in self.actors:
            mainsource.write('        if(ready_' + actor.actorId + '){\n')
            mainsource.write('            ready_' + actor.actorId + ' = PT_SCHEDULE(' + actor.actorId + '_INIT(&pt_' + actor.actorId + ',&s_' + actor.actorId + '));\n')
            mainsource.write('        }\n')

        mainsource.write('        exitLoop = ')
        for actor in self.actors:
            mainsource.write('ready_' + actor.actorId)
            if actor != self.actors[-1]:
                mainsource.write('|')
            else:
                mainsource.write(';\n')

        mainsource.write('    }\n')
        mainsource.write('    PT_END(pt);\n')
        mainsource.write('}\n')


        mainsource.write('\n\nint main(){\n\n')

        mainsource.write('//List all fifos so that tcecc make memory initialization :)\n')
        for extmem in self.externalMems:
            for fifo in extmem.fifos:
                pass
                #mainsource.write('    '+fifo.fifoId+';\n')
                #mainsource.write('    ' + fifo.fifoId + '_spacer;\n')
                #mainsource.write('    ' + fifo.fifoId + '_storage;\n')

        mainsource.write('    PT_INIT(&pt_handler);\n')
        for actor in self.actors:
            mainsource.write('    PT_INIT(&pt_' + actor.actorId + ');\n')

        mainsource.write('''\n    /*Init actors*/\n''')
        mainsource.write('    PT_SCHEDULE(handler_init_' + self.coreId + '(&pt_handler));\n')

        mainsource.write('    PT_INIT(&pt_handler);\n')
        '''
        for actor in self.actors:
            for key, fifo in actor.inputs.items():
                mainsource.write('    PT_INIT(&pt_input_' + fifo.fifoId + ');\n')
            for key, fifo in actor.outputs.items():
                mainsource.write('    PT_INIT(&pt_output_' + fifo.fifoId + ');\n')
        '''
        mainsource.write('\n    /*Init fifos*/\n')

        #mainsource.write('    PT_SCHEDULE(handler_init_fifos_' + self.coreId + '(&pt_handler));\n')


        mainsource.write('    PT_INIT(&pt_handler);\n')
        for actor in self.actors:
            mainsource.write('    PT_INIT(&pt_' + actor.actorId + ');\n')

        mainsource.write('\n    /*Fire actors*/\n')
        mainsource.write('    PT_SCHEDULE(handler(&pt_handler));\n')

        mainsource.write('\n    /*cleanup actors*/\n')
        for actor in self.actors:
            mainsource.write('    ' + actor.actorId + '_FINISH(&s_' + actor.actorId + ');\n')

        mainsource.write('\n    while(1);\n')
        mainsource.write('\n    return 0;\n}\n')


        mainsource.close()

class RuntimeCoreX86(RuntimeCore):
    def __init__(self,coreId, name, clkf, wordsize=64):
        RuntimeCore.__init__(self,coreId, name, clkf)
        self.arch = 'X86'
        self.wordsize = wordsize

    def getWordSize(self):
        return self.wordsize

    def writeCoreMainHeader(self, filename,options):
        mainsource = open(filename, "w")

        mainsource.write('#ifndef '+self.coreId.upper()+'_MAIN_\n')
        mainsource.write('#define '+self.coreId.upper()+'_MAIN_\n')

        mainsource.write('#include "pt.h"\n')
        mainsource.write('int '+self.coreId+'_main();\n')

        mainsource.write('#endif\n')


    def writeCoreMainCSource(self, filename,options):
        mainsource = open(filename, "w")

        mainsource.write('#include "'+self.coreId+'_main.h"\n')

        for actor in self.actors:
            mainsource.write('#include "' + actor.actorId + '.h"\n')

        mainsource.write('extern volatile int KILLNETWORK;\n')

        for extmem in self.externalMems:
            for fifo in extmem.fifos:
                mainsource.write('extern char * ' + fifo.fifoId.upper()+ '_BASEADDR;\n')

        mainsource.write('\nstatic struct pt pt_handler;\n')
        for actor in self.actors:
            mainsource.write('static struct pt pt_' + actor.actorId + ';\n')
            for key, fifo in actor.inputs.items():
                mainsource.write('static struct pt pt_input_' + fifo.fifoId + ';\n')
            for key, fifo in actor.outputs.items():
                mainsource.write('static struct pt pt_output_' + fifo.fifoId + ';\n')

        mainsource.write('\n')


        for localmem in self.localMems:
            for fifo in localmem.fifos:
                mainsource.write('unsigned char '+fifo.fifoId+'_storage['+str(fifo.capacity*fifo.tokenSizeInBytes)+'];\n')

            mainsource.write('\n')
        for localmem in self.localMems:
            for fifo in localmem.fifos:
                mainsource.write('fifoType '+fifo.fifoId+' = ' + fifo.codeActionFifoStaticInit('&'+fifo.fifoId+'_storage', self) +';\n')





        mainsource.write('''\n/*Declare state structures for actors*/\n''')
        for index, actor in enumerate(self.actors):
            mainsource.write(
                'static ' + actor.actorId + '_STATE s_' + actor.actorId + ' = { .ttadf_actor_name = "' + actor.actorId + '", .ttadf_empty = 0, .ttadf_full = 0, .ttadf_stop = 0, .ttadf_nb_firings = 0, .ttadf_id =' + str(
                    actor.owner.numericId) + ',\n')
            for key, fifo in actor.inputs.items():
                mem = fifo.owner
                fifoId = fifo.fifoId
                if mem.type == "local":
                    mainsource.write('\t.' + fifoId + ' = (p_fifo) &' + fifoId + ',\n')
                else:
                    mainsource.write(
                        '\t.' + fifoId + ' = 0,\n')

            for key, fifo in actor.outputs.items():
                mem = fifo.owner
                fifoId = fifo.fifoId
                if mem.type == "local":
                    mainsource.write('\t.' + fifoId + ' = (p_fifo) &' + fifoId + ',\n')
                else:
                    mainsource.write(
                        '\t.' + fifoId + ' = 0,\n')

            mainsource.write('};\n')


        mainsource.write('\n\nPT_THREAD(handler_'+self.coreId+'(struct pt *pt)){\n')
        mainsource.write('    PT_BEGIN(pt);\n')
        mainsource.write('    static int stop;\n')

        mainsource.write('    while(!KILLNETWORK){\n\n')
        for actor in self.actors:
            mainsource.write('        if(!s_' + actor.actorId + '.ttadf_stop){\n')
            mainsource.write('            PT_SCHEDULE(' + actor.actorId + '_FIRE(&pt_' + actor.actorId + ',&s_' + actor.actorId + '));\n')
            mainsource.write('        }\n')
            if actor.canStopNetwork:
                mainsource.write('        if(s_'+actor.actorId + '.ttadf_stop){\n')
                mainsource.write('            KILLNETWORK = 1;\n')
                mainsource.write('        }\n')

        mainsource.write('''    }\n\n''')
        mainsource.write('''    PT_END(pt);\n''')
        mainsource.write('''}\n''')

        mainsource.write('\n\nPT_THREAD(handler_init_' + self.coreId + '(struct pt *pt)){\n')
        mainsource.write('    PT_BEGIN(pt);\n')

        for index, actor in enumerate(self.actors):
            for key, fifo in actor.inputs.items():
                mem = fifo.owner
                fifoId = fifo.fifoId
                if mem.type == "local":
                    mainsource.write('')
                else:
                    mainsource.write('    s_'+actor.actorId + '.' + fifoId + ' = (volatile p_fifo) (' + fifo.fifoId.upper() + '_BASEADDR + ' + str(fifo.startAddr) + ');\n')
            for key, fifo in actor.outputs.items():
                mem = fifo.owner
                fifoId = fifo.fifoId
                if mem.type == "local":
                    mainsource.write('')
                else:
                    mainsource.write('    s_'+actor.actorId + '.' + fifoId + ' = (volatile p_fifo) (' + fifo.fifoId.upper() + '_BASEADDR + ' + str(fifo.startAddr) + ');\n')


        for actor in self.actors:
            mainsource.write('    int ready_' + actor.actorId + ' = 1;\n')
        mainsource.write('    int exitLoop = 1;\n')
        mainsource.write('    while(exitLoop){\n')
        for actor in self.actors:
            mainsource.write('        if(ready_' + actor.actorId + '){\n')
            mainsource.write(
                '            ready_' + actor.actorId + ' = PT_SCHEDULE(' + actor.actorId + '_INIT(&pt_' + actor.actorId + ',&s_' + actor.actorId + '));\n')
            mainsource.write('        }\n')

        mainsource.write('        exitLoop = ')
        for actor in self.actors:
            mainsource.write('ready_' + actor.actorId)
            if actor != self.actors[-1]:
                mainsource.write('|')
            else:
                mainsource.write(';\n')

        mainsource.write('    }\n')
        mainsource.write('    PT_END(pt);\n')
        mainsource.write('}\n')


        mainsource.write('\n\nint '+self.coreId+'_main(){\n')

        #mainsource.write('    printf("hello thread x86\\n"); \n')

        mainsource.write('    PT_INIT(&pt_handler);\n')
        for actor in self.actors:
            mainsource.write('    PT_INIT(&pt_' + actor.actorId + ');\n')
        mainsource.write('''\n    /*Init actors*/\n''')
        mainsource.write('    PT_SCHEDULE(handler_init_' + self.coreId + '(&pt_handler));\n')

        mainsource.write('    PT_INIT(&pt_handler);\n')

        for actor in self.actors:
            mainsource.write('    PT_INIT(&pt_' + actor.actorId + ');\n')
        mainsource.write('\n    /*Fire actors*/\n')
        mainsource.write('    PT_SCHEDULE(handler_'+self.coreId+'(&pt_handler));\n')

        mainsource.write('\n    /*cleanup actors*/\n')
        for actor in self.actors:
            mainsource.write('    ' + actor.actorId + '_FINISH(&s_' + actor.actorId + ');\n')

        mainsource.write('\n    return 0;\n}\n')


        mainsource.close()