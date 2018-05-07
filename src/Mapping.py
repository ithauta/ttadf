from lxml import etree, objectify
from optparse import OptionParser
from subprocess import call, check_output
from shutil import copy2
import os
import re
from TTADF_Tools import *
from RuntimeActor import RuntimeActor
from RuntimeFifo import RuntimeFifo
from RuntimeMemory import MemoryObject, Arbiter

class Mapping:
    def __init__(self, mappingFilename, defines = None):
        self.mappingFilename = mappingFilename

        with open(self.mappingFilename) as f:
            self.xml_mapping = f.read()

        self.checkXMLPragmas()
        self.mapping = objectify.fromstring(self.xml_mapping)
        self.defines = defines

    def replaceWithDefines(self,string):
        #print(string)
        for label,value in self.defines.items():
            string = string.replace(str(label),str(value))
        #print(string)
        return string

    def parsePragmaParams(self, codeblock, start, nb_inputs):

        inputParams = []

        noOpenBrackets = 0
        charNo = 0
        startCaptureFlag = False
        inputString = ''

        for char in codeblock[start:]:
            charNo += 1
            if char == '(':
                if startCaptureFlag == False:
                    startCaptureFlag = True
                else:
                    inputString += char
                noOpenBrackets += 1
            elif char == ')':
                noOpenBrackets -= 1
                if noOpenBrackets == 0:
                    inputParams.append(inputString)
                    break
                else:
                    inputString += char
            elif char == ',':
                if noOpenBrackets == 1:
                    inputParams.append(inputString)
                    inputString = ''
                else:
                    inputString += char
            elif startCaptureFlag == True:
                inputString += char

        if (nb_inputs != len(inputParams)):
            return None, None

        return inputParams, start + charNo

    def checkXMLPragmas(self):

        match = re.search('#PRAGMA\s*GENERATE',self.xml_mapping)
        while match:

            inputargs, end = self.parsePragmaParams(self.xml_mapping, match.end(), 3)

            iterator = inputargs[0]
            initVal = inputargs[1]
            toVal = inputargs[2]

            if not (inputargs):
                print('[ERROR] When parsing PRAGMA TTADF_GENERATE: could not find 3 input parameters!')
                exit()

            endMatch = re.search('#PRAGMA END GENERATE',self.xml_mapping[match.start():])

            if not endMatch:
                print("[ERROR] NOT FOUND PRAGMA END GENERATE")
                exit()


            if not strIsInt(initVal):
                initVal = self.replaceWithDefines(initVal)
                if not strIsInt(initVal):
                    print('[ERROR] PRAGMA TTADF_GENERATE invalid init value')
            if not strIsInt(toVal):
                toVal = self.replaceWithDefines(toVal)
                if not strIsInt(initVal):
                    print('[ERROR] PRAGMA TTADF_GENERATE invalid stop value')


            generateBlock = self.xml_mapping[end:endMatch.start()+match.start()]

            newContent = ''
            for i in range(int(initVal),int(toVal)):
                newContent += generateBlock.replace('$'+iterator+'$',str(i))


            preContent = self.xml_mapping[:match.start()]
            postContent = self.xml_mapping[endMatch.end()+match.start():]

            self.xml_mapping = preContent + newContent + postContent
            match = re.search('#PRAGMA\s*GENERATE', self.xml_mapping)

    def getAllCores(self):
        corelist = []
        for core in self.mapping.core:
            corelist.append(core)

        return corelist


    def addActorsToRuntimeCores(self, runtime, network):
        for xmlcore in self.mapping.core:
            coreId = xmlcore.get("id")
            core = runtime.getCoreById(coreId)
            if core:
                for actor in xmlcore.actor:
                    actorId = actor.get("id")
                    xmlActor = network.findActorById(actorId)
                    if not len(xmlActor):
                        print('[ERROR] Mapping file "'+self.mappingFilename+'" defines actor "'+actorId+'", but it is not in actor network!' )
                        exit()

                    actorObj = RuntimeActor(actorId)

                    actorObj.name = str(xmlActor.name)

                    for outputPort in xmlActor.iterchildren(tag="output"):
                        actorObj.addOutputConnection(None,outputPort.get("port"))

                    for inputPort in xmlActor.iterchildren(tag="input"):
                        actorObj.addInputConnection(None,inputPort.get("port"))

                    for mainSourceFile in xmlActor.iterchildren(tag="mainSourceFile"):
                        actorObj.setMainSourceFile(str(mainSourceFile))

                    for sourcefile in xmlActor.iterchildren(tag="sourceFile"):
                        actorObj.addSourcefile(str(sourcefile))

                    for generic in xmlActor.iterchildren(tag="generic"):
                        if str(generic).strip()[0] == '"' and str(generic).strip()[-1] == '"':
                            actorObj.addGeneric(generic.get("label"),str(generic))
                        else:
                            ns = {'__builtins__': None}
                            actorObj.addGeneric(generic.get("label"),eval(network.replaceWithDefines(str(generic)),ns))

                    try:
                        if xmlActor.stopNetwork:
                            actorObj.canStopNetwork = True
                            print('[INFO] '+ actorObj.actorId + ' can stop network execution.')
                    except:
                        pass

                    actorObj.owner = core
                    actorObj.setNetwork(network)
                    core.addActor(actorObj)

            else:
                print("[ERROR]" + coreId + " not found in runtime system!\n \tCheck architecture description file")
                exit()

    def addFifosToRuntimeMemories(self, runtime, network):

        for xmlfifo in network.network.fifo:
            fifoObj = RuntimeFifo(xmlfifo.get("id"))
            fifoObj.name = xmlfifo.name

            fifoObj.target = runtime.getActorById(xmlfifo.target)
            fifoObj.source = runtime.getActorById(xmlfifo.source)
            fifoObj.source_port_id = xmlfifo.source.get("port")
            fifoObj.target_port_id = xmlfifo.target.get("port")

            ns = {'__builtins__': None}
            fifoObj.tokenSizeInBytes = eval(network.replaceWithDefines(str(xmlfifo.tokenSizeInBytes)),ns)
            fifoObj.capacity = eval(network.replaceWithDefines(str(xmlfifo.capacity)),ns)
            #print(fifoObj.tokenSizeInBytes)

            try:
                fifoObj.target.connectInputFifo(fifoObj,fifoObj.target_port_id)
            except AttributeError:
                print('[ERROR] When trying connect target of "' + fifoObj.fifoId + '": Wrong actorId "'+xmlfifo.target+'" or invalid target port "'+ fifoObj.target_port_id + '" !' )
                exit()

            try:
                fifoObj.source.connectOutputFifo(fifoObj,fifoObj.source_port_id)
            except AttributeError:
                print(
                '[ERROR] When trying connect source of "' + fifoObj.fifoId + '": Wrong actorId "' + xmlfifo.source + '" or invalid source port "' + fifoObj.source_port_id + '" !')
                exit()

            tcore = fifoObj.target.owner
            score = fifoObj.source.owner
            if tcore == score:
                if tcore.arch == 'TTA':
                    memory = tcore.getMemory("data")
                    if not memory:
                        print('[ERROR] TTA "'+tcore.coreId+'" has no local memory address-space "data"')
                        print('\tWhen trying place fifo "'+ fifoObj.fifoId+'"')
                        print('\tAvailable local mens in core "'+ tcore.coreId+'" :')
                        print(tcore.localMems)
                        exit()
                    fifoObj.owner = memory
                    memory.addFifo(fifoObj)
                else:
                    memory = tcore.getMemory("data")
                    if not memory:
                        memory = MemoryObject("data")
                        memory.width = None
                        memory.minAddress = None
                        memory.maxAddress = None
                        memory.owner = tcore
                        memory.type = "local"
                        tcore.addLocalMem(memory)
                    fifoObj.owner = memory
                    memory.addFifo(fifoObj)

            else:
                targetCore = fifoObj.target.owner
                sourceCore = fifoObj.source.owner

                #TODO First check if fifo have hand tailored mapping


                memorylist = runtime.getMemoryByConnection(targetCore,sourceCore)
                if not memorylist:
                    print('[ERROR]: There is no shared memory connection between '+sourceCore.coreId +' and '+ targetCore.coreId)
                    print('         which is needed for "' + fifoObj.fifoId + '" which connects: ')
                    print('         "'+fifoObj.source.actorId + '" to "'+ fifoObj.target.actorId+'"')
                    exit()

                if len(memorylist)  == 1:
                    fifoObj.owner = memorylist[0]
                    memorylist[0].addFifo(fifoObj)
                else: #chooses memory where is most of free space
                    bestmem = memorylist[0]
                    for mem in memorylist:
                        if (mem.maxAddress-mem.addressPointer) > (bestmem.maxAddress-bestmem.addressPointer):
                            bestmem = mem
                    fifoObj.owner = bestmem
                    bestmem.addFifo(fifoObj)