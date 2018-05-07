
from functools import reduce

from lxml import etree, objectify
from optparse import OptionParser
from subprocess import call, check_output
from shutil import copy2
import os
import re
import TTADF_Tools

class RuntimeActor:
    def __init__(self, actorId, name="unnamed_actor"):
        self.actorId = actorId
        self.name = name
        self.initF = ""
        self.fireF = ""
        self.finishF = ""
        self.stateStruct = ""
        self.preDirectives = ""
        self.helperFunctions = ""
        self.sourceFiles = []
        self.mainSourceFile = ''
        self.inputs = {}
        self.outputs = {}
        self.generics = {}
        self.canStopNetwork = False
        self.owner = None
        self.network = None


    def setNetwork(self,network):
        self.network = network

    def getNetwork(self):
        return self.network

    def setInit(self, code):
        self.initF = code

    def setFire(self, code):
        self.fireF = code

    def setFinish(self, code):
        self.finishF = code

    def setStateStruct(self, code):
        self.stateStruct = code

    def setPreDirectives(self, code):
        self.preDirectives = code

    def setMainSourceFile(self, mainSourceFile):
        self.mainSourceFile = mainSourceFile

    def setHelperFunctions(self, helperFuntions):
        self.helperFunctions = helperFuntions

    def getHelperFunctions(self):
        return self.helperFunctions

    def addSourcefile(self, sourceFile):
        self.sourceFiles.append(sourceFile)

    def addInputConnection(self, fifo, port):
        self.inputs[port] = fifo

    def addOutputConnection(self, fifo, port):
        self.outputs[port] = fifo

    def addGeneric(self,label,value):
        self.generics[label] = value

    def replaceWithActorGenerics(self,string):
        for label,value in self.generics.items():
            string = string.replace(str(label),str(value))
        return string

    def connectOutputFifo(self,fifo,port):
        if port in self.outputs:
            self.outputs[port] = fifo
        else:
            print('[Error] when connecting output FIFO: ' + fifo.fifoId + ' to the PORT: ' + port + ' not found in ACTOR ' \
                  + self.name + ': ' + self.actorId)

    def connectInputFifo(self,fifo,port):
        if port in self.inputs:
            self.inputs[port] = fifo
        else:
            print('[Error] when connecting input FIFO: ' + fifo.fifoId + ' to the PORT: ' + port + ' not found in ACTOR ' \
                  + self.name + ': ' + self.actorId)

    def writeActorCfile(self, filename):
        actorfile = open(filename, "w")

        core = self.owner

        if core.arch == 'TTA':
            actorfile.write('#define __ARCH_TTA__\n')
        if core.arch == 'X86':
            actorfile.write('#define __ARCH_X86__\n')

        actorfile.write('''#include "'''+self.actorId+'''.h"\n\n''')

        for localmem in core.localMems:
            for fifo in localmem.fifos:
                actorfile.write('''extern fifoType ''' + fifo.fifoId + ''';\n''')

        actorfile.write('''\n''')

        for localmem in core.localMems:
            for fifo in localmem.fifos:
                actorfile.write('''extern unsigned char ''' + fifo.fifoId + '''_storage[''' + str(fifo.capacity * fifo.tokenSizeInBytes) + '''];\n''')

        if core.arch == 'X86':
            for extmem in core.externalMems:
                for fifo in extmem.fifos:
                    actorfile.write('extern char * ' + fifo.fifoId.upper()+ '_BASEADDR;\n')

        actorfile.write('\n')
        actorfile.write(self.initF + '\n\n')
        actorfile.write(self.fireF + '\n\n')
        actorfile.write(self.finishF + '\n\n')

        if self.getHelperFunctions():
            actorfile.write(self.getHelperFunctions() + '\n')

        actorfile.close()

    def writeActorHeaderFile(self, filename,options):
        actorfile = open(filename, "w")
        actorfile.write('#ifndef ACTOR_' + self.actorId.upper() + '_H_\n')
        actorfile.write('#define ACTOR_' + self.actorId.upper() + '_H_\n')

        if self.owner.arch == 'TTA':
            actorfile.write('#define __ARCH_TTA__\n')
        if self.owner.arch == 'X86':
            actorfile.write('#define __ARCH_X86__\n')
        actorfile.write('#include <stdint.h>\n')
        actorfile.write('#include "common.h"\n')
        actorfile.write('#include "fifo.h"\n')
        actorfile.write('#include "pt.h"\n')

        actorfile.write('/*USER DEFINED GENERICS*/\n')
        for label, value in self.generics.items():
            actorfile.write('#undef '+label+ '\n')
            actorfile.write('#define '+label+ ' ' + str(value)+'\n')
        actorfile.write('\n')

        actorfile.write('#undef ' + self.name + '_STATE ' + '\n')
        actorfile.write('#define '+self.name+'_STATE '+self.actorId+'_STATE\n')
        actorfile.write('typedef struct ' + self.actorId + '_state_t ' + self.actorId + '_STATE;\n')

        for portname in self.inputs:
            for i, varName in enumerate(self.inputs[portname].variableNames):
                if(self.inputs[portname].variableOwner[i] == self):
                    actorfile.write('#undef TTADF_GET_AS_' + varName + '_ \n')
                    actorfile.write('#define TTADF_GET_AS_'+varName+'_ ' )
                    actorfile.write(self.inputs[portname].codeActionFifoGetAS(self,'') +'\n')
                    actorfile.write('#undef TTADF_GET_ASID_' + varName + '_ \n')
                    actorfile.write('#define TTADF_GET_ASID_' + varName + '_ ')
                    if self.owner.arch == 'TTA':
                        actorfile.write('"'+self.inputs[portname].codeActionFifoGetASNAME(self) + '"')
                    actorfile.write('\n')
        for portname in self.outputs:
            for i, varName in enumerate(self.outputs[portname].variableNames):
                if (self.outputs[portname].variableOwner[i] == self):
                    actorfile.write('#undef TTADF_GET_AS_' + varName + '_ \n')
                    actorfile.write('#define TTADF_GET_AS_'+varName+'_ ' )
                    actorfile.write(self.outputs[portname].codeActionFifoGetAS(self,'') +'\n')
                    actorfile.write('#undef TTADF_GET_ASID_' + varName + '_ \n')
                    actorfile.write('#define TTADF_GET_ASID_' + varName + '_ ')
                    if self.owner.arch == 'TTA':
                        actorfile.write('"'+self.outputs[portname].codeActionFifoGetASNAME(self) + '"')
                    actorfile.write('\n')

        actorfile.write(self.preDirectives + '\n\n')
        actorfile.write(self.stateStruct + '\n')
        actorfile.write(self.initF.split('{')[0] + ';\n')
        actorfile.write(self.fireF.split('{')[0] + ';\n')
        actorfile.write(self.finishF.split('{')[0] + ';\n')

        for port, outputFifo in self.outputs.items():
            actorfile.write('PT_THREAD(' + outputFifo.fifoId + '_INIT(struct pt *pt, ' + self.actorId + '_STATE *context));\n')
        for port, inputFifo in self.inputs.items():
            actorfile.write('PT_THREAD(' + inputFifo.fifoId + '_CHECK(struct pt *pt, ' + self.actorId + '_STATE *context));\n')


        actorfile.write('#endif\n')

        actorfile.close()