import math

from TTADF_Tools import isPowerOf2

class RuntimeFifo:
    def __init__(self, fifoId, name="unnamed", tokenSizeInBytes=8, capacity=1, target=None, source=None):
        self.fifoId = fifoId
        self.name = name
        self.tokenSizeInBytes = tokenSizeInBytes
        self.capacity = capacity
        self.target = target
        self.target_port_id = None
        self.source = source
        self.source_port_id = None
        self.startAddr = 0
        self.endAddr = 0
        self.structSize = 128
        self.owner = None
        self.variableNames = []
        self.variableTypes = []
        self.variableOwner = []
        self.tokenAddresses = [] #if fifo capacity is  <= 8 this is used




    def getPayloadStartAddr(self):
        return self.getStartAddr()+self.getStructSize()

    def getCapacity(self):
        return self.capacity

    def getStructSize(self):
        return self.structSize

    def getFifoVarTypeByName(self,variableName,actor):

        for index, fifovar in enumerate(self.variableNames):
            if fifovar == variableName and self.variableOwner[index] == actor:
                return self.variableTypes[index]


        if '->' in variableName:

            print('[INFO] PORTVAR "' + variableName + '" not found in actor "'+actor.actorId+'" trying using '+variableName.split('->')[1])
            variableName = variableName.split('->')[1]
            for index, fifovar in enumerate(self.variableNames):
                if fifovar == variableName and self.variableOwner[index] == actor:
                    return self.variableTypes[index]


        print('[ERROR] PORTVAR "' + variableName + '" not found in actor "'+actor.actorId+'"')
        print('        Following variables defined:')
        for index, fifovar in enumerate(self.variableNames):
            if self.variableOwner[index] == actor:
                print('\t\t'+str(index)+': var "'+fifovar +'", type "'+str(self.variableTypes[index])+'"')
        exit(0)

    def codeActionFifoCheck(self,statevar,capacity,tokensize,storageaddr,indent):
        fifo = statevar + '->' + self.fifoId


        codeblock = indent +  'PT_WAIT_UNTIL(pt, '+fifo+'->capacity == '+capacity+');\n'
        codeblock += indent + '#ifndef TTADF_BENCHMARK\n'
        codeblock += indent + 'printf("' + self.fifoId + ' capacity: OK!\\n");\n'
        codeblock += indent + '#endif\n'
        codeblock += indent + 'PT_WAIT_UNTIL(pt, (unsigned int)'+fifo+'->buffer_start == (unsigned int)'+storageaddr+');\n'
        codeblock += indent + '#ifndef TTADF_BENCHMARK\n'
        codeblock += indent + 'printf("' + self.fifoId + ' buffer_start: OK!\\n");\n'
        codeblock += indent + '#endif\n'
        codeblock += indent + 'PT_WAIT_UNTIL(pt, '+fifo+'->consuming_stopped == 0 ); \n'
        codeblock += indent + '#ifndef TTADF_BENCHMARK\n'
        codeblock += indent + 'printf("' + self.fifoId + ' consuming_stopped: OK!\\n");\n'
        codeblock += indent + '#endif\n'
        codeblock += indent + 'PT_WAIT_UNTIL(pt, '+fifo+'->production_stopped == 0 );\n'
        codeblock += indent + '#ifndef TTADF_BENCHMARK\n'
        codeblock += indent + 'printf("' + self.fifoId + ' production_stopped: OK!\\n");\n'
        codeblock += indent + '#endif\n'
        codeblock += indent + 'PT_WAIT_UNTIL(pt, ' + fifo + '->write_item_no == 0 );\n'
        codeblock += indent + '#ifndef TTADF_BENCHMARK\n'
        codeblock += indent + 'printf("' + self.fifoId + ' write item: OK!\\n");\n'
        codeblock += indent + '#endif\n'
        codeblock += indent + 'PT_WAIT_UNTIL(pt, ' + fifo + '->read_item_no == 13 );\n'
        codeblock += indent + '#ifndef TTADF_BENCHMARK\n'
        codeblock += indent + 'printf("' + self.fifoId + ' read item: OK!\\n");\n'
        codeblock += indent + '#endif\n'
        #codeblock += self.compilerBarrier(indent,self.target.owner.getArch())+ ';\n'
        codeblock += indent +  fifo + '->read_item_no = 0;\n'
        codeblock += self.compilerBarrier(indent,self.target.owner.getArch())+ ';\n'
        codeblock += indent + fifo + '->starving = 13131313;\n'
        codeblock += indent + '#ifndef TTADF_BENCHMARK\n'
        codeblock += indent + 'printf("'+self.fifoId+' check: ALL OK!\\n");\n'
        codeblock += indent + '#endif\n'

        return codeblock

    def getStartAddr(self):
        return self.startAddr

    def getMifInit(self):
        address = self.getStartAddr()
        c = ''
        c += format(address,'04x') + ' : ' + format(self.capacity,'032b') + '; -- '+self.fifoId+' fifo capacity\n'
        address += 4;
        c += format(address,'04x') + ' : ' + format(self.getStartAddr()+self.getStructSize(), '032b') + '; -- '+self.fifoId+' buffer_start\n'
        address += 4;
        c += format(address, '04x') + ' : ' + format(0,'032b') + '; -- '+self.fifoId+' pad0\n'
        address += 4;
        c += format(address, '04x') + ' : ' + format(self.getStartAddr()+self.getStructSize()+self.capacity*self.tokenSizeInBytes,'032b') + '; -- '+self.fifoId+' buffer_end\n'
        address += 4;
        c += format(address, '04x') + ' : ' + format(0,'032b') + '; -- '+self.fifoId+' pad1\n'
        address += 4;
        c += format(address, '04x') + ' : ' + format(0,'032b') + '; -- '+self.fifoId+' read_item_no\n'
        address += 4;
        c += format(address, '04x') + ' : ' + format(0,'032b') + '; -- '+self.fifoId+' pad2\n'
        address += 4;
        c += format(address, '04x') + ' : ' + format(0,'032b') + '; -- '+self.fifoId+' write_item_no\n'
        address += 4;
        c += format(address, '04x') + ' : ' + format(0,'032b') + '; -- '+self.fifoId+' pad3\n'
        address += 4;
        c += format(address, '04x') + ' : ' + format(0,'032b') + '; -- '+self.fifoId+' consuming_stopped\n'
        address += 4;
        c += format(address, '04x') + ' : ' + format(0,'032b') + '; -- '+self.fifoId+' production_stopped\n'
        address += 4;
        c += format(address, '04x') + ' : ' + format(0,'032b') + '; -- '+self.fifoId+' rd_overflow\n'
        address += 4;
        c += format(address, '04x') + ' : ' + format(0,'032b') + '; -- '+self.fifoId+' wr_overflow\n'
        address += 4;
        c += format(address, '04x') + ' : ' + format(0,'032b') + '; -- '+self.fifoId+' starving\n'
        address += 4;
        c += format(address, '04x') + ' : ' + format(0,'032b') + '; -- '+self.fifoId+' full\n'
        return c

    def getMTIInit(self):
        address = self.getStartAddr()/4
        c = ''
        c += format(address,'d') + ': ' + format(self.capacity,'08x') +'\n'
        address += 1;
        c += format(address,'d') + ': ' + format(self.getStartAddr()+self.getStructSize(), '08x') + '\n'
        address += 1;
        c += format(address, 'd') + ': ' + format(0,'08x') + '\n'
        address += 1;
        c += format(address, 'd') + ': ' + format(self.getStartAddr()+self.getStructSize()+self.capacity*self.tokenSizeInBytes,'08x') +'\n'
        address += 1;
        c += format(address, 'd') + ': ' + format(0,'08x') + '\n'
        address += 1;
        c += format(address, 'd') + ': ' + format(0,'08x') + '\n'
        address += 1;
        c += format(address, 'd') + ': ' + format(0,'08x') + '\n'
        address += 1;
        c += format(address, 'd') + ': ' + format(0,'08x') + '\n'
        address += 1;
        c += format(address, 'd') + ': ' + format(0,'08x') + '\n'
        address += 1;
        c += format(address, 'd') + ': ' + format(0,'08x') + '\n'
        address += 1;
        c += format(address, 'd') + ': ' + format(0,'08x') + '\n'
        address += 1;
        c += format(address, 'd') + ': ' + format(0,'08x') + '\n'
        address += 1;
        c += format(address, 'd') + ': ' + format(0,'08x') + '\n'
        address += 1;
        c += format(address, 'd') + ': ' + format(0,'08x') + '\n'
        address += 1;
        c += format(address, 'd') + ': ' + format(0,'08x') + '\n'
        return c

    def codeActionFifoInit(self,statevar,storageaddr,core,indent):

        fifo = statevar +'->'+self.fifoId
        codeblock = ''
        codeblock += indent + '#ifndef TTADF_BENCHMARK\n'
        codeblock += indent + 'printf("' + self.fifoId + ' init START!\\n");\n'
        codeblock += indent + '#endif\n'
        if(core.isTTA()):
            codeblock += indent+fifo+'->pad0 = 0;\n'
            codeblock += indent + fifo + '->pad1 = 0;\n'
            codeblock += indent + fifo + '->pad2 = 0;\n'
            codeblock += indent + fifo + '->pad3 = 0;\n'

        #codeblock = self.codeActionMutexInit(statevar,indent)
        codeblock += indent +fifo+'->capacity = '+str(self.capacity)+';\n'
        #codeblock += indent +fifo+'''->token_size = '''+str(self.tokenSizeInBytes)+''';\n'''
        codeblock += indent +fifo+'->buffer_start = '+storageaddr+';\n'
        codeblock += indent +fifo+'->buffer_end = ('+fifo+'->buffer_start) + ('+str(self.capacity*self.tokenSizeInBytes)+');\n'
        codeblock += indent +fifo+'->consuming_stopped = 0;\n'
        codeblock += indent +fifo+'->production_stopped = 0;\n'
        codeblock += self.codeActionFifoReset(statevar,core,indent)
        #codeblock += self.compilerBarrier(indent,self.source.owner.getArch())+ ';\n'
        codeblock += indent + 'PT_WAIT_WHILE(pt, ' + fifo + '->read_item_no != 0);\n'
        #codeblock += self.compilerBarrier(indent,self.source.owner.getArch())+ ';\n'
        codeblock += indent + fifo + '->full = 13131313;\n'
        codeblock += indent + '#ifndef TTADF_BENCHMARK\n'
        codeblock += indent + 'printf("'+self.fifoId+' init OK!\\n");\n'
        codeblock += indent + '#endif\n'
        return codeblock

    def codeActionFifoStaticInit(self,storageaddr,core):
        codeblock = '{\n'
        if storageaddr == None:
            storageaddr = str(self.startAddr+self.structSize)

        if(core.isTTA()):
            codeblock += '\t.pad0 = 0,\n'
            codeblock += '\t.pad1 = 0,\n'
            codeblock += '\t.pad2 = 0,\n'
            codeblock += '\t.pad3 = 0,\n'

        codeblock += '\t.capacity = '+str(self.capacity)+',\n'
        codeblock += '\t.buffer_start = (uintptr_t) '+storageaddr+',\n'
        codeblock += '\t.buffer_end = 0,\n'
        codeblock += '\t.consuming_stopped = 0,\n'
        codeblock += '\t.production_stopped = 0,\n'
        codeblock += '\t.write_item_no = 0,\n'
        codeblock += '\t.read_item_no = 0,\n'
        codeblock += '\t.rd_overflow = 0,\n'
        codeblock += '\t.wr_overflow = 0,\n'
        codeblock += '\t.full = 0\n'
        codeblock += '}'
        return codeblock

    def codeActionFifoStaticInitPointer(self,storageaddr,core):
        codeblock = ''
        if(core.isTTA()):
            codeblock += '\t' + self.fifoId +'->pad0 = 0;\n'
            codeblock += '\t' + self.fifoId +'->pad1 = 0;\n'
            codeblock += '\t' + self.fifoId +'->pad2 = 0;\n'
            codeblock += '\t' + self.fifoId +'->pad3 = 0;\n'

        codeblock += '\t' + self.fifoId +'->capacity = '+str(self.capacity)+';\n'
        codeblock += '\t' + self.fifoId +'->buffer_start = '+storageaddr+';\n'
        codeblock += '\t' + self.fifoId +'->buffer_end = 0;\n'
        codeblock += '\t' + self.fifoId +'->consuming_stopped = 0;\n'
        codeblock += '\t' + self.fifoId +'->production_stopped = 0;\n'
        codeblock += '\t' + self.fifoId +'->write_item_no = 0;\n'
        codeblock += '\t' + self.fifoId +'->read_item_no = 13;\n'
        codeblock += '\t' + self.fifoId +'->rd_overflow = 0;\n'
        codeblock += '\t' + self.fifoId +'->wr_overflow = 0;\n'
        codeblock += '\t' + self.fifoId +'->full = 13131313;\n'
        return codeblock

    def codeActionFifoReset(self,statevar,core,indent):
        fifo = statevar + '->' + self.fifoId
        #codeblock = self.codeActionMutexLock(statevar,core,indent)
        #codeblock = indent +fifo+'''->write_pointer = '''+fifo+'''->buffer_start;\n'''
        #codeblock += indent +fifo+'''->read_pointer = '''+fifo+'''->buffer_start;\n'''
        #codeblock += indent +fifo+'''->population = 0;\n'''
        codeblock = indent +fifo+'->write_item_no = 0;\n'
        codeblock += indent + fifo + '->read_item_no = 13;\n'
        codeblock += indent +fifo+'->rd_overflow = 0;\n'
        codeblock += indent +fifo+ '->wr_overflow = 0;\n'
        #codeblock += self.codeActionMutexUnlock(statevar,core,indent)
        return codeblock


    def codeRWEnd(self,actor,pointer):
        if actor.owner.isTTA() and actor.owner.hasHwFifoExtensionWREnd():
            codeblock = '_TCE_TTADF_RW_END('+ pointer+','+str(self.tokenSizeInBytes)\
                        +','+ str(self.capacity*self.tokenSizeInBytes)+'UL,'+pointer+')'
        else:
            codeblock = pointer+' = ttadf_rw_end(' +pointer+',' + str(self.tokenSizeInBytes)\
                         + ',' + str(self.capacity * self.tokenSizeInBytes) + 'UL)'
        return codeblock

    def writeItemTemp(self,fifo):
        return '((' +fifo + '_write_no) & ~(1<<31UL))'

    def writeItem(self,fifo):
        return '((' +fifo + '->write_item_no) & ~(1<<31UL))'

    def readItemTemp(self, fifo):
        return '((' + fifo + '_read_no) & ~(1<<31UL))'

    def readItem(self, fifo):
        return '((' + fifo + '->read_item_no) & ~(1<<31UL))'

    def writeItemOpt(self,fifo):
        return '((' +fifo + '->write_item_no) & '+str(self.capacity*self.tokenSizeInBytes-1)+')'

    def readItemOpt(self, fifo):
        return '((' + fifo + '->read_item_no) & '+str(self.capacity*self.tokenSizeInBytes-1)+')'

    def getCodeOptCapacity(self,statevar):
        fifo = statevar + '->' + self.fifoId
        return '('+fifo+'->write_item_no-'+fifo+'->read_item_no)'


    def getNFirtsTokenAddress(self,n):
        firstTokenAddr = self.getStartAddr() + self.getStructSize()
        addrlist = []
        for i in range(n):
            addrlist.append(firstTokenAddr)
            firstTokenAddr += self.tokenSizeInBytes
            if i > self.capacity:
                firstTokenAddr = self.getStartAddr() + self.getStructSize()
        return addrlist



    def codeActionFifoWriteStartN(self,statevar,var,actor, repeat,indent):
        fifo = statevar + '->' + self.fifoId
        codeblock = '/* '+ self.fifoId+ ' token write operation*/\n'

        if actor.owner.arch == 'TTA':
            codeblock += indent + 'PT_WAIT_WHILE(pt,' + self.codeActionFifoGetPopulation(statevar, '')\
                         + '+(' + str(self.tokenSizeInBytes) + 'UL * '+repeat+') > '\
                         + str(self.capacity * self.tokenSizeInBytes) + 'UL  );\n'
            codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var,actor)\
                         + ' SET_AS(' + str(self.owner.getAddressSpaceForCore(actor.owner))\
                         + ') *) ((' + self.writeItem(fifo) +') + '+ fifo + '->buffer_start);\n'


        elif actor.owner.arch == 'X86':
            codeblock += indent + 'PT_WAIT_WHILE(pt,' + self.codeActionFifoGetPopulation(statevar, '')\
                         + '+(' + str(self.tokenSizeInBytes) + 'UL * '+repeat+') > '\
                         + str(self.capacity * self.tokenSizeInBytes) + 'UL  );\n'
            if self.owner.type == 'shared':
                codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var,actor)\
                             + '*) ((' + self.writeItem(fifo) + ') + '+ fifo\
                             + '->buffer_start +'+self.fifoId.upper()+'_BASEADDR);\n'
            else:
                codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var,actor)\
                             + '*) ((' +  self.writeItem(fifo)+ ') + '+ fifo + '->buffer_start)\n'

        # set temporary write_no
        codeblock += fifo + '_write_no  = ' + fifo + '->write_item_no'

        return codeblock

    def codeActionFifoWriteEndN(self,statevar,actor,indent):
        fifo = statevar + '->' + self.fifoId
        codeblock = '/* ' + self.fifoId + ' end write operation*/\n'
        codeblock += self.compilerBarrier(indent,actor.owner.getArch()) + ';\n'

        codeblock += indent + fifo + '->write_item_no = ' +fifo + '_write_no'

        #codeblock += indent + fifo + '->write_item_no =

        #if actor.owner.isTTA() and actor.owner.hasHwFifoExtensionWREnd():
            #codeblock += indent + '_TCE_TTADF_RW_END('+ fifo +'->write_item_no,'+str(self.tokenSizeInBytes)+'*'+repeat+','+ str(self.capacity*self.tokenSizeInBytes)+'UL,'+fifo +'->write_item_no)'
        #else:
            #codeblock += indent + fifo + '->write_item_no = ttadf_rw_end(' + fifo + '->write_item_no,' + str(
            #    self.tokenSizeInBytes) + '*'+repeat+',' + str(
            #    self.capacity * self.tokenSizeInBytes) + 'UL)'

        return codeblock

    def codeActionFifoReadStartN(self,statevar,var,actor,repeat,indent):
        fifo = statevar + '->' + self.fifoId
        codeblock = '/* '+ self.fifoId+ ' read operation*/\n'

        if actor.owner.arch == 'TTA':
            codeblock += indent + 'PT_WAIT_WHILE(pt,' + self.codeActionFifoGetPopulation(statevar, '')\
                         + '<' + str(self.tokenSizeInBytes) + 'UL * '+repeat+');\n'
            codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var,actor)\
                         + ' SET_AS(' + str(self.owner.getAddressSpaceForCore(actor.owner)) + ') *) ((' \
                         + self.readItem(fifo) +') + '+ fifo + '->buffer_start);\n'
        elif actor.owner.arch == 'X86':
            codeblock += indent + 'PT_WAIT_WHILE(pt,' + self.codeActionFifoGetPopulation(statevar, '') \
                         + '<' + str(self.tokenSizeInBytes) + 'UL * '+repeat+' );\n'
            if self.owner.type == 'shared':
                codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var, actor) + '*) ((' \
                             + self.readItem(fifo) + ') + ' + fifo + '->buffer_start +' \
                             + self.fifoId.upper() + '_BASEADDR);\n'
            else:
                codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var, actor) + '*) ((' \
                             + self.readItem(fifo) + ') + ' + fifo + '->buffer_start);\n'

        # set temporary write_no
        codeblock += indent + fifo + '_read_no  = ' + fifo + '->read_item_no'

        #codeblock += self.compilerBarrier(indent,actor.owner.getArch())
        return codeblock

    def codeActionFifoReadEndN(self,statevar,actor,indent):
        fifo = statevar + '->' + self.fifoId
        codeblock = '/* ' + self.fifoId + ' end read operation*/\n'
        codeblock += self.compilerBarrier(indent,actor.owner.getArch()) +';\n'

        codeblock += indent+ fifo + '->read_item_no = ' + fifo + '_read_no'
        #codeblock += indent + fifo + '->read_item_no %= ('+str(self.capacity*self.tokenSizeInBytes)+'U);\n '


        #if actor.owner.isTTA() and actor.owner.hasHwFifoExtensionWREnd():
        #    codeblock += indent + '_TCE_TTADF_RW_END('+ fifo +'->read_item_no,'+str(self.tokenSizeInBytes)+'*'+repeat+','+ str(self.capacity*self.tokenSizeInBytes)+'UL,'+fifo +'->read_item_no)'

        #else:
        #    codeblock += indent +fifo + '->read_item_no = ttadf_rw_end(' + fifo + '->read_item_no,' + str(
        #        self.tokenSizeInBytes) + '*'+repeat+',' + str(
        #        self.capacity * self.tokenSizeInBytes) + 'UL)'
        return codeblock


    def codeActionFifoWriteStart(self,statevar,var,actor, indent):
        fifo = statevar + '->' + self.fifoId
        codeblock = '/* '+ self.fifoId+ ' token write operation*/\n'

        if actor.owner.arch == 'TTA':
            bufferStart = fifo + '->buffer_start'

            codeblock += indent + 'PT_WAIT_WHILE(pt,' + self.codeActionFifoGetPopulation(statevar, '') + '+(' + str(self.tokenSizeInBytes) + 'UL) > ' + str(self.capacity * self.tokenSizeInBytes) + 'UL  );\n'
            codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var,actor) + ' SET_AS(' + str(self.owner.getAddressSpaceForCore(actor.owner)) + ') *) ((' + self.writeItem(fifo) +') + '+bufferStart+')'
        elif actor.owner.arch == 'X86':
            codeblock += indent + 'PT_WAIT_WHILE(pt,' + self.codeActionFifoGetPopulation(statevar, '') + '+(' + str(self.tokenSizeInBytes) + 'UL) > ' + str(self.capacity * self.tokenSizeInBytes) + 'UL  );\n'
            if self.owner.type == 'shared':
                codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var,actor) + '*) ((' + self.writeItem(fifo) + ') + '+ fifo + '->buffer_start +'+self.fifoId.upper()+'_BASEADDR);\n'
            else:
                codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var,actor) + '*) ((' +  self.writeItem(fifo)+ ') + '+ fifo + '->buffer_start)'

        return codeblock

    def codeActionFifoWriteEnd(self,statevar,actor,indent):
        fifo = statevar + '->' + self.fifoId
        codeblock = '/* ' + self.fifoId + ' end write operation*/\n'
        codeblock += self.compilerBarrier(indent,actor.owner.getArch()) + ';\n'


        if actor.owner.isTTA() and actor.owner.hasHwFifoExtensionWREnd():
            codeblock += indent + '_TCE_TTADF_RW_END('+ fifo +'->write_item_no,'+str(self.tokenSizeInBytes)+','+ str(self.capacity*self.tokenSizeInBytes)+'UL,'+fifo +'->write_item_no)'
        else:
            codeblock += indent + fifo + '->write_item_no = ttadf_rw_end(' + fifo + '->write_item_no,' + str(
                self.tokenSizeInBytes) + ',' + str(
                self.capacity * self.tokenSizeInBytes) + 'UL)'
        return codeblock

    def codeActionFifoReadStart(self,statevar,var,actor,indent):
        fifo = statevar + '->' + self.fifoId
        codeblock = '/* '+ self.fifoId+ ' read operation*/\n'

        if actor.owner.arch == 'TTA':
            bufferStart = fifo + '->buffer_start'
            codeblock += indent + 'PT_WAIT_WHILE(pt,' + self.codeActionFifoGetPopulation(statevar, '') + '<' + str(self.tokenSizeInBytes) + 'UL );\n'
            codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var,actor) + ' SET_AS(' + str(self.owner.getAddressSpaceForCore(actor.owner)) + ') *) ((' + self.readItem(fifo) +') + '+bufferStart+ ')'
        elif actor.owner.arch == 'X86':
            codeblock += indent + 'PT_WAIT_WHILE(pt,' + self.codeActionFifoGetPopulation(statevar, '') + '<' + str(self.tokenSizeInBytes) + 'UL );\n'
            if self.owner.type == 'shared':
                codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var, actor) + '*) ((' + self.readItem(fifo) + ') + ' + fifo + '->buffer_start +' + self.fifoId.upper() + '_BASEADDR);\n'
            else:
                codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var, actor) + '*) ((' + self.readItem(fifo) + ') + ' + fifo + '->buffer_start);\n'

        return codeblock

    def codeActionFifoReadEnd(self,statevar,actor,indent):
        fifo = statevar + '->' + self.fifoId
        codeblock = '/* ' + self.fifoId + ' end read operation*/\n'
        codeblock += self.compilerBarrier(indent,actor.owner.getArch()) +';\n'

        if actor.owner.isTTA() and actor.owner.hasHwFifoExtensionWREnd():
            codeblock += indent + '_TCE_TTADF_RW_END('+ fifo +'->read_item_no,'+str(self.tokenSizeInBytes)+','+ str(self.capacity*self.tokenSizeInBytes)+'UL,'+fifo +'->read_item_no)'
        else:
            codeblock += indent +fifo + '->read_item_no = ttadf_rw_end(' + fifo + '->read_item_no,' + str(
                self.tokenSizeInBytes) + ',' + str(
                self.capacity * self.tokenSizeInBytes) + 'UL)'

        return codeblock

    def codeActionFifoReadUpdate(self, statevar, var,actor, indent):
        fifo = statevar + '->' + self.fifoId
        codeblock = '/* ' + self.fifoId + ' end read operation*/\n'
        codeblock += self.compilerBarrier(indent, actor.owner.getArch()) + ';\n'

        readItem = fifo+'_read_no'

        if actor.owner.isTTA() and actor.owner.hasHwFifoExtensionWREnd():
            codeblock += indent + '_TCE_TTADF_RW_END(' + readItem + ',' + str(
                self.tokenSizeInBytes) + ',' + str(
                self.capacity * self.tokenSizeInBytes) + 'UL,' + readItem + ');\n'
        else:
            codeblock += indent + readItem + ' = ttadf_rw_end(' + readItem + ',' + str(
                self.tokenSizeInBytes) + ',' + str(
                self.capacity * self.tokenSizeInBytes) + 'UL);\n'
        if actor.owner.arch == 'TTA':
            bufferStart = fifo + '->buffer_start'
            codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var,actor) + ' SET_AS(' \
                         + str(self.owner.getAddressSpaceForCore(actor.owner)) + ') *) ((' + self.readItemTemp(fifo) \
                         +') + '+bufferStart+ ')'
        elif actor.owner.arch == 'X86':
            if self.owner.type == 'shared':
                codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var, actor) \
                             + '*) ((' + self.readItemTemp(fifo) + ') + ' + fifo + '->buffer_start +' \
                             + self.fifoId.upper() + '_BASEADDR);\n'
            else:
                codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var, actor) \
                             + '*) ((' + self.readItemTemp(fifo) + ') + ' + fifo + '->buffer_start);\n'
        return codeblock

    def codeActionFifoWriteUpdate(self, statevar, var, actor, indent):
        fifo = statevar + '->' + self.fifoId
        codeblock = '/* ' + self.fifoId + ' end write operation*/\n'
        codeblock += self.compilerBarrier(indent,actor.owner.getArch()) + ';\n'

        writeItem = fifo+'_write_no'

        if actor.owner.isTTA() and actor.owner.hasHwFifoExtensionWREnd():
            codeblock += indent + '_TCE_TTADF_RW_END('+ writeItem+','+str(self.tokenSizeInBytes)\
                         +','+ str(self.capacity*self.tokenSizeInBytes)+'UL,'+writeItem+');\n'
        else:
            codeblock += indent + writeItem + ' = ttadf_rw_end(' + writeItem + ',' + str(
                self.tokenSizeInBytes) + ',' + str(
                self.capacity * self.tokenSizeInBytes) + 'UL);'

        if actor.owner.arch == 'TTA':
            bufferStart = fifo + '->buffer_start'
            codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var,actor) \
                         + ' SET_AS(' + str(self.owner.getAddressSpaceForCore(actor.owner)) \
                         + ') *) ((' + self.writeItemTemp(fifo) +') + '+bufferStart+')'
        elif actor.owner.arch == 'X86':
            if self.owner.type == 'shared':
                codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var,actor) \
                             + '*) ((' + self.writeItemTemp(fifo) + ') + '\
                             + fifo + '->buffer_start +'+self.fifoId.upper()+'_BASEADDR);\n'
            else:
                codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var,actor) \
                             + '*) ((' +  self.writeItemTemp(fifo)+ ') + '+ fifo + '->buffer_start)'

        return codeblock


    def codeActionFifoVectorWriteStart(self,statevar,var,actor, repeat,indent):
        fifo = statevar + '->' + self.fifoId
        codeblock = '/* '+ self.fifoId+ ' token vector write operation*/\n'

        if actor.owner.arch == 'TTA':
            codeblock += indent + 'PT_WAIT_WHILE(pt,' + self.codeActionFifoGetPopulation(statevar, '')\
                         + '+(' + str(self.tokenSizeInBytes) + 'UL * '+repeat+') > '\
                         + str(self.capacity * self.tokenSizeInBytes) + 'UL  );\n'

            codeblock += indent + var + '[0] = (' + self.getFifoVarTypeByName(var,actor)\
                         + ' SET_AS(' + str(self.owner.getAddressSpaceForCore(actor.owner))\
                         + ') *) ((' + self.writeItem(fifo) +') + '+ fifo + '->buffer_start);\n'



        elif actor.owner.arch == 'X86':
            codeblock += indent + 'PT_WAIT_WHILE(pt,' + self.codeActionFifoGetPopulation(statevar, '')\
                         + '+(' + str(self.tokenSizeInBytes) + 'UL * '+repeat+') > '\
                         + str(self.capacity * self.tokenSizeInBytes) + 'UL  );\n'
            if self.owner.type == 'shared':
                codeblock += indent + var + '[0] = (' + self.getFifoVarTypeByName(var,actor)\
                             + '*) ((' + self.writeItem(fifo) + ') + '+ fifo\
                             + '->buffer_start +'+self.fifoId.upper()+'_BASEADDR);\n'
            else:
                codeblock += indent + var + '[0] = (' + self.getFifoVarTypeByName(var,actor)\
                             + '*) ((' +  self.writeItem(fifo)+ ') + '+ fifo + '->buffer_start)\n'

        # set temporary write_no
        codeblock += indent + fifo + '_write_no  = ' + fifo + '->write_item_no;\n'


        codeblock += indent + 'for(int ttadf_i=1 ; ttadf_i<'+repeat+'; ttadf_i++){\n'
        codeblock += indent + '    ' + self.codeRWEnd(actor,fifo+'_write_no')+';\n'
        if actor.owner.arch == 'TTA':
            bufferStart = fifo + '->buffer_start'
            codeblock += indent + '    ' + var + '[ttadf_i] = (' + self.getFifoVarTypeByName(var, actor) + ' SET_AS(' \
                         + str(self.owner.getAddressSpaceForCore(actor.owner)) + ') *) ((' + self.writeItemTemp(fifo) \
                         + ') + ' + bufferStart + ');\n'
            codeblock += indent + '}\n'
        codeblock += indent + self.codeRWEnd(actor, fifo + '_write_no')


        return codeblock


    def codeActionFifoVectorReadStart(self,statevar,var,actor, repeat,indent):
        fifo = statevar + '->' + self.fifoId
        codeblock = '/* '+ self.fifoId+ ' token vector read operation*/\n'

        if actor.owner.arch == 'TTA':
            codeblock += indent + 'PT_WAIT_WHILE(pt,' + self.codeActionFifoGetPopulation(statevar, '')\
                         + '<' + str(self.tokenSizeInBytes) + 'UL * '+repeat+');\n'
            codeblock += indent + var + '[0] = (' + self.getFifoVarTypeByName(var,actor)\
                         + ' SET_AS(' + str(self.owner.getAddressSpaceForCore(actor.owner)) + ') *) ((' \
                         + self.readItem(fifo) +') + '+ fifo + '->buffer_start);\n'
        elif actor.owner.arch == 'X86':
            codeblock += indent + 'PT_WAIT_WHILE(pt,' + self.codeActionFifoGetPopulation(statevar, '') \
                         + '<' + str(self.tokenSizeInBytes) + 'UL * '+repeat+' );\n'
            if self.owner.type == 'shared':
                codeblock += indent + var + '[0] = (' + self.getFifoVarTypeByName(var, actor) + '*) ((' \
                             + self.readItem(fifo) + ') + ' + fifo + '->buffer_start +' \
                             + self.fifoId.upper() + '_BASEADDR);\n'
            else:
                codeblock += indent + var + '[0] = (' + self.getFifoVarTypeByName(var, actor) + '*) ((' \
                             + self.readItem(fifo) + ') + ' + fifo + '->buffer_start);\n'

        # set temporary read_no
        codeblock += indent + fifo + '_read_no  = ' + fifo + '->read_item_no;\n'


        codeblock += indent + 'for(int ttadf_i=1 ; ttadf_i<'+repeat+'; ttadf_i++){\n'
        codeblock += indent + '    ' + self.codeRWEnd(actor,fifo+'_read_no')+';\n'
        if actor.owner.arch == 'TTA':
            bufferStart = fifo + '->buffer_start'
            codeblock += indent + '    ' + var + '[ttadf_i] = (' + self.getFifoVarTypeByName(var, actor) + ' SET_AS(' \
                         + str(self.owner.getAddressSpaceForCore(actor.owner)) + ') *) ((' + self.readItemTemp(fifo) \
                         + ') + ' + bufferStart + ');\n'
            codeblock += indent + '}\n'
        codeblock += indent + self.codeRWEnd(actor, fifo + '_read_no')


        return codeblock




    #START OF NON-BLOCKING METHODS
    def codeActionFifoWriteStartNonBlocking(self,statevar,var,actor, indent):
        fifo = statevar + '->' + self.fifoId
        codeblock = '/* '+ self.fifoId+ ' token write operation*/\n'

        condition = 'if(' + self.codeActionFifoGetPopulation(statevar, '') + '+(' + str(self.tokenSizeInBytes) + 'UL) > ' + str(self.capacity * self.tokenSizeInBytes) + 'UL  ){\n'
        if actor.owner.arch == 'TTA':
            codeblock += indent + condition
            codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var,actor) + ' SET_AS(' + str(self.owner.getAddressSpaceForCore(actor.owner)) + ') *) ((' + self.writeItem(fifo) +') + '+ fifo + '->buffer_start)'
        elif actor.owner.arch == 'X86':
            codeblock += indent + condition
            if self.owner.type == 'shared':
                codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var,actor) + '*) ((' + self.writeItem(fifo) + ') + '+ fifo + '->buffer_start +'+self.fifoId.upper()+'_BASEADDR);\n'
            else:
                codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var,actor) + '*) ((' +  self.writeItem(fifo)+ ') + '+ fifo + '->buffer_start)'

        return codeblock

    def codeActionFifoWriteEndNonBlocking(self,statevar,actor,indent):
        fifo = statevar + '->' + self.fifoId
        codeblock = '/* ' + self.fifoId + ' end write operation*/\n'
        codeblock += self.compilerBarrier(indent,actor.owner.getArch()) + ';\n'

        if actor.owner.isTTA() and actor.owner.hasHwFifoExtensionWREnd():
            codeblock += indent + '_TCE_TTADF_RW_END('+ fifo +'->write_item_no,'+str(self.tokenSizeInBytes)+','+ str(self.capacity*self.tokenSizeInBytes)+'UL,'+fifo +'->write_item_no)'
        else:
            codeblock += indent + fifo + '->write_item_no = ttadf_rw_end(' + fifo + '->write_item_no,' + str(
                self.tokenSizeInBytes) + ',' + str(
                self.capacity * self.tokenSizeInBytes) + 'UL)'

        codeblock += '}\n'

        return codeblock

    def codeActionFifoReadStartNonBlocking(self,statevar,var,actor,indent):
        fifo = statevar + '->' + self.fifoId
        codeblock = '/* '+ self.fifoId+ ' read operation*/\n'

        if actor.owner.arch == 'TTA':
            codeblock += indent + 'if(' + self.codeActionFifoGetPopulation(statevar, '') + '>=' + str(self.tokenSizeInBytes) + 'UL ){;\n'
            codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var,actor) + ' SET_AS(' + str(self.owner.getAddressSpaceForCore(actor.owner)) + ') *) ((' + self.readItem(fifo) +') + '+ fifo + '->buffer_start)'
        elif actor.owner.arch == 'X86':
            codeblock += indent + 'if(' + self.codeActionFifoGetPopulation(statevar, '') + '>=' + str(self.tokenSizeInBytes) + 'UL ){\n'
            if self.owner.type == 'shared':
                codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var, actor) + '*) ((' + self.readItem(fifo) + ') + ' + fifo + '->buffer_start +' + self.fifoId.upper() + '_BASEADDR);\n'
            else:
                codeblock += indent + var + ' = (' + self.getFifoVarTypeByName(var, actor) + '*) ((' + self.readItem(fifo) + ') + ' + fifo + '->buffer_start);\n'

        return codeblock

    def codeActionFifoReadEndNonBlocking(self,statevar,actor,indent):
        fifo = statevar + '->' + self.fifoId
        codeblock = '/* ' + self.fifoId + ' end read operation*/\n'
        codeblock += self.compilerBarrier(indent,actor.owner.getArch()) +';\n'

        if actor.owner.isTTA() and actor.owner.hasHwFifoExtensionWREnd():
            codeblock += indent + '_TCE_TTADF_RW_END('+ fifo +'->read_item_no,'+str(self.tokenSizeInBytes)+','+ str(self.capacity*self.tokenSizeInBytes)+'UL,'+fifo +'->read_item_no)'

        else:
            codeblock += indent +fifo + '->read_item_no = ttadf_rw_end(' + fifo + '->read_item_no,' + str(
                self.tokenSizeInBytes) + ',' + str(
                self.capacity * self.tokenSizeInBytes) + 'UL);'

        codeblock += '}\n'
        return codeblock

    # END OF NON-BLOCKING METHODS

    def codeActionFifoGetPopulation(self,statevar,indent):
        codeblock = indent
        fifo = statevar + '->' + self.fifoId

        #codeblock += 'ttadf_get_population('+fifo+'->write_item_no,'+fifo+'->wr_overflow,'+fifo+'->read_item_no,'+fifo+'->rd_overflow,'+str(self.capacity*self.tokenSizeInBytes)+'U)'
        codeblock += 'ttadf_get_population(' + fifo + '->write_item_no,' + fifo + '->read_item_no,' + str(self.capacity * self.tokenSizeInBytes) + 'U)'
        #codeblock += '(unsigned int)((' + fifo + '->write_item_no -' + fifo + '->read_item_no ))'

        return codeblock

    def codeActionFifoGetCapacity(self,statevar,indent):
        codeblock = indent
        fifo = statevar + '->' + self.fifoId
        codeblock += str(self.capacity)

        return codeblock

    def codeActionFifoGetPopulationTTAHWExtensionsWrite(self,statevar,indent):
        codeblock = ''
        fifo = statevar + '->' + self.fifoId
        codeblock += indent + 'unsigned int ttadf_population_wr_'+self.fifoId+';\n'
        codeblock += indent + '_TCE_TTADF_POPULATION(' + fifo + '->write_item_no,' + fifo + '->read_item_no,' + str(self.capacity * self.tokenSizeInBytes) + 'U, ttadf_population_wr_'+self.fifoId +');\n'
        codeblock += indent + 'PT_WAIT_WHILE(pt,ttadf_population_wr_'+self.fifoId + '+(' + str(self.tokenSizeInBytes) + 'UL) > ' + str(self.capacity * self.tokenSizeInBytes) + 'UL  );\n'
        return codeblock

    def codeActionFifoGetPopulationTTAHWExtensionsRead(self, statevar, indent):
        codeblock = ''
        fifo = statevar + '->' + self.fifoId
        codeblock += indent + 'unsigned int ttadf_population_rd_'+self.fifoId+';\n'
        codeblock += indent + '_TCE_TTADF_POPULATION(' + fifo + '->write_item_no,' + fifo + '->read_item_no,' + str(self.capacity * self.tokenSizeInBytes) + 'U, ttadf_population_rd_' + self.fifoId + ');\n'
        codeblock += indent + 'PT_WAIT_WHILE(pt,ttadf_population_rd_'+self.fifoId + '<' + str(self.tokenSizeInBytes) + 'UL );\n'
        return codeblock

    def codeActionFifoGetAS(self,actor,indent):
        codeblock = ''
        if actor.owner.arch == 'TTA':
            codeblock = indent + 'SET_AS(' + str(self.owner.getAddressSpaceForCore(actor.owner))+')'
        return codeblock

    def codeActionFifoGetASID(self,actor):
        if actor.owner.arch == 'TTA':
            return self.owner.getAddressSpaceForCore(actor.owner)
        return 0

    def codeActionFifoGetASNAME(self,actor):
        codeblock = ''
        if actor.owner.arch == 'TTA':
            codeblock = str(self.owner.name)
        return codeblock

    def compilerBarrier(self,indent,arch):
        codeblock = indent
        if arch == 'X86':
            codeblock += 'ttadf_compiler_barrier()'

        elif arch == 'TTA':
            codeblock += 'ttadf_compiler_barrier()'
        return codeblock


    def prinfInfo(self):
        print("\t\t\t FIFO: " + self.name + " (" + self.fifoId + ")")
        print("\t\t\t\t tokenSizeInBytes: " + str(self.tokenSizeInBytes))
        print("\t\t\t\t capacity: " + str(self.capacity))
        print("\t\t\t\t source: " + self.source.actorId)
        print("\t\t\t\t target: " + self.target.actorId)
        print("\t\t\t\t addrRange: " + str(self.startAddr) + " - " + str(self.endAddr))