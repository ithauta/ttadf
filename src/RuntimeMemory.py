
import math
import RuntimeCore
from vhdlNetworkGenerator import RtlPort,RtlGeneric,VHDLEntity
from ttadf_rtl_components import RtlMemoryArbiter

class MemoryObject:
    def __init__(self, name):
        self.name = name
        self.width = 0
        self.minAddress = 0
        self.maxAddress = 0
        self.type = None
        self.addressSpaces = {}
        self.loadStoreUnits = {}
        self.connections = []
        self.isArbiterConnection = []
        self.owner = None
        self.fifos = []
        self.addressPointer = 32
        self.arbiter = None
        self.instructions = False
        self.vhdlEntity = None

        self.rtlIfaceSuffix = ['mem_en_x', 'wr_en_x', 'wr_mask_x', 'addr', 'data_in', 'data_out']

    def getRtlIfaceSuffix(self):
        return self.rtlIfaceSuffix

    def getRtlIfaceTypes(self):
        types = []
        types.append('std_logic')
        types.append('std_logic')
        types.append('std_logic_vector(' + str(self.getRtlDataW()) + '-1 downto 0)')
        types.append('std_logic_vector(' + str(self.getRtlAddrW()) + '-1 downto 0)')
        types.append('std_logic_vector(' + str(self.getRtlDataW()) + '-1 downto 0)')
        types.append('std_logic_vector(' + str(self.getRtlDataW()) + '-1 downto 0)')
        return types


    def arbiterConnection(self):
        if self.isArbiterConnection:
            return True
        else:
            return False

    def isInstructionMem(self):
        return (self.addressSpaces[self.owner.getCoreId()] == 1)

    def getAddrWidth(self):
        return int(math.ceil(math.log(self.getLen(),2)))

    def setWidth(self,w):
        self.width = w

    def getWidth(self):
        return self.width

    def getLen(self):
        return self.maxAddress-self.minAddress+1

    def setLen(self,l):
        self.maxAddress = self.minAddress+l

    def getName(self):
        return self.name

    def onlyX86Connections(self):
        for core in self.connections:
            if core.isTTA():
                return False
        return True

    def isInterfaceMemory(self):

        tta = False
        gpp = False

        for core in self.connections:
            if core.isTTA():
                tta = True
            if not core.isTTA():
                gpp = True

        return (tta and gpp)

    def setArbiter(self,arbiter):
        self.arbiter = arbiter

    def getArbiter(self):
        return self.arbiter

    def addConnection(self,core,isArbiter):
        self.connections.append(core)
        self.isArbiterConnection.append(isArbiter)

    def getArbiterConnections(self):
        corelist = []
        for i,core in enumerate(self.connections):
            if self.isArbiterConnection[i]:
                corelist.append(core)

        return corelist

    def getDirectConnections(self):
        corelist = []
        for i,core in enumerate(self.connections):
            if not self.isArbiterConnection[i]:
                corelist.append(core)
        return corelist

    def getHostConnections(self):
        coreList = []
        for core in self.getDirectConnections():
            if not core.isTTA():
                coreList.append(core)

        for core in self.getArbiterConnections():
            if not core.isTTA():
                coreList.append(core)
        return coreList

    def getConnections(self):
        list = []
        for obj in self.getDirectConnections():
            list.append(obj)
        list.append(self.getArbiter())
        return list

    def getNumberOfMemoryPorts(self):
        if self.isInstructionMem():
            return 1
        else:
            if self.type != "shared":
                return 1
            else:
                return len([x for x in self.getConnections() if x is not None])

    def addFifo(self, fifo):

        if self.type == "shared":

            while(self.addressPointer % 4 != 0):
                self.addressPointer += 1

            if self.addressPointer % 4 != 0:
                print('[WARNING]'+ fifo.fifoId +' NOT WORD ALIGNED')
                exit(0)

            fifo.startAddr = self.addressPointer
            fifo.endAddr = (self.addressPointer + fifo.structSize + fifo.tokenSizeInBytes * fifo.capacity)-1
            if fifo.endAddr > self.maxAddress:
                print('[ERROR] "' + fifo.fifoId + '" is out of "'+self.name+'" memory range')
                print('[INFO]   Fifo need '+str(fifo.endAddr - self.maxAddress)+ ' bytes more space.')
                exit(0)
            self.addressPointer = self.addressPointer + fifo.structSize + fifo.tokenSizeInBytes * fifo.capacity + 32

        self.fifos.append(fifo)

    def getAddressSpaceForCore(self, core):
        return self.addressSpaces[core.coreId]

    def setAddressSpaceForCore(self, core,addresspace):
        self.addressSpaces[core.coreId] = addresspace

    def getLoadStoreUnitForCore(self,core):
        print self.getName()
        print self.loadStoreUnits
        return self.loadStoreUnits[core.coreId]

    def setMemTypeShared(self):
        self.type = "shared"

    def setMemTypeLocal(self):
        self.type = "local"

    def setMemOwner(self,core,forceflag):
        if not self.owner or forceflag:
            self.owner = core

    def getMemOwner(self):
        return self.owner

    def createMTIFile(self,outputDir):
        #print(outputDir)
        cont = '// memory data file (do not edit the following line - required for mem load use)\n'
        cont = '// format=mti addressradix=d dataradix=h version=1.0 wordsperline=1\n'

        for fifo in self.fifos:
            cont += fifo.getMTIInit()

        with open(outputDir +'/' +self.name +'.mti', 'w') as memInitFile:
            memInitFile.write(cont)

    def createMifFile(self,outputDir):
        #print(outputDir)
        cont = 'DEPTH = '+ str( (self.maxAddress-self.minAddress)/4) +';\n'
        cont += 'WIDTH = 32;\n'
        cont += 'ADDRESS_RADIX = HEX;\n'
        cont += 'DATA_RADIX = BIN;\n'
        cont += 'CONTENT\nBEGIN\n\n'

        for fifo in self.fifos:
            cont += fifo.getMifInit()


        cont += 'END;\n'
        with open(outputDir +'/' +self.name +'.mif', 'w') as memInitFile:
            memInitFile.write(cont)

    def getMemoryMapForCore(self,core):
        adds  = str(self.getAddressSpaceForCore(core))
        addsc = 'SET_AS('+adds+')'
        mm = '\n //Memory layout for address space '+ adds + '\n'

        mm += 'volatile unsigned int ttadf_memmap_prefix_'+adds+'[7] '+addsc+' = {13};\n'
        for fifo in self.fifos:

            storageSize = fifo.tokenSizeInBytes * fifo.capacity + 32
            if storageSize % 4 == 0:
                storageSize = str(storageSize / 4)
            else:
                storageSize = str((storageSize / 4) + 1)

            mm += '\nextern volatile unsigned int ' + fifo.fifoId + '_storage[' + storageSize + '] ' + addsc + ';\n'

            mm += 'volatile fifoType '+fifo.fifoId+ ' '+ addsc+' = ' + fifo.codeActionFifoStaticInit('&'+fifo.fifoId + '_storage' , core) +';\n'
            mm += 'volatile unsigned int ' + fifo.fifoId + '_spacer[17] ' + addsc + '= {13};\n'
            mm += 'volatile unsigned int ' + fifo.fifoId + '_storage[' + storageSize + '] ' + addsc + '= {13};\n'
        return mm

    def writeVhdlComponent(self):
        if not self.vhdlEntity:
            self.createEntity()
        return self.vhdlEntity.writeComponent()

    def setVhdlEntity(self,entity):
        self.vhdlEntity = entity

    def getVhdlEntity(self):
        if not self.vhdlEntity:
            self.createEntity()
        return self.vhdlEntity

    def getVHDLInterfacePorts(self):
        return self.getVhdlEntity().getPorts()

    def getVHDLInterfacePortsX86(self):
        list = []
        for i,connection in enumerate(self.getConnections()):
            if isinstance(connection,RuntimeCore.RuntimeCoreX86):
                for port in self.getVHDLInterfacePorts():
                    if 'p'+str(i) in port.getId():
                        list.append(port)

        return list

    def getRtlDataW(self):
        if self.isInstructionMem():
            return self.getWidth()
        else:
            return self.getWidth()*4

    def getRtlAddrW(self):
        if self.isInstructionMem():
            return self.getAddrWidth()
        else:
            return self.getAddrWidth()-2

    def getRtlMemD(self):
        if self.isInstructionMem():
            return self.getLen()
        else:
            return int(math.ceil(float(self.getLen())/4))

    def createEntity(self):

        data_width = str(self.getRtlDataW())
        addr_width = str(self.getRtlAddrW())
        mem_depth = str(self.getRtlMemD())

        entity = VHDLEntity(self.getName() + '_' + data_width + '_' + addr_width)

        entity.addPort(RtlPort('clk', 'std_logic', 'in'))

        for i in range(self.getNumberOfMemoryPorts()):
            entity.addPort(RtlPort('p'+str(i)+'_mem_en_x','std_logic','in'))
            entity.addPort(RtlPort('p'+str(i)+'_wr_en_x', 'std_logic', 'in'))
            entity.addPort(RtlPort('p'+str(i)+'_wr_mask_x', 'std_logic_vector(' + data_width + '-1 downto 0)', 'in'))
            entity.addPort(RtlPort('p'+str(i)+'_addr', 'std_logic_vector(' + addr_width + '-1 downto 0)', 'in'))
            entity.addPort(RtlPort('p'+str(i)+'_data_in', 'std_logic_vector(' + data_width + '-1 downto 0)', 'in'))
            entity.addPort(RtlPort('p'+str(i)+'_data_out', 'std_logic_vector(' + data_width + '-1 downto 0)', 'out'))

        self.setVhdlEntity(entity)

        return entity

    def createVerilog(self,masktype):

        data_width = str(self.getRtlDataW())
        addr_width = str(self.getRtlAddrW())
        mem_depth = str(self.getRtlMemD())


        v =  '//  This is automatically generated TTADF Verilog RAM COMPONENT\n'
        v += '//  Ilkka Hautala, CMVS, University Of Oulu, Finland\n'
        v += 'module '+self.getName()+'_'+data_width+'_'+addr_width+'(\n'
        v += '    clk,\n'
        for i in range(self.getNumberOfMemoryPorts()):
            v += '    p'+str(i)+'_data_out,\n'
            v += '    p'+str(i)+'_data_in,\n'
            v += '    p'+str(i)+'_mem_en_x,\n'
            v += '    p'+str(i)+'_addr,\n'
            v += '    p'+str(i)+'_wr_mask_x,\n'
            v += '    p'+str(i)+'_wr_en_x'
            if (i+1) < self.getNumberOfMemoryPorts():
                v += ',\n'
            else:
                v += '\n'
        v += ');\n'



        v += '    input clk;\n'
        for i in range(self.getNumberOfMemoryPorts()):
            v += '    output ['+data_width+' - 1:0] p'+str(i)+'_data_out;\n'
            v += '    input p'+str(i)+'_mem_en_x;\n'
            v += '    input['+addr_width+' - 1:0] p'+str(i)+'_addr;\n'
            v += '    input p'+str(i)+'_wr_en_x;\n'
            v += '    input['+data_width+' - 1:0] p'+str(i)+'_data_in;\n'
            if masktype == 'bytemask':
                v += '    input['+data_width+' / 8 - 1:0] p'+str(i)+'_wr_mask_x;\n'
            elif masktype == 'bitmask':
                v += '    input['+data_width+' - 1:0] p'+str(i)+'_wr_mask_x;\n'

        v += '// synthesis translate_off\n'

        for i in range(self.getNumberOfMemoryPorts()):
            v += '    reg['+data_width+' - 1:0] p'+str(i)+'_data_out;\n'
        v += '    reg['+data_width+' - 1:0] mem[0:'+mem_depth+' - 1];\n'

        v += '    integer i;\n'

        v += '    always @ (posedge clk) begin\n'
        for i in range(self.getNumberOfMemoryPorts()):
            v += '        if (p'+str(i)+'_mem_en_x == 0) begin\n'
            v += '            if (p'+str(i)+'_wr_en_x == 0) begin\n'
            if masktype == 'bytemask':
                v += '                for (i=0; i < '+data_width+' / 8; i = i+1) begin: wr_mask_code'+str(i)+' \n'
                v += '                    if (p'+str(i)+'_wr_mask_x[i] == 0) \n'
                v += '                        mem[p'+str(i)+'_addr][8 * i +:1] = p'+str(i)+'_data_in[8 * i +:1];\n'
                v += '                    end\n'
                v += '                end\n'
            elif masktype == 'bitmask':
                v += '                for (i=0; i < '+data_width+' ; i = i+1) begin: wr_mask_code'+str(i)+' \n'
                v += '                    if (p'+str(i)+'_wr_mask_x[i] == 0) \n'
                v += '                        mem[p'+str(i)+'_addr][i] = p'+str(i)+'_data_in[i];\n'
                v += '                    end\n'
                v += '                end\n'

            v += '            else begin\n'
            v += '                p'+str(i)+'_data_out <= mem[p'+str(i)+'_addr];\n'
            v += '            end\n'
            v += '        end\n'
        v += '    end\n'
        v += '// synthesis translate_on\n'

        v += '    endmodule\n'

        return v

class Arbiter:
    def __init__(self,name):
        self.name = name
        self.memconnection = None
        self.coreConnetions = []
        self.rtlPortMap = []
        self.rtlImplementation = None

    def getDataW(self):
        return self.getMemory().getWidth()*4

    def getCoreConnections(self):
        return self.coreConnetions

    def getName(self):
        return self.name

    def setName(self,name):
        self.name = name

    def getMemory(self):
        return self.memconnection

    def setMemory(self,memObject):
        self.memconnection = memObject

    def addCore(self,core):
        self.coreConnetions.append(core)

    def getNbCores(self):
        return len(self.coreConnetions)

    def getAllHostConnections(self):
        hosts = []
        for core in self.getCoreConnections():
            if not core.isTTA:
                hosts.append(core)
        return hosts

    def getAllHostConnectionsRTL(self):
        hosts = self.getAllHostConnections()

    def createEntity(self):
        self.rtlImplementation = RtlMemoryArbiter(self.getNbCores(),self.getMemory().getAddrWidth()-2,self.getDataW())

    def getRTLPortMap(self):
        return self.rtlPortMap

    def getRtlEntity(self):
        if not self.rtlImplementation:
            self.createEntity()
        return self.rtlImplementation.getEntity()

    def writeVhdlComponent(self):
        return self.getRtlEntity().writeComponent()


    def replaceVHDLaliases(self,string):
        string = string.replace('ports_g',str(self.getNbCores()))
        string = string.replace('dataw_g',str(self.getMemory().getRtlDataW()))
        string = string.replace('addrw_g', str(self.getMemory().getRtlAddrW()))
        return string