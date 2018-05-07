# /usr/bin/python
# -*- coding: utf-8 -*-

# TTA Dataflow Framework
# Ilkka Hautala
# ithauta@ee.oulu.fi
# Center for Machine Vision and Signal Analysis (CMVS)
# University of Oulu, Finland
#

import RuntimeSystem
import re
from TTADF_Tools import addTab



class VHDLEntity:
    def __init__(self,name):
        self.name = name
        self.ports = []
        self.generics = []

    def getId(self):
        return self.name


    def getName(self):
        return self.name

    def setName(self,name):
        self.name = name

    def setPorts(self,ports):
        self.ports = ports

    def find(self,id):
        for port in self.getPorts():
            if port.getId() == id:
                return port
        for generic in self.getGenerics():
            if generic.getId() == id:
                return generic

        print('[WARNING] Port or generic: ' + id + ' not found!')
        for port in self.getPorts():
            print('\t'+port.getId())
        for generics in self.getGenerics():
            print('\t'+generics.getId())


        return None

    def getPorts(self):
        return self.ports

    def addPort(self,port):
        if isinstance(port,RtlPort):
            self.ports.append(port)
        else:
            print('[ERROR] type of "'+port+':'+ type(port)+ 'is not required type '+type(RtlPort))

    def deletePort(self,portId):
        for port in self.ports:
            if port.getId() == portId:
                self.ports.remove(port)
                return port
        return None

    def setGenerics(self,generics):
        self.generics = generics

    def getGenerics(self):
        return self.generics

    def addGeneric(self,generic):
        if isinstance(generic,RtlGeneric):
            self.generics.append(generic)
        else:
            print('[ERROR] type of "'+generic+':'+ type(generic)+ 'is not required type '+type(RtlGeneric))

    def deleteGeneric(self,genericId):
        for generic in self.generics:
            if generic.getId() == genericId:
                self.generics.remove(generic)
                return generic
        return None

    def write(self,prefix):
        vhdlCode = ''
        vhdlCode += prefix+' '+ self.getName() + ' is\n'

        if self.generics:
            vhdlCode += addTab('generic (',1)
            vhdlCode +='\n'
            for generic in self.generics:
                vhdlCode += addTab(generic.getId() + ' : ' + generic.getType() + ' := ' + generic.getValue() , 2)
                if generic is not self.generics[-1]:
                    vhdlCode += ';\n'
                else:
                    vhdlCode += '\n'
            vhdlCode += addTab(');',1)
            vhdlCode += '\n'

        vhdlCode += addTab('port (',1)
        vhdlCode += '\n'
        for port in self.ports:
            vhdlCode += addTab(port.getId()+' : ' + port.getDir() + ' ' + port.getType(),2)
            if port is not self.ports[-1]:
                vhdlCode += ';\n'
            else:
                vhdlCode += '\n'

        vhdlCode += addTab(');', 1)
        vhdlCode += '\n'
        if(prefix == 'component'):
            vhdlCode += 'end component;\n'
        else:
            vhdlCode += 'end '+self.getName()+';\n'

        return vhdlCode

    def writeComponent(self):
        return self.write('component')

    def writeEntity(self):
        return self.write('entity')



class VHDLEntityParser:

    def __init__(self):
        pass

    def parsePorts(self,code):

        startpoint = re.search(r'port\s*\(',code)
        code = code[startpoint.end():].strip()[:-2]

        portStringArray = code.split(';')

        ports = []

        for i, array in enumerate(portStringArray):
            portStringArray[i] = array.strip()
            nameAndType = portStringArray[i].split(':')

            for j, array2 in enumerate(nameAndType):
                nameAndType[j] = array2.strip()

            name = nameAndType[0]
            dir = nameAndType[1].split()[0]
            type = nameAndType[1].split(' ',1)[1]
            ports.append(RtlPort(name,type,dir))

        return ports


    def parseFile(self,fname):
        try:
            with open(fname) as f:
                code = f.read()
        except IOError:
            print('[ERROR] VHDL file: "'+fname+ '" not found!')
            exit()

        #try find entities
        startpoint = re.search(r'entity\s*(\S*)\s*is(?:\s|.)', code)

        entityname = startpoint.groups()[0]
        newEntity = VHDLEntity(entityname)

        endpoint = re.search(r'end\s*'+entityname+'\s*;',code)

        ports = self.parsePorts(code[startpoint.end():endpoint.start()])
        newEntity.setPorts(ports)


        return newEntity


class RtlArchitecture:

    def __init__(self, impId,entityName):
        self.impId = impId
        self.entityName = entityName
        self.signals = []
        self.components = []
        self.mappings = []
        self.portMappings = []
        self.processes = []
        self.typedefs = []
        self.codelines = []


    def findSignalById(self,id):
        for signal in self.getSignals():
            if signal.getId() == id:
                #print signal
                return signal

        #print('[WARNING] Not found requested signal ' + id +' !')
        #print('Possible signal are: ')
        #for signal in self.getSignals():
        #    print('\t'+ signal.getId())

        return None

    def addTypedef(self,type):
        self.typedefs.append(type)

    def addCodeline(self,code):
        self.codelines.append(code)

    def getCodelines(self):
        return self.codelines

    def getTypedefs(self):
        return self.typedefs

    def getImpId(self):
        return self.impId

    def setImpId(self,impId):
        self.impId = impId

    def setEntityName(self,entityName):
        self.entityName = entityName

    def getEntityName(self):
        return self.entityName

    def addMapping(self,mapping):
        self.mappings.append(mapping)

    def getMappings(self):
        return self.mappings

    def addSignal(self,signal):
        self.signals.append(signal)

    def getSignals(self):
        return self.signals

    def addComponent(self,component):
        self.components.append(component)

    def getComponents(self):
        return self.components

    def addPortMap(self, portMap):
        self.portMappings.append(portMap)

    def getPortMaps(self):
        return self.portMappings

    def getProcesses(self):
        return self.processes

    def addProcess(self,process):
        self.processes.append(process)

    def write(self):
        vhdl = ''
        vhdl = 'architecture '+ self.getImpId() + ' of ' + self.getEntityName() +' is \n\n'

        for typedef in self.getTypedefs():
            vhdl += typedef.write() + ';\n'

        for signal in self.getSignals():
            vhdl += signal.write() + ';\n'

        vhdl += '\n'

        for component in self.getComponents():
            vhdl += component.writeComponent()
            vhdl += '\n'
        vhdl += '\n'

        vhdl += 'begin\n'

        for portmap in self.getPortMaps():
            vhdl += portmap.writeMapping()
            vhdl += '\n'
        vhdl += '\n'

        for process in self.getProcesses():
            vhdl += process.write()
            vhdl += '\n'

        for map in self.getMappings():
            vhdl += map.writeArch() +';\n'

        for codeline in self.getCodelines():
            vhdl += codeline +'\n'

        vhdl += '\n'
        vhdl += 'end ' + self.getImpId() +';\n'

        return vhdl


class RtlProcess:

    def __init__(self,id):
        self.id = id
        self.sensitivitylist = []
        self.variables = []
        self.code = ''

    def setId(self,id):
        self.id = id

    def getId(self):
        return self.id

    def addToSensitivitylist(self,signal):
        self.sensitivitylist.append(signal)

    def setCode(self,code):
        self.code = code

    def addVariable(self,variable):
        self.variables.append(variable)

    def getSensivityList(self):
        return self.sensitivitylist

    def getVariables(self):
        return self.variables

    def addVariable(self,variable):
        self.variables.append(variable)


    def write(self):
        vhdl = ''
        vhdl += 'process ('
        for signal in self.getSensivityList():
            vhdl += signal.getId()
            if signal is not self.getSensivityList()[-1]:
                vhdl += ', '
        vhdl += ')\n'

        for variable in self.getVariables():
            vhdl += variable.write() + ';\n'

        vhdl += 'begin \n'

        vhdl += self.getCode()
        vhdl += 'end process; \n'

        return vhdl;


class RtlVariable:

    def __init__(self,id,type):
        self.id = id
        self.type = type
        self.init = None

    def setInit(self,init):
        self.init = init

    def getInit(self):
        return self.init

    def getId(self):
        return self.id

    def getType(self):
        return self.type

    def setId(self,id):
        self.id = id

    def setType(self,type):
        self.type = type

    def write(self):
        if not self.getInit():
            return 'variable ' + self.getId() + ' : ' + self.getType()
        else:
            return 'variable ' + self.getId() + ' : ' + self.getType() + ' := ' + self.getInit()

class RtlSignal:

    def __init__(self,id,type):
        self.id = id
        self.type = type

    def getId(self):
        return self.id

    def getType(self):
        return self.type

    def setId(self,id):
        self.id = id

    def setType(self,type):
        self.type = type

    def write(self):
        return 'signal ' + self.getId() + ' : ' + self.getType()


class RtlPort:

    def __init__(self,id,type,dir):
        self.id = id
        self.type = type
        self.dir = dir

    def getId(self):
        return self.id

    def getType(self):
        return self.type

    def getDir(self):
        return self.dir

    def setId(self,id):
        self.id = id

    def setType(self,type):
        self.type = type

    def setDir(self,dir):
        self.dir = dir

    def getVhdlInterface(self):
        return self.getId() + ' : ' + self.getDir() + ' ' + self.getType()

class RtlGeneric:

    def __init__(self,id,type,value):
        self.id = id
        self.type = type
        self.value = value

    def getId(self):
        return self.id

    def getType(self):
        return self.type

    def getValue(self):
        return self.value

    def setId(self,id):
        self.id = id

    def setType(self,type):
        self.type = type

    def setValue(self,value):
        self.value = value

class RtlMapping:
    def __init__(self,source,dest):
        self.source = source
        self.dest = dest
        self.sourceSel = ''
        self.destSel = ''

    def setSourceSel(self,sel):
        self.sourceSel = sel

    def getSourceSel(self):
        return self.sourceSel

    def setDestSel(self, sel):
        self.destSel = sel

    def getDestSel(self):
        return self.destSel

    def getSource(self):
        return self.source

    def getDest(self):
        return self.dest

    def setSource(self,source):
        self.source = source

    def setDest(self,dest):
        self.dest = dest

    def write(self):
        return self.getDest().getId()+self.getDestSel() + ' => ' + self.getSource().getId()+self.getSourceSel()

    def writeGeneric(self):
        return self.getDest().getId() + ' => ' + self.getSource().getValue()

    def writeArch(self):
        target = self.getDest().getId()+self.getDestSel()
        source = self.getSource().getId()+self.getSourceSel()
        return target + ' <= ' + source

class RtlTypedef:
    def __init__(self, id,type):
        self.id = id
        self.type = type

    def getId(self):
        return self.id

    def getType(self):
        return self.type

    def setId(self,id):
        self.id = id

    def setType(self,type):
        self.type = type

    def write(self):
        return 'type ' + self.getId() + ' ' + self.getType()


class PortMap:
    def __init__(self,inst_id, component):
        self.id = inst_id
        self.component = component
        self.portMappings = []
        self.genericMappings = []

    def getComponent(self):
        return self.component

    def getId(self):
        return self.id

    def addGenericMapping(self,mapping):
        self.genericMappings.append(mapping)

    def getGenericMapping(self):
        return self.genericMappings

    def addPortMapping(self,mapping):
        found = None
        for port in self.component.getPorts():
            if port.getId() == mapping.getSource().getId():
                self.portMappings.append(mapping)
                found = mapping
                break
            elif port.getId() == mapping.getDest().getId():
                self.portMappings.append(mapping)
                found = mapping
                break

        if not found:
            print('[Warning] Cant create portmap: ' + mapping.getSource().getId() + ' => ' + mapping.getDest().getId()+'!\n')
            print('\t VHDL implementation won\'t be functional\n')

        return found

    def getPortMapping(self):
        return self.portMappings

    def addGenericMapping(self,mapping):
        found = None
        for port in self.component.getGenerics():
            self.genericMappings.append(mapping)
            found = mapping
            break

        if not found:
            print('[Warning] Cant create generic map: ' + mapping.getSource().getId() + ' => ' + mapping.getDest().getId()+'!\n')
            print('\t VHDL implementation won\'t be functional\n')

        return found

    def writeMapping(self):
        vhdl = ''
        vhdl += self.getId() + ' : ' + self.getComponent().getId() + '\n'

        if len(self.getGenericMapping()):
            vhdl += 'generic map ('
            vhdl += '\n'

            for map in self.getGenericMapping():
                vhdl += '\t'+ map.writeGeneric()
                if map is self.getGenericMapping()[-1]:
                    vhdl += '\n)\n'
                else:
                    vhdl += ',\n'

        vhdl += 'port map ('
        vhdl += '\n'

        for map in self.getPortMapping():
            vhdl += '\t' + map.write()
            if map is self.getPortMapping()[-1]:
                vhdl += '\n);\n'
            else:
                vhdl += ',\n'

        return vhdl

class RtlFile():

    def __init__(self,id):
        self.id = id
        self.architectures = []
        self.libraries = []
        self.entity = None

    def setId(self,id):
        self.id = id

    def getId(self):
        return self.id

    def addArchitecture(self,architecture):
        self.architectures.append(architecture)

    def getArchitectures(self):
        return self.architectures

    def addLibrary(self,library):
        self.libraries.append(library)

    def getLibraries(self):
        return self.libraries

    def setEntity(self,entity):
        self.entity = entity

    def getEntity(self):
        return self.entity

    def write(self):

        vhdl = ''
        vhdl += '---------------------------------------------------------------\n'
        vhdl += '-- This file is automatically generated by using \n'
        vhdl += '-- TTADF Framework\n'
        vhdl += '-- Ilkka Hautala \n'
        vhdl += '-- Center for Machine Vision and Signal Analysis \n'
        vhdl += '-- University of Oulu \n'
        vhdl += '-- FINLAND \n'
        vhdl += '---------------------------------------------------------------\n'

        for lib in self.getLibraries():
            vhdl += lib +';\n'
        vhdl += '\n'

        vhdl += self.getEntity().writeEntity()

        vhdl += '\n'

        for arch in self.getArchitectures():
            vhdl += arch.write()

        return vhdl



class VhdlNetworkGenerator:

    def __init__(self, system, rootdir):

        self.rootdir = rootdir
        self.toplevelSourceFile = ''
        self.libraryList = ['ieee.std_logic_1164.all',
                           'ieee.numeric_std.all'
                           ]

        self.system = system




    def createHdl(self,filename):
        sf = open(self.rootdir + '/' + filename, "w")

        sf += '---------------------------------------------------------------'
        sf += '-- This file is automatically generated by using \n'
        sf += '-- TTADF Framework\n'
        sf += '-- Ilkka Hautala \n'
        sf += '-- Center for Machine Vision and Signal Analysis \n'
        sf += '-- University of Oulu \n'
        sf += '-- FINLAND \n'
        sf += '---------------------------------------------------------------'

        sf.write('library ieee;\n')
        for library in self.libraryList:
            sf.write('use '+library+';\n')


        sf.write('entity '+ self.system.getSystemArchitectureName()+' is')
        sf.write