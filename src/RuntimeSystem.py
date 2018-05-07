from functools import reduce

from lxml import etree, objectify
from optparse import OptionParser
from subprocess import call, check_output
from shutil import copy2
import os
import re
import Network
import TTADF_Tools
import systemCRuntime


class RuntimeSystem:
    def __init__(self, name, networkName="unnamed_network", architechtureName="unnamed_architechture"):
        self.name = name
        self.networkName = networkName
        self.systemArchitectureName = architechtureName
        self.cores = []
        self.memories = []
        self.memArbiters = []


    def getName(self):
        return self.name

    def setName(self,name):
        self.name = name

    def setSystemArchitectureName(self,name):
        self.systemArchitecture = name

    def getSystemArchitectureName(self):
        return self.systemArchitectureName

    def getAllMemories(self):
        return self.memories

    def getAllHostInterfaceMemories(self):
        memlist = []
        for mem in self.getAllMemories():
            if mem.isInterfaceMemory():
                memlist.append(mem)

        return memlist

    def getCPSMems(self):
        memlist = []
        for mem in self.getAllMemories():
            if not mem.onlyX86Connections():
                memlist.append(mem)
        return memlist


    def addNewArbiter(self,arbiterObject):
        self.memArbiters.append(arbiterObject)

    def getArbiterByName(self,name):
        for arbiter in self.getAllArbiters():
            if arbiter.getName() == name:
                return arbiter
        return None

    def getAllArbiters(self):
        return  self.memArbiters

    def addNewCore(self, core):
        for coreObject in self.cores:
            if coreObject.coreId == core.coreId:
                print("[ Warning ] " + core.coreId + " already exists in system")
                return None

        core.numericId = len(self.cores) + 1

        self.cores.append(core)

    def addNewMemory(self, memory):
        memFound = 0
        for memObject in self.memories:
            if memObject.name == memory.name:
                memFound = 1
                memObject.setAddressSpaceForCore(memory.owner.coreId, memory.getAddressSpaceForCore(memory.owner))
        if not memFound:
            self.memories.append(memory)

    def getCoreById(self, coreId):
        for core in self.cores:
            if core.coreId == coreId:
                return core
        return None

    def getMemoryByName(self, name):
        for mem in self.memories:
            if mem.name == name:
                return mem
        return None

    def getMemoryByConnection(self,core1,core2):
        memlist = []
        for mem in self.memories:
            if core1 in mem.connections and core2 in mem.connections:
                memlist.append(mem)

        if len(memlist) == 0:
            return None
        else:
            return  memlist

    def getActorById(self, actorId):
        for core in self.cores:
            actor = core.getActorById(actorId)
            if actor:
                return actor
        return None

    def getAllX86Cores(self):
        x86CoreList = []
        for core in self.cores:
            if core.arch == 'X86' and core.actors:
                x86CoreList.append(core)
        return x86CoreList

    def getAllHostCores(self):
        return self.getAllX86Cores()

    def getAllTTACores(self):
        ttaCoreList = []
        for core in self.cores:
            if core.arch == 'TTA':
                if core.actors:
                    ttaCoreList.append(core)
        return ttaCoreList


    def createDotGraph(self,outdir):

        colorTable = ['"#1E90FF"', '"#AF593E"', '"#01A368"', '"#FF861F"', '"#ED0A3F"', '"#76D7EA"','"#8359A3"','"#C5E17A"','"#FFDF00"','"#E96792"', '"#404E5A"', '"#D0FF14"','"#BC6CAC"']
        colorDict = {}
        for i,core in enumerate(self.cores):
            colorDict[core.coreId] = colorTable[i%len(colorTable)]

        graph_txt = "digraph " + self.networkName + " {\n"

        for mem in self.memories:
            for fifo in mem.fifos:
                graph_txt += fifo.source.actorId + '[style="filled"] [color="#333334"] [fillcolor='+colorDict[fifo.source.owner.coreId]+'];'
                graph_txt += fifo.target.actorId + '[style="filled"] [color="#333334"][fillcolor=' + colorDict[fifo.target.owner.coreId] + '];'
                graph_txt += "\t" + fifo.source.actorId + "-> "+ fifo.target.actorId + ";\n"

        for core in self.cores:
            for mem in core.localMems:
                for fifo in mem.fifos:
                    graph_txt += fifo.source.actorId + '[style="filled"] [color="#333334"] [fillcolor=' + colorDict[fifo.source.owner.coreId] + '];'
                    graph_txt += fifo.target.actorId + '[style="filled"] [color="#333334"] [fillcolor=' + colorDict[fifo.target.owner.coreId] + '];'
                    graph_txt += "\t" + fifo.source.actorId + "-> " + fifo.target.actorId + ";\n"

        graph_txt = graph_txt + "}\n"

        outputDot = open(outdir + self.networkName + ".dot", 'w')
        outputDot.write(graph_txt)
        outputDot.close()

        call(["dot", "-T", "png", outdir + self.networkName + ".dot", "-o", outdir + self.networkName + ".png"])