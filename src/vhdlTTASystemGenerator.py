# /usr/bin/python
# -*- coding: utf-8 -*-

# Ilkka Hautala
# ithauta@ee.oulu.fi
# Center for Machine Vision and Signal Analysis (CMVS)
# University of Oulu, Finland
#

import RuntimeSystem, RuntimeCore, RuntimeMemory
import math
import vhdlNetworkGenerator
import ttadf_rtl_components
import copy
from TTADF_Tools import addTab
from vhdlNetworkGenerator import *
from vhdlNetworkGenerator import RtlMapping


class vhdlTTACoreWrapper(RtlFile):

    def __init__(self,id,core):
        RtlFile.__init__(self,id)
        self.core = core

        self.addLibrary('library IEEE')
        self.addLibrary('use IEEE.std_logic_1164.all')
        self.addLibrary('use IEEE.std_logic_arith.all')
        self.addLibrary('use work.tce_util.all')
        self.addLibrary('use work.'+self.core.getCoreId()+'_globals.all')
        self.addLibrary('use work.'+self.core.getCoreId() + '_imem_mau.all')
        self.addLibrary('use work.'+self.core.getCoreId()+'_params.all')

        entity = copy.deepcopy(self.core.getRTLEntity())
        entity.setName('wrapper_'+self.core.getCoreId())

        #find internal memory ports DATAMEM and instructions MEMORY
        deletedPorts = []
        deletedPorts.append([entity.deletePort('imem_en_x'), 'wire_imem_mem_en_x'])
        deletedPorts.append([entity.deletePort('imem_addr'), 'wire_imem_addr'])
        deletedPorts.append([entity.deletePort('imem_data'), 'wire_imem_data_out'])


        for LSU in self.core.getLoadStoreUnits():
            memObj = LSU[0]
            entity.find('fu_'+LSU[1]+'_mem_en_x').setType('std_logic')
            entity.find('fu_'+LSU[1]+'_wr_en_x').setType('std_logic')
            entity.find('fu_'+LSU[1]+'_wr_mask_x').setType('std_logic_vector('+str(memObj.getRtlDataW()-1)+' downto 0)')
            entity.find('fu_'+LSU[1]+'_addr').setType('std_logic_vector('+str(memObj.getRtlAddrW()-1)+' downto 0)')
            entity.find('fu_'+LSU[1]+'_data_in').setType('std_logic_vector('+str(memObj.getRtlDataW()-1)+' downto 0)')
            entity.find('fu_'+LSU[1]+'_data_out').setType('std_logic_vector('+str(memObj.getRtlDataW()-1)+' downto 0)')


        for mem in self.core.getLocalMems():
            try:
                for LSU in mem.loadStoreUnits[core.getCoreId()]:
                    prefix = 'wire_'+LSU+'_'+mem.getName()
                    deletedPorts.append([entity.deletePort('fu_' + LSU + '_mem_en_x'),prefix+'_mem_en_x'])
                    deletedPorts.append([entity.deletePort('fu_' + LSU + '_wr_en_x'),prefix+'_wr_en_x'])
                    deletedPorts.append([entity.deletePort('fu_' + LSU + '_wr_mask_x'),prefix+'_wr_mask_x'])
                    deletedPorts.append([entity.deletePort('fu_' + LSU + '_addr'),prefix+'_addr'])
                    deletedPorts.append([entity.deletePort('fu_' + LSU + '_data_in'),prefix+'_data_in'])
                    deletedPorts.append([entity.deletePort('fu_' + LSU + '_data_out'),prefix+'_data_out'])

            except KeyError:
                pass

        core.setWrapperRtlEntity(entity)
        arch = RtlArchitecture('rtl',entity.getName())
        arch.addComponent(self.core.getRTLEntity())

        for LSU in self.core.getLoadStoreUnits():
            memObj = LSU[0]
            prefix = 'w_fu_'+LSU[1]
            arch.addSignal(RtlSignal(prefix+'_mem_en_x', 'std_logic_vector(0 downto 0)'))
            arch.addSignal(RtlSignal(prefix+'_wr_en_x', 'std_logic_vector(0 downto 0)'))
            arch.addSignal(RtlSignal(prefix+'_wr_mask_x','std_logic_vector('+ str(memObj.getRtlDataW())+'-1 downto 0)'))
            arch.addSignal(RtlSignal(prefix+'_addr','std_logic_vector('+str(memObj.getRtlAddrW())+'-1 downto 0)'))
            arch.addSignal(RtlSignal(prefix+'_data_in','std_logic_vector('+str(memObj.getRtlDataW())+'-1 downto 0)'))
            arch.addSignal(RtlSignal(prefix+'_data_out','std_logic_vector('+str(memObj.getRtlDataW())+'-1 downto 0)'))

        # generate generic data memory and instruction memory
        for mem in core.getLocalMems():
            if mem.addressSpaces[core.getCoreId()] == 1:  # Instruction Memory
                arch.addSignal(RtlSignal('wire_imem_mem_en_x','std_logic'))
                arch.addSignal(RtlSignal('wire_imem_wr_en_x', 'std_logic'))
                arch.addSignal(RtlSignal('wire_imem_wr_mask_x', 'std_logic_vector('+str(mem.getRtlDataW()) +'-1 downto 0)'))
                arch.addSignal(RtlSignal('wire_imem_addr', 'std_logic_vector('+str(mem.getRtlAddrW()) +'-1 downto 0)'))
                arch.addSignal(RtlSignal('wire_imem_data_in', 'std_logic_vector('+str(mem.getRtlDataW()) +'-1 downto 0)'))
                arch.addSignal(RtlSignal('wire_imem_data_out', 'std_logic_vector(' + str(mem.getRtlDataW()) + '-1 downto 0)'))
            else:
                for LSU in mem.loadStoreUnits[core.getCoreId()]:
                    prefix = LSU+'_'+mem.getName()
                    arch.addSignal(RtlSignal('wire_'+prefix+'_mem_en_x','std_logic_vector(0 downto 0)'))
                    arch.addSignal(RtlSignal('wire_'+prefix+'_wr_en_x', 'std_logic_vector(0 downto 0)'))
                    arch.addSignal(RtlSignal('wire_'+prefix+'_wr_mask_x', 'std_logic_vector('+str(mem.getRtlDataW()) +'-1 downto 0)'))
                    arch.addSignal(RtlSignal('wire_'+prefix+'_addr', 'std_logic_vector('+str(mem.getRtlAddrW()) +'-1 downto 0)'))
                    arch.addSignal(RtlSignal('wire_'+prefix+'_data_in', 'std_logic_vector('+str(mem.getRtlDataW()) +'-1 downto 0)'))
                    arch.addSignal(RtlSignal('wire_'+prefix+'_data_out', 'std_logic_vector(' + str(mem.getRtlDataW()) + '-1 downto 0)'))

        for mem in core.getLocalMems():
            arch.addComponent(mem.getVhdlEntity())
            rtlCode = mem.createVerilog('bitmask')
            f = open(core.getHdlFileDir()+'/mem_'+mem.getName()+'.v', 'w')
            f.write(rtlCode)
            f.close()


        for mem in core.getLocalMems():
            mem_portmap = PortMap('inst_' + mem.getName(), mem.getVhdlEntity())

            mapping = RtlMapping(entity.find('clk'), mem.getVhdlEntity().find('clk'))
            mem_portmap.addPortMapping(mapping)

            if mem.addressSpaces[core.getCoreId()] == 1:  # Instruction Memory

                mapping = RtlMapping(arch.findSignalById('wire_imem_mem_en_x'),mem.getVhdlEntity().find('p0_mem_en_x'))
                mem_portmap.addPortMapping(mapping)

                mapping = RtlMapping(arch.findSignalById('wire_imem_wr_en_x'), mem.getVhdlEntity().find('p0_wr_en_x'))
                mem_portmap.addPortMapping(mapping)
                mapping = RtlMapping(arch.findSignalById('wire_imem_wr_mask_x'), mem.getVhdlEntity().find('p0_wr_mask_x'))
                mem_portmap.addPortMapping(mapping)
                mapping = RtlMapping(arch.findSignalById('wire_imem_addr'), mem.getVhdlEntity().find('p0_addr'))
                mem_portmap.addPortMapping(mapping)
                mapping = RtlMapping(arch.findSignalById('wire_imem_data_out'), mem.getVhdlEntity().find('p0_data_out'))
                mem_portmap.addPortMapping(mapping)
                mapping = RtlMapping(arch.findSignalById('wire_imem_data_in'), mem.getVhdlEntity().find('p0_data_in'))
                mem_portmap.addPortMapping(mapping)

            else:
                for i,LSU in enumerate(mem.loadStoreUnits[core.getCoreId()]):
                    prefix = 'wire_'+LSU + '_' + mem.getName()
                    prefix2 = 'p'+str(i)+'_'
                    mapping = RtlMapping(arch.findSignalById(prefix+ '_mem_en_x'),mem.getVhdlEntity().find(prefix2+'mem_en_x'))
                    mapping.setSourceSel('(0)')
                    mem_portmap.addPortMapping(mapping)
                    mapping = RtlMapping(arch.findSignalById(prefix+ '_wr_en_x'),mem.getVhdlEntity().find(prefix2 + 'wr_en_x'))
                    mapping.setSourceSel('(0)')
                    mem_portmap.addPortMapping(mapping)
                    mapping = RtlMapping(arch.findSignalById(prefix+ '_wr_mask_x'),mem.getVhdlEntity().find(prefix2 + 'wr_mask_x'))
                    mem_portmap.addPortMapping(mapping)
                    mapping = RtlMapping(arch.findSignalById(prefix+ '_addr'),mem.getVhdlEntity().find(prefix2 + 'addr'))
                    mem_portmap.addPortMapping(mapping)
                    mapping = RtlMapping(arch.findSignalById(prefix+ '_data_out'),mem.getVhdlEntity().find(prefix2 + 'data_in'))
                    mem_portmap.addPortMapping(mapping)
                    mapping = RtlMapping(arch.findSignalById(prefix + '_data_in'),mem.getVhdlEntity().find(prefix2 + 'data_out'))
                    mem_portmap.addPortMapping(mapping)

            arch.addPortMap(mem_portmap)


        core_portmap = PortMap('inst_'+core.getCoreId(),core.getRTLEntity())

        for port in core.getRTLEntity().getPorts():
            signalname = None
            for i in range(len(deletedPorts)):
                if deletedPorts[i][0].getId() == port.getId():
                    signalname = deletedPorts[i][1]
                    mapping = RtlMapping(arch.findSignalById(signalname),port)
                    core_portmap.addPortMapping(mapping)
            if not signalname:
                if(arch.findSignalById('w_'+port.getId())):
                    mapping = RtlMapping(arch.findSignalById('w_'+port.getId()),port)
                    core_portmap.addPortMapping(mapping)
                    if(port.getDir() == 'out'):
                        mapping = RtlMapping(arch.findSignalById('w_'+port.getId()),port)
                        if '_mem_en_x' in port.getId():
                            mapping.setSourceSel('(0)')
                        elif '_wr_en_x' in port.getId():
                            mapping.setSourceSel('(0)')
                    else:
                        mapping = RtlMapping(port,arch.findSignalById('w_'+port.getId()))
                        if '_mem_en_x' in port.getId():
                            mapping.setDestSel('(0)')
                        elif '_wr_en_x' in port.getId():
                            mapping.setDestSel('(0)')


                    arch.addMapping(mapping)
                else:
                    mapping = RtlMapping(entity.find(port.getId()),port)
                    core_portmap.addPortMapping(mapping)

        arch.addPortMap(core_portmap)

        self.setEntity(entity)
        self.addArchitecture(arch)





class vhdlTTASystemGenerator(RtlFile):

    def __init__(self, system, rootdir):
        RtlFile.__init__(self, system.getName())
        self.rootdir = rootdir
        self.toplevelSourceFile = ''

        self.addLibrary('library IEEE')
        self.addLibrary('use IEEE.std_logic_1164.all')
        self.addLibrary('use IEEE.std_logic_arith.all')


        self.system = system
        self.setEntity(self.createEntity())
        self.addArchitecture(self.createArchitecture())

        for ttaCore in self.system.getAllTTACores():
            self.addLibrary('use work.'+ttaCore.getCoreId() + '_globals.all')
            self.addLibrary('use work.'+ttaCore.getCoreId() + '_imem_mau.all')
            self.addLibrary('use work.'+ttaCore.getCoreId() + '_params.all')

    def getEntity(self):
        return self.entity

    def createEntity(self):

        entity = vhdlNetworkGenerator.VHDLEntity('TTA_CPS_'+self.system.getName())

        port = vhdlNetworkGenerator.RtlPort('clk', 'std_logic', 'in')
        entity.addPort(port)

        port = vhdlNetworkGenerator.RtlPort('rst_x', 'std_logic', 'in')
        entity.addPort(port)

        for ttaCore in self.system.getAllTTACores():

            port = vhdlNetworkGenerator.RtlPort('clk_'+ttaCore.getCoreId(),'std_logic','in')
            entity.addPort(port)

        for ttaCore in self.system.getAllTTACores():
            port = vhdlNetworkGenerator.RtlPort('rst_'+ttaCore.getCoreId(),'std_logic','in')
            entity.addPort(port)

        for ttaCore in self.system.getAllTTACores():
            port = vhdlNetworkGenerator.RtlPort('busy_'+ttaCore.getCoreId(),'std_logic','in')
            entity.addPort(port)

        for index, mem in enumerate(self.system.getAllHostInterfaceMemories()):
            for core in mem.getHostConnections():
                for port in mem.getVHDLInterfacePortsX86():
                    copyPort = copy.deepcopy(port)
                    copyPort.setId(mem.getName()+'_'+core.getCoreId()+'_'+copyPort.getId())
                    entity.addPort(copyPort)

        return entity

    def createArchitecture(self):

        arch = vhdlNetworkGenerator.RtlArchitecture('structural',self.entity.getName())

        globallockComponent = ttadf_rtl_components.RTLGlobalLockOr('temp',2)

        for core in self.system.getAllTTACores():
            arch.addComponent(core.getWrapperRtlEntity())

        if len(self.system.getAllTTACores()):
            arch.addComponent(globallockComponent.getEntity())

        for mem in self.system.getCPSMems():
            arch.addComponent(mem.getVhdlEntity())

        for arbiter in self.system.getAllArbiters():
            arch.addComponent(arbiter.getRtlEntity())

        #connect globalLockComponents

        for core in self.system.getAllTTACores():
            portmap_core = vhdlNetworkGenerator.PortMap('inst_'+core.getCoreId(), core.getWrapperRtlEntity())

            signal = vhdlNetworkGenerator.RtlSignal('w_glock_'+core.getCoreId(), 'std_logic')
            signal2 = signal
            arch.addSignal(signal)

            portmap_glock = vhdlNetworkGenerator.PortMap('inst_'+core.getCoreId()+'_'+globallockComponent.getEntity().getId(), globallockComponent.getEntity())
            mapping = vhdlNetworkGenerator.RtlMapping(signal, globallockComponent.getEntity().find('glock'))
            portmap_glock.addPortMapping(mapping)


            generic = vhdlNetworkGenerator.RtlGeneric('glockinputs','integer', str(len(core.getArbiters())+1))
            mapping = vhdlNetworkGenerator.RtlMapping(generic,globallockComponent.getEntity().find('glockinputs'))
            portmap_glock.addGenericMapping(mapping)
            signal = vhdlNetworkGenerator.RtlSignal('w_glocks_'+core.getCoreId(), 'std_logic_vector('+str(len(core.getArbiters()))+' downto 0)')
            arch.addSignal(signal)
            mapping = vhdlNetworkGenerator.RtlMapping(signal, globallockComponent.getEntity().find('glocks'))
            portmap_glock.addPortMapping(mapping)

            mapping = vhdlNetworkGenerator.RtlMapping(self.entity.find('busy_'+core.getCoreId()),signal)
            mapping.setDestSel('(0)')
            arch.addMapping(mapping)

            mapping = vhdlNetworkGenerator.RtlMapping(signal2, core.getWrapperRtlEntity().find('busy'))
            portmap_core.addPortMapping(mapping)

            mapping = vhdlNetworkGenerator.RtlMapping(self.entity.find('clk_'+core.getCoreId()), core.getWrapperRtlEntity().find('clk'))
            portmap_core.addPortMapping(mapping)

            mapping = vhdlNetworkGenerator.RtlMapping(self.entity.find('rst_'+core.getCoreId()), core.getWrapperRtlEntity().find('rstx'))
            portmap_core.addPortMapping(mapping)

            signalList = ['mem_en_x', 'wr_en_x', 'wr_mask_x', 'addr', 'data_in', 'data_out']
            signalList2 = ['mem_en_x', 'wr_en_x', 'wr_mask_x', 'addr', 'data_out','data_in']
            for lsu in core.getLoadStoreUnits():
                for i,port in enumerate(signalList):
                    signal2 = core.getWrapperRtlEntity().find('fu_'+lsu[1]+'_'+port)

                    signal = vhdlNetworkGenerator.RtlSignal('w_'+core.getCoreId()+'_'+lsu[1]+'_'+signalList2[i],signal2.getType())
                    mapping = vhdlNetworkGenerator.RtlMapping(signal, signal2)
                    arch.addSignal(signal)
                    portmap_core.addPortMapping(mapping)

            for i,arbiter in enumerate(core.getArbiters()):
                signal = vhdlNetworkGenerator.RtlSignal('w_wait_rq_' + arbiter.getName()+'_'+core.getCoreId(), 'std_logic')
                arch.addSignal(signal)
                mapping = vhdlNetworkGenerator.RtlMapping(signal,arch.findSignalById('w_glocks_'+core.getCoreId()))
                mapping.setDestSel('('+str(i+1)+')')
                arch.addMapping(mapping)


            arch.addPortMap(portmap_glock)
            arch.addPortMap(portmap_core)

        for arbiter in self.system.getAllArbiters():
            portmap_arbiter = vhdlNetworkGenerator.PortMap('inst_'+arbiter.getName(), arbiter.getRtlEntity())

            mem = arbiter.getMemory()

            for i,port in enumerate(mem.getRtlIfaceSuffix()):
                signal = vhdlNetworkGenerator.RtlSignal('w_'+arbiter.getName()+'_'+mem.getName()+'_'+port, mem.getRtlIfaceTypes()[i])
                arch.addSignal(signal)

            prefix = 'w_'+arbiter.getName()+'_'+mem.getName()
            mapping = vhdlNetworkGenerator.RtlMapping(arch.findSignalById(prefix+'_mem_en_x'),arbiter.getRtlEntity().find('ram_en_x'))
            portmap_arbiter.addPortMapping(mapping)
            mapping = vhdlNetworkGenerator.RtlMapping(arch.findSignalById(prefix + '_wr_en_x'),arbiter.getRtlEntity().find('ram_wr_x'))
            portmap_arbiter.addPortMapping(mapping)
            mapping = vhdlNetworkGenerator.RtlMapping(arch.findSignalById(prefix + '_wr_mask_x'),arbiter.getRtlEntity().find('ram_bit_wr_x'))
            portmap_arbiter.addPortMapping(mapping)
            mapping = vhdlNetworkGenerator.RtlMapping(arch.findSignalById(prefix + '_addr'),arbiter.getRtlEntity().find('ram_addr'))
            portmap_arbiter.addPortMapping(mapping)
            mapping = vhdlNetworkGenerator.RtlMapping(arch.findSignalById(prefix + '_data_out'),arbiter.getRtlEntity().find('ram_q'))
            portmap_arbiter.addPortMapping(mapping)
            mapping = vhdlNetworkGenerator.RtlMapping(arch.findSignalById(prefix + '_data_in'),arbiter.getRtlEntity().find('ram_d'))
            portmap_arbiter.addPortMapping(mapping)

            portmap_arbiter.addPortMapping(vhdlNetworkGenerator.RtlMapping(self.getEntity().find('clk'), arbiter.getRtlEntity().find('clk')))
            portmap_arbiter.addPortMapping(vhdlNetworkGenerator.RtlMapping(self.getEntity().find('rst_x'), arbiter.getRtlEntity().find('rst_n')))

            generic = vhdlNetworkGenerator.RtlGeneric('ports_g', 'integer', str(len(arbiter.getCoreConnections())))
            mapping = vhdlNetworkGenerator.RtlMapping(generic, arbiter.getRtlEntity().find('ports_g'))
            portmap_arbiter.addGenericMapping(mapping)
            generic = vhdlNetworkGenerator.RtlGeneric('addrw_g', 'integer', str(arbiter.getMemory().getAddrWidth()-2))
            mapping = vhdlNetworkGenerator.RtlMapping(generic, arbiter.getRtlEntity().find('addrw_g'))
            portmap_arbiter.addGenericMapping(mapping)
            generic = vhdlNetworkGenerator.RtlGeneric('dataw_g', 'integer', str(arbiter.getMemory().getWidth()*4))
            mapping = vhdlNetworkGenerator.RtlMapping(generic, arbiter.getRtlEntity().find('dataw_g'))
            portmap_arbiter.addGenericMapping(mapping)

            signalList = ['bit_wr_x','en_x','wr_x','d','addr','q','waitrequest']

            for s in signalList:
                signal = vhdlNetworkGenerator.RtlSignal('w_'+arbiter.getName()+'_'+s, arbiter.getRtlEntity().find(s).getType())
                signal.setType(arbiter.replaceVHDLaliases(signal.getType()))
                mapping = vhdlNetworkGenerator.RtlMapping(signal,  arbiter.getRtlEntity().find(s))
                arch.addSignal(signal)
                portmap_arbiter.addPortMapping(mapping)

            for i,core in enumerate(arbiter.getCoreConnections()):
                mapping = vhdlNetworkGenerator.RtlMapping(arch.findSignalById('w_'+arbiter.getName()+'_waitrequest'),arch.findSignalById('w_wait_rq_'+arbiter.getName()+'_'+core.getCoreId()))
                mapping.setSourceSel('('+str(i)+')')
                arch.addMapping(mapping)

                signalList = ['mem_en_x', 'wr_en_x', 'wr_mask_x', 'addr', 'data_in', 'data_out']

                dest = arch.findSignalById('w_'+core.getCoreId()+'_'+core.getLSUNameByMemName(mem)+'_mem_en_x')
                source = arch.findSignalById('w_'+arbiter.getName()+'_en_x')
                mapping = vhdlNetworkGenerator.RtlMapping(dest,source)
                mapping.setDestSel('('+ str(i) +')')
                arch.addMapping(mapping)

                dest = arch.findSignalById('w_'+core.getCoreId()+'_'+core.getLSUNameByMemName(mem)+'_wr_en_x')
                source = arch.findSignalById('w_'+arbiter.getName()+'_wr_x')
                mapping = vhdlNetworkGenerator.RtlMapping(dest,source)
                mapping.setDestSel('('+ str(i) +')')
                arch.addMapping(mapping)

                dataw = arbiter.getMemory().getWidth()*4
                dest = arch.findSignalById('w_'+core.getCoreId()+'_'+core.getLSUNameByMemName(mem)+'_wr_mask_x')
                source = arch.findSignalById('w_'+arbiter.getName()+'_bit_wr_x')
                mapping = vhdlNetworkGenerator.RtlMapping(dest,source)
                mapping.setDestSel('('+ str((i+1)*(arbiter.getMemory().getWidth()*4)-1) +' downto '+ str(i*dataw) +')')
                arch.addMapping(mapping)

                dest = arch.findSignalById('w_'+core.getCoreId()+'_'+core.getLSUNameByMemName(mem)+'_addr')
                source = arch.findSignalById('w_'+arbiter.getName()+'_addr')
                mapping = vhdlNetworkGenerator.RtlMapping(dest,source)
                addrw = arbiter.getMemory().getAddrWidth()-2
                mapping.setDestSel('('+ str((i+1)*(addrw)-1) +' downto '+ str(i*addrw) +')')
                arch.addMapping(mapping)

                dest = arch.findSignalById('w_'+core.getCoreId()+'_'+core.getLSUNameByMemName(mem)+'_data_out')
                source = arch.findSignalById('w_'+arbiter.getName()+'_d')
                mapping = vhdlNetworkGenerator.RtlMapping(dest,source)
                mapping.setDestSel('('+ str((i+1)*(dataw)-1) +' downto '+ str(i*dataw) +')')
                arch.addMapping(mapping)

                dest = arch.findSignalById('w_'+core.getCoreId()+'_'+core.getLSUNameByMemName(mem)+'_data_in')
                source = arch.findSignalById('w_'+arbiter.getName()+'_q')
                mapping = vhdlNetworkGenerator.RtlMapping(source,dest)
                mapping.setSourceSel('('+ str((i+1)*(dataw)-1) +' downto '+ str(i*dataw) +')')
                arch.addMapping(mapping)


            arch.addPortMap(portmap_arbiter)


        for mem in self.system.getCPSMems():

            portmap_mem = vhdlNetworkGenerator.PortMap('inst_'+mem.getName(), mem.getVhdlEntity())

            mapping = vhdlNetworkGenerator.RtlMapping(self.entity.find('clk'), mem.getVhdlEntity().find('clk'))
            portmap_mem.addPortMapping(mapping)


            for i,connection in enumerate(mem.getConnections()):
                if isinstance(connection, RuntimeMemory.Arbiter):
                    for suffix in mem.getRtlIfaceSuffix():
                        dest = mem.getVhdlEntity().find('p'+str(i)+'_'+suffix)
                        source = arch.findSignalById('w_'+connection.getName()+'_'+mem.getName()+'_'+suffix)
                        mapping = vhdlNetworkGenerator.RtlMapping(source,dest)
                        portmap_mem.addPortMapping(mapping)
                if isinstance(connection, RuntimeCore.RuntimeCoreTTA):
                    for suffix in mem.getRtlIfaceSuffix():
                        dest = mem.getVhdlEntity().find('p'+str(i)+'_'+suffix)
                        source = arch.findSignalById('w_'+connection.getCoreId()+'_'+connection.getLSUNameByMemName(mem) +'_'+suffix)
                        mapping = vhdlNetworkGenerator.RtlMapping(source,dest)
                        portmap_mem.addPortMapping(mapping)
                if isinstance(connection, RuntimeCore.RuntimeCoreX86):
                    for suffix in mem.getRtlIfaceSuffix():
                        dest = mem.getVhdlEntity().find('p'+str(i)+'_'+suffix)
                        source = self.entity.find(mem.getName()+'_'+connection.getCoreId()+'_p'+str(i)+'_'+suffix)
                        mapping = vhdlNetworkGenerator.RtlMapping(source,dest)
                        portmap_mem.addPortMapping(mapping)


            arch.addPortMap(portmap_mem)


        return arch