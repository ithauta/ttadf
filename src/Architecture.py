from functools import reduce

from lxml import etree, objectify
from optparse import OptionParser
from subprocess import call, check_output
from shutil import copy2
import os
import re
import TTADF_Tools
import systemCRuntime
from RuntimeCore import RuntimeCore, RuntimeCoreX86, RuntimeCoreTTA
from RuntimeMemory import MemoryObject, Arbiter


class Architecture:
    def __init__(self, architectureFilename):
        try:
            with open(architectureFilename) as f:
                self.xml_architecture = f.read()
        except IOError:
            print('[ERROR] System architechture file: "'+architectureFilename+ '" not found!')
            exit()

        self.architecture = objectify.fromstring(self.xml_architecture)

        self.name = (self.architecture.get("name"))

    def findCoreById(self, coreId):
        for core in self.architecture.core:
            if core.get("id") == coreId:
                return core
        return None

    def getMemoryAddrSpaceFromCore(self, memoryId, coreId):
        for core in self.architecture.core:
            if core.get("id") == coreId:
                for mem in core.mems.addrspace:
                    if mem == memoryId:
                        return mem.get("id")
        return None

    def addCoresToRuntime(self, runtime):

        runtime.setSystemArchitectureName(self.name)

        for core in self.architecture.core:

            clkf = 1
            if core.clkf:
                clkf = core.clkf

            compilerflags = ''
            try:
                if core.cflags:
                    compilerflags = str(core.cflags)
            except AttributeError:
                print('[INFO] Core "'+core.get("id")+'" has no compiler flags ')

            if core.arch == 'TTA':
                ttaCore = RuntimeCoreTTA(core.get("id"), str(core.name), clkf, str(core.deffile))
                ttaCore.setCompilerFlags(compilerflags)
                ttaCore.checkHwFifoExtensionSupport()

                hwDefFile = ''
                try:
                    if core.hwdef:
                        hwDefFile = str(core.hwdef)
                        ttaCore.setHWDefFile(hwDefFile)
                except AttributeError:
                    print('[WARNING] Core "' + core.get(
                    "id") + '" has no hardware definition, hardware description files cannot be created!')

                runtime.addNewCore(ttaCore)
            elif core.arch == 'X86' or core.arch == 'X86_64' or core.arch == 'ARM64' or core.arch == 'ARMv8':
                x86Core = RuntimeCoreX86(core.get("id"), str(core.name), clkf, 64)
                x86Core.setCompilerFlags(compilerflags)
                runtime.addNewCore(x86Core)
            elif core.arch == 'ARM32' or core.arch == 'X86_32' or core.arch == 'ARMv7':
                x86Core = RuntimeCoreX86(core.get("id"), str(core.name), clkf, 32)
                x86Core.setCompilerFlags(compilerflags)
                runtime.addNewCore(x86Core)


    def addMemoriesToRuntime(self, runtime):

        try:
            for memory in self.architecture.memory:
                name = memory.get("id")
                mem = MemoryObject(name)
                mem.type = "shared"
                mem.width = int(memory.width)
                mem.minAddress = int(memory['min-address'])
                mem.maxAddress = int(memory['max-address'])
                runtime.addNewMemory(mem)
                print('[INFO] Added memory ' + mem.name + ' to system architecture.')

        except AttributeError:
            print('[INFO] No shared memories in architecture.')

        try:
            for xmlArb in self.architecture.arbiter:
                name = xmlArb.get('id')
                arbiter = Arbiter(name)
                arbiter.setMemory(runtime.getMemoryByName(xmlArb))
                arbiter.getMemory().setArbiter(arbiter)
                runtime.addNewArbiter(arbiter)
        except AttributeError:
            print('[INFO] No arbiters in architecture.')


        for core in runtime.cores:

            for xmlcore in self.architecture.core:
                if xmlcore.get('id') == core.coreId:
                    if core.arch == 'X86':
                        try:
                            for connect in xmlcore.connect:
                                mem = runtime.getMemoryByName(connect)
                                arbiter = runtime.getArbiterByName(connect)

                                if arbiter:  # check if memory is connect using arbiter
                                    arbiter.addCore(core)
                                    mem = arbiter.getMemory()

                                    if core not in mem.connections:
                                        mem.addConnection(core,True)

                                    if mem:
                                        print('[INFO] Core "' + core.coreId + '" is connected to memory "' + mem.name + '" using arbiter "' + arbiter.getName()+'"')

                                if mem:
                                    if mem not in core.externalMems:
                                        core.addExternalMem(mem)
                                    if core not in mem.connections:
                                        mem.addConnection(core,False)
                                else:
                                    print('ERROR: Core "'+core.coreId+ '" connection to memory "'+connect+'" failed: memory not found!')
                                    exit()

                        except AttributeError:
                            print('[INFO] "'+core.coreId+'" has no shared memory connections specified in architecture file.')

                    if core.arch == 'TTA':
                        #try:
                        for lsuconnect in xmlcore['lsu-connect']:
                            lsuname = lsuconnect.get('lsu')
                            mem = runtime.getMemoryByName(lsuconnect)
                            isArbiter = False
                            if not mem: #check if memory is connect using arbiter
                                arbiter = runtime.getArbiterByName(lsuconnect)
                                arbiter.addCore(core)
                                mem = arbiter.getMemory()
                                if mem:
                                    print('[INFO] Core "'+core.coreId+ '" is connected to memory "'+ mem.name + '" using arbiter "'+arbiter.getName()+'"')
                                    isArbiter = True
                            if mem:
                                if not mem in core.externalMems:
                                    core.addExternalMem(mem)
                                    memoryNumericalId = core.addExternalLoadStoreUnit(mem, lsuname)
                                    mem.setAddressSpaceForCore(core, memoryNumericalId)
                                    mem.setMemTypeShared()
                                    mem.setMemOwner(core,False)
                                else:
                                    memoryNumericalId = mem.getAddressSpaceForCore(core)

                                foundlsu = False

                                myE = objectify.ElementMaker(annotate=False)
                                ADDRESSPACE = getattr(myE, "address-space")

                                for fu in core.archDef['function-unit']:
                                    try:
                                        if fu.get('name') == lsuname:
                                            fu.remove(fu['address-space'])
                                            foundlsu = True
                                            fu.append(ADDRESSPACE(mem.name))
                                            break
                                    except:
                                        pass

                                if not(foundlsu):
                                    print('[ERROR] When trying connect lsu "'+lsuname+'" of core "'+core.coreId+'" to memory "'+mem.name+'" :')
                                    print('\tmemory not found!')
                                    exit(0)

                                if core not in mem.connections:

                                    key = 0
                                    for item in core.archDef.iterchildren():
                                        key += 1
                                        if item.tag == 'global-control-unit':
                                            break

                                    mem.addConnection(core,isArbiter)

                                    myE = objectify.ElementMaker(annotate=False)
                                    ADDRESSPACE = getattr(myE, "address-space")
                                    WIDTH = myE.width
                                    MINADDRESS = getattr(myE, "min-address")
                                    MAXADDRESS = getattr(myE, "max-address")
                                    SHAREDMEMORY = getattr(myE, "shared-memory")
                                    NUMERICALID = getattr(myE, "numerical-id")

                                    addresspace = ADDRESSPACE(
                                        WIDTH(mem.width),
                                        MINADDRESS(mem.minAddress),
                                        MAXADDRESS(mem.maxAddress),
                                        SHAREDMEMORY(1),
                                        NUMERICALID(memoryNumericalId),
                                        name = mem.name
                                    )

                                    core.archDef.insert(key-1,addresspace)
                                    #core.archDef.append(addresspace)

                            else:
                                print('ERROR: Core "'+core.coreId+ '" connection to memory "'+lsuconnect+'" failed: memory not found!')
                                exit()
                        #except AttributeError:
                        #    print('[INFO] TTA "' + core.coreId + '" has no shared memory connections (no LSU connection) specified in architecture file.')

                    if core.arch == 'TTA':
                         with open(core.deffile) as f:
                             coreAdf = f.read()
                         coreAdf = objectify.fromstring(coreAdf.encode('utf8'))


                         for addrspace in coreAdf['address-space']:
                             name = addrspace.get('name')
                             width = addrspace.width
                             minAddress = addrspace['min-address']
                             maxAddress = addrspace['max-address']
                             numericalid = addrspace['numerical-id']
                             try:
                                 shared = addrspace['shared-memory']
                             except AttributeError:
                                 shared = 0


                             if not shared:
                                 mem = MemoryObject(name)
                                 mem.width = width
                                 mem.minAddress = minAddress
                                 mem.maxAddress = maxAddress
                                 mem.addressSpaces[core.coreId] = numericalid
                                 mem.owner = core
                                 mem.type = "local"



                                 #find LSU connected to it


                                 for fu in coreAdf['function-unit']:

                                    if fu['address-space'] == name:
                                        print '[INFO] Memory "' + name + '" is connected to fu ' + fu.get('name')

                                        try:
                                            mem.loadStoreUnits[core.coreId].append(fu.get('name'))
                                        except KeyError:
                                            mem.loadStoreUnits[core.coreId] = []
                                            mem.loadStoreUnits[core.coreId].append(fu.get('name'))
                                 core.addLocalMem(mem)

                                 print('[INFO] local memory '+name)

        for core in runtime.getAllTTACores():
            #check that all memories have address-space in core deffile
            for mem in core.externalMems:
                try:
                    mem.getAddressSpaceForCore(core)
                except KeyError:
                    print('[ERROR] Memory "'+mem.name+'" has no address-space in "'+core.coreId+'" !')
                    exit()