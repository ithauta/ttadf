from TTADF_Tools import *
from Network import *
import re


class TTADFParserElement:
    def __init__(self,pattern):
        self.pattern = pattern

    def setPattern(self,pattern):
        self.pattern = pattern

    def code(self, codeBlock, actor, stateVar, match):
        return codeBlock

    def parseFunctionInputParams(self,codeblock,start,nb_inputs):

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

        if(nb_inputs != len(inputParams)):
            return None , None

        return inputParams, start+charNo

    def search(self,codeBlock, actor, stateVar):

        match = re.search(self.pattern,codeBlock)
        while match:

            codeBlock = self.code(codeBlock, actor, stateVar, match)
            match = re.search(self.pattern, codeBlock)

        return codeBlock


    def getIndentation(self, codeblock, rewindpoint):
        point = rewindpoint - 1
        indent = ''
        while codeblock[point] != '\n':
            indent += codeblock[point]
            point -= 1

        return indent

class ParseTTADFGenerateStart(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'#PRAGMA\s*TTADF_GENERATE_START')

    def code(self,codeBlock, actor, stateVar,match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 3)

        iterator = inputargs[0]
        initVal = inputargs[1]
        toVal = inputargs[2]

        if not (inputargs):
            print('[ERROR] When parsing PRAGMA TTADF_GENERATE: could not find 3 input parameters!')
            exit()

        endMatch = re.search('#PRAGMA\s*TTADF_GENERATE_END', codeBlock[match.start():])

        if not endMatch:
            print("[ERROR] NOT FOUND TTADF_GENERATE_END")
            exit()

        network = actor.getNetwork()

        if not strIsInt(initVal):
            initVal = network.replaceWithDefines(initVal)
            if not strIsInt(initVal):
                initVal = actor.replaceWithActorGenerics(initVal)
                if not strIsInt(initVal):
                    print('[ERROR] PRAGMA TTADF_GENERATE invalid init value')
        if not strIsInt(toVal):
            toVal = network.replaceWithDefines(toVal)
            if not strIsInt(toVal):
                toVal = actor.replaceWithActorGenerics(toVal)
                if not strIsInt(toVal):
                    print('[ERROR] PRAGMA TTADF_GENERATE invalid stop value')

        generateBlock = codeBlock[end:endMatch.start() + match.start()]

        newContent = ''
        try:
            for i in range(int(initVal), int(toVal)):
                newContent += generateBlock.replace('<' + iterator + '>', str(i))
        except ValueError:
            print('[ERROR] PRAGMA TTADF_GENERATE invalid stop or value')
            exit()

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[endMatch.end() + match.start():]

        codeBlock = preContent + newContent + postContent

        return codeBlock


class ParseTTADFPortVar(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_VAR')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 3)

        #print(inputargs)
        fifo = None

        if not (inputargs):
            print('[ERROR] When parsing macro TTADF_PORT_VAR: Could not find 3 input parameters!')
            exit()
        else:
            portId = inputargs[0].strip('"')
            fifoVar = inputargs[1].strip()
            fifoType = inputargs[2].strip().strip('"')



        if portId in actor.outputs:
            fifo = actor.outputs[portId]
        elif portId in actor.inputs:
            fifo = actor.inputs[portId]

        if not fifo:
            print('[ERROR]: No fifos connected to the port "'+portId+'" of actor "' + actor.actorId +'" !')
            exit()

        appendVarFlag = True
        for index, var in enumerate(fifo.variableNames):
            if var == fifoVar:
                if fifo.variableOwner[index] == actor:
                    print("[WARNING]: actor " + actor.actorId + " port: " + portId + "has already variable name: " + fifoVar)
                    appendVarFlag = False

        if appendVarFlag:
            fifo.variableNames.append(fifoVar)
            fifo.variableTypes.append(fifoType)
            fifo.variableOwner.append(actor)

        core = actor.owner

        mem = fifo.owner

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        if core.arch == 'TTA':
            addrspace = mem.getAddressSpaceForCore(core)
            if stateVar:
                newContent = 'static ' +fifoType + ' SET_AS('+ str(addrspace) + ') * restrict ' + fifoVar
                #newContent += ';\nstatic ' + fifoType + ' SET_AS(' + str(addrspace) + ') * ttadf_temp_' + fifoVar
            else:
                newContent =  fifoType + ' SET_AS(' + str(addrspace) + ') * restrict ' + fifoVar
                #newContent += ';\n'+fifoType + ' SET_AS(' + str(addrspace) + ') * ttadf_temp_' + fifoVar
        elif core.arch == 'X86':
            if stateVar:
                newContent = 'static ' + fifoType + ' *  ' + fifoVar
                #newContent += ';\nstatic ' + fifoType + ' * ttadf_temp_' + fifoVar
            else:
                newContent = fifoType + ' *  ' + fifoVar
                #newContent += ';\n'+fifoType + ' * ttadf_temp_' + fifoVar

        codeBlock = preContent + newContent + postContent
        return codeBlock


class ParseTTADFPortVectorVar(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_VECTOR_VAR')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 4)

        #print(inputargs)
        fifo = None

        if not (inputargs):
            print('[ERROR] When parsing macro ' +self.pattern + 'Could not find 4 input parameters!')
            exit()
        else:
            portId = inputargs[0].strip('"')
            fifoVar = inputargs[1].strip()
            fifoType = inputargs[2].strip().strip('"')
            veclen = inputargs[3].strip()



        if portId in actor.outputs:
            fifo = actor.outputs[portId]
        elif portId in actor.inputs:
            fifo = actor.inputs[portId]

        if not fifo:
            print('[ERROR]: No fifos connected to the port "'+portId+'" of actor "' + actor.actorId +'" !')
            exit()

        appendVarFlag = True
        for index, var in enumerate(fifo.variableNames):
            if var == fifoVar:
                if fifo.variableOwner[index] == actor:
                    print("[WARNING]: actor " + actor.actorId + " port: " + portId + "has already variable name: " + fifoVar)
                    appendVarFlag = False

        if appendVarFlag:
            fifo.variableNames.append(fifoVar)
            fifo.variableTypes.append(fifoType)
            fifo.variableOwner.append(actor)

        core = actor.owner

        mem = fifo.owner

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        if core.arch == 'TTA':
            addrspace = mem.getAddressSpaceForCore(core)
            if stateVar:
                newContent = 'static ' +fifoType + ' SET_AS('+ str(addrspace) + ') * restrict ' + fifoVar + '['+veclen+']'
                #newContent += ';\nstatic ' + fifoType + ' SET_AS(' + str(addrspace) + ') * ttadf_temp_' + fifoVar
            else:
                newContent =  fifoType + ' SET_AS(' + str(addrspace) + ') * restrict ' + fifoVar + '['+veclen+']'
                #newContent += ';\n'+fifoType + ' SET_AS(' + str(addrspace) + ') * ttadf_temp_' + fifoVar
        elif core.arch == 'X86':
            if stateVar:
                newContent = 'static ' + fifoType + ' *  ' + fifoVar + '['+veclen+']'
                #newContent += ';\nstatic ' + fifoType + ' * ttadf_temp_' + fifoVar
            else:
                newContent = fifoType + ' *  ' + fifoVar + '['+veclen+']'
                #newContent += ';\n'+fifoType + ' * ttadf_temp_' + fifoVar

        codeBlock = preContent + newContent + postContent
        return codeBlock

class ParseTTADFPortWriteStart(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_WRITE_START')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 2)

        # print(inputargs)

        if not (inputargs):
            print(
                '[ERROR] When parsing macro TTADF_PORT_WRITE_START in "' + actor.actorId + '": Could not find 2 input parameters!')
            exit()
        else:
            portId = inputargs[0].strip('"')
            fifoVar = inputargs[1].strip()

        fifo = actor.outputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoWriteStart(stateVar, fifoVar, actor,
                                                   self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent
        return codeBlock


class ParseTTADFPortWriteEnd(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_WRITE_END')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 1)

        # print(inputargs)

        if not (inputargs):
            print('[ERROR] When parsing macro '+self.pattern+': Could not find input parameter!')
            exit()
        else:
            portId = inputargs[0].strip('"')

        fifo = actor.outputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoWriteEnd(stateVar, actor, self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent
        return codeBlock


class ParseTTADFPortReadStart(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_READ_START')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 2)

        # print(inputargs)

        if not (inputargs):
            print(
                '[ERROR] When parsing macro '+self.pattern+': "' + actor.actorId + '": Could not find 2 input parameters!')
            exit()
        else:
            portId = inputargs[0].strip('"')
            fifoVar = inputargs[1].strip()

        fifo = actor.inputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoReadStart(stateVar, fifoVar, actor,
                                                  self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent
        return codeBlock

class ParseTTADFPortPeek(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_PEEK')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 2)

        # print(inputargs)

        if not (inputargs):
            print(
                '[ERROR] When parsing macro '+self.pattern+': "' + actor.actorId + '": Could not find 2 input parameters!')
            exit()
        else:
            portId = inputargs[0].strip('"')
            fifoVar = inputargs[1].strip()

        fifo = actor.inputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoReadStart(stateVar, fifoVar, actor,
                                                  self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent
        return codeBlock

class ParseTTADFPortReadEnd(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_READ_END')

    def code(self, codeBlock, actor, stateVar, match):

        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 1)

        # print(inputargs)

        if not (inputargs):
            print('[ERROR] When parsing macro '+self.pattern+': Could not find input parameter!')
            exit()
        else:
            portId = inputargs[0].strip('"')

        fifo = actor.inputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoReadEnd(stateVar, actor, self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent

        return codeBlock


class ParseTTADFPortWriteNStart(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_MULTIRATE_WRITE_START')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 3)

        # print(inputargs)

        if not (inputargs):
            print('[ERROR] When parsing macro '+self.pattern+': Could not find 3 input parameters!')
            exit()
        else:
            portId = inputargs[0].strip('"')
            fifoVar = inputargs[1]
            nbBytes = inputargs[2]

        fifo = actor.outputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoWriteStartN(stateVar, fifoVar, actor, nbBytes,
                                                    self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent

        return codeBlock


class ParseTTADFPortWriteUpdate(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_WRITE_UPDATE')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 2)

        # print(inputargs)

        if not (inputargs):
            print('[ERROR] When parsing macro '+self.pattern+': Could not find input parameter!')
            exit()
        else:
            portId = inputargs[0].strip('"')
            fifoVar = inputargs[1]

        fifo = actor.outputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoWriteUpdate(stateVar, fifoVar, actor,
                                                    self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent
        return codeBlock

class ParseTTADFPortWriteNEnd(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_MULTIRATE_WRITE_END')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 1)

        # print(inputargs)

        if not (inputargs):
            print('[ERROR] When parsing macro '+self.pattern+': Could not find input parameter!')
            exit()
        else:
            portId = inputargs[0].strip('"')

        fifo = actor.outputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoWriteEndN(stateVar, actor, self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent
        return codeBlock

class ParseTTADFPortVectorWriteEnd(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_VECTOR_WRITE_END')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 1)

        # print(inputargs)

        if not (inputargs):
            print('[ERROR] When parsing macro '+self.pattern+': Could not find input parameter!')
            exit()
        else:
            portId = inputargs[0].strip('"')

        fifo = actor.outputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoWriteEndN(stateVar, actor, self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent
        return codeBlock

class ParseTTADFPortReadNStart(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_MULTIRATE_READ_START')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 3)

        # print(inputargs)

        if not (inputargs):
            print('[ERROR] When parsing macro '+self.pattern+': Could not find 3 input parameters!')
            exit()
        else:
            portId = inputargs[0].strip('"')
            fifoVar = inputargs[1]
            nbBytes = inputargs[2]

        fifo = actor.inputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoReadStartN(stateVar, fifoVar, actor, nbBytes,
                                                   self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent

        return codeBlock


class ParseTTADFPortReadNEnd(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_MULTIRATE_READ_END')



    def code(self, codeBlock, actor, stateVar, match):
        argc = 1
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), argc)
        # print(inputargs)

        if not (inputargs):
            print('[ERROR] When parsing macro '+self.pattern+': Could not find ' + argc + ' input parameters!')
            exit()
        else:
            portId = inputargs[0].strip('"')

        fifo = actor.inputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoReadEndN(stateVar, actor, self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent

        return codeBlock

class ParseTTADFPortVectorReadEnd(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_VECTOR_READ_END')



    def code(self, codeBlock, actor, stateVar, match):
        argc = 1
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), argc)
        # print(inputargs)

        if not (inputargs):
            print('[ERROR] When parsing macro '+self.pattern+': Could not find ' + argc + ' input parameters!')
            exit()
        else:
            portId = inputargs[0].strip('"')

        fifo = actor.inputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoReadEndN(stateVar, actor, self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent

        return codeBlock


class ParseTTADFPortReadUpdate(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_READ_UPDATE')

    def code(self, codeBlock, actor, stateVar, match):

        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 2)

        # print(inputargs)

        if not (inputargs):
            print('[ERROR] When parsing macro '+self.pattern+': Could not find input parameter!')
            exit()
        else:
            portId = inputargs[0].strip('"')
            fifoVar = inputargs[1]

        fifo = actor.inputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoReadUpdate(stateVar, fifoVar, actor,
                                                   self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent

        return codeBlock


class ParseTTADFPortVectorWriteStart(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self, 'TTADF_PORT_VECTOR_WRITE_START')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 3)

        # print(inputargs)

        if not (inputargs):
            print('[ERROR] When parsing macro ' + self.pattern + ': Could not find 3 input parameters!')
            exit()
        else:
            portId = inputargs[0].strip('"')
            fifoVar = inputargs[1]
            veclen = inputargs[2]

        fifo = actor.outputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoVectorWriteStart(stateVar, fifoVar, actor, veclen,
                                                    self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent

        return codeBlock

class ParseTTADFPortVectorReadStart(TTADFParserElement):
        def __init__(self):
            TTADFParserElement.__init__(self, 'TTADF_PORT_VECTOR_READ_START')

        def code(self, codeBlock, actor, stateVar, match):
            inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 3)

            # print(inputargs)

            if not (inputargs):
                print('[ERROR] When parsing macro ' + self.pattern + ': Could not find 3 input parameters!')
                exit()
            else:
                portId = inputargs[0].strip('"')
                fifoVar = inputargs[1]
                veclen = inputargs[2]

            fifo = actor.inputs[portId]

            preContent = codeBlock[:match.start()]
            postContent = codeBlock[end:]

            newContent = fifo.codeActionFifoVectorReadStart(stateVar, fifoVar, actor, veclen,
                                                             self.getIndentation(codeBlock, match.start()))

            codeBlock = preContent + newContent + postContent

            return codeBlock


#NON BLOCKING OPERATIONS



class ParseTTADFPortReadStartNonBlocking(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_NON_BLOCK_READ_START')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 2)

        # print(inputargs)

        if not (inputargs):
            print(
                '[ERROR] When parsing macro '+self.pattern+': "' + actor.actorId + '": Could not find 2 input parameters!')
            exit()
        else:
            portId = inputargs[0].strip('"')
            fifoVar = inputargs[1].strip()

        fifo = actor.inputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoReadStartNonBlocking(stateVar, fifoVar, actor,
                                                  self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent
        return codeBlock


class ParseTTADFPortReadEndNonBlocking(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_NON_BLOCK_READ_END')

    def code(self, codeBlock, actor, stateVar, match):

        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 1)

        # print(inputargs)

        if not (inputargs):
            print('[ERROR] When parsing macro '+self.pattern+': Could not find input parameter!')
            exit()
        else:
            portId = inputargs[0].strip('"')

        fifo = actor.inputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoReadEndNonBlocking(stateVar, actor, self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent

        return codeBlock


class ParseTTADFPortWriteStartNonBlocking(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_NON_BLOCK_WRITE_START')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 2)

        # print(inputargs)

        if not (inputargs):
            print(
                '[ERROR] When parsing macro '+self.pattern+': "' + actor.actorId + '": Could not find 2 input parameters!')
            exit()
        else:
            portId = inputargs[0].strip('"')
            fifoVar = inputargs[1].strip()

        fifo = actor.inputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoWriteStartNonBlocking(stateVar, fifoVar, actor,
                                                  self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent
        return codeBlock


class ParseTTADFPortWriteEndNonBlocking(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_NON_BLOCK_WRITE_END')

    def code(self, codeBlock, actor, stateVar, match):

        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 1)

        # print(inputargs)

        if not (inputargs):
            print('[ERROR] When parsing macro '+self.pattern+': Could not find input parameter!')
            exit()
        else:
            portId = inputargs[0].strip('"')

        fifo = actor.inputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        newContent = fifo.codeActionFifoWriteEndNonBlocking(stateVar, actor, self.getIndentation(codeBlock, match.start()))

        codeBlock = preContent + newContent + postContent

        return codeBlock




class ParseTTADFPortPopulation(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_POPULATION')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 1)

        if not (inputargs):
            print('[ERROR] When parsing macro '+self.pattern+': Could not find 1 input parameter!')
            exit()
        else:
            portId = inputargs[0].strip('"')

        try:
            fifo = actor.outputs[portId]
        except KeyError:
            fifo = actor.inputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]
        # newContent = stateVar + '->' + fifo.fifoId + "->population"

        newContent = fifo.codeActionFifoGetPopulation(stateVar, '')

        codeBlock = preContent + newContent + postContent

        return codeBlock


class ParseTTADFPortCapacity(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self,'TTADF_PORT_CAPACITY')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 1)

        if not (inputargs):
            print('[ERROR] When parsing macro '+self.pattern+': Could not find 1 input parameter!')
            exit()
        else:
            portId = inputargs[0].strip('"')

        try:
            fifo = actor.outputs[portId]
        except KeyError:
            fifo = actor.inputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]
        # newContent = stateVar + '->' + fifo.fifoId + "->population"

        newContent = fifo.codeActionFifoGetCapacity(stateVar, '')

        codeBlock = preContent + newContent + postContent

        return codeBlock


class ParseTTADFPortSetStopProduction(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self, 'TTADF_FIFO_SET_STOP_PRODUCTION')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 1)

        if not (inputargs):
            print('[ERROR] When parsing macro ' + self.pattern + ': Could not find 1 input parameter!')
            exit()
        else:
            portId = inputargs[0].strip('"')

        fifo = actor.outputs[portId]
        indent = self.getIndentation(codeBlock, match.start())

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]
        newContent = 'while(' + stateVar + '->' + fifo.fifoId + '->production_stopped == 0 ){\n'
        newContent += indent + '    ' + stateVar + '->' + fifo.fifoId + '->production_stopped = 1;\n'
        newContent += indent + '}\n'

        codeBlock = preContent + newContent + postContent

        return codeBlock


class ParseTTADFPortIsProductionStopped(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self, 'TTADF_FIFO_IS_PRODUCTION_STOPPED')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 1)

        if not (inputargs):
            print('[ERROR] When parsing macro ' + self.pattern + ': Could not find 1 input parameter!')
            exit()
        else:
            portId = inputargs[0].strip('"')

        try:
            fifo = actor.inputs[portId]
        except:
            print(
                '[ERROR] in API CALL "TTADF_FIFO_IS_PRODUCTION_STOPPED" in ' + actor.mainSourceFile + ', cannot not find port "' + portId + '".')
            exit()

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]
        newContent = stateVar + '->' + fifo.fifoId + "->production_stopped"

        codeBlock = preContent + newContent + postContent

        return codeBlock

class ParseTTADFPortSetStopConsuming(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self, 'TTADF_FIFO_SET_STOP_CONSUMING')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 1)

        if not (inputargs):
            print('[ERROR] When parsing macro ' + self.pattern + ': Could not find 1 input parameter!')
            exit()
        else:
            portId = inputargs[0].strip('"')

        core = actor.owner
        fifo = actor.inputs[portId]
        mem = fifo.owner
        addrspace = mem.getAddressSpaceForCore(core)

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]
        newContent = stateVar + '->' + fifo.fifoId + "->consuming_stopped = 1"

        codeBlock = preContent + newContent + postContent

        return codeBlock


class ParseTTADFPortIsConsumingStopped(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self, 'TTADF_FIFO_IS_CONSUMING_STOPPED')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 1)

        if not (inputargs):
            print('[ERROR] When parsing macro ' + self.pattern + ': Could not find 1 input parameter!')
            exit()
        else:
            portId = inputargs[0].strip('"')

        core = actor.owner
        fifo = actor.outputs[portId]
        mem = fifo.owner

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]
        newContent = stateVar + '->' + fifo.fifoId + "->consuming_stopped"

        codeBlock = preContent + newContent + postContent

        return codeBlock


class ParseTTADFGetPort(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self, 'TTADF_GET_PORT')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 1)

        if not (inputargs):
            print('[ERROR] When parsing macro ' + self.pattern + ': Could not find 1 input parameter!')
            exit()
        else:
            portId = inputargs[0].strip('"')

        try:
            fifo = actor.outputs[portId]
        except KeyError:
            fifo = actor.inputs[portId]

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]
        newContent = stateVar + '->' + fifo.fifoId

        codeBlock = preContent + newContent + postContent

        return codeBlock


class ParseTTADFStop(TTADFParserElement):
    def __init__(self):
        TTADFParserElement.__init__(self, 'TTADF_STOP')

    def code(self, codeBlock, actor, stateVar, match):
        inputargs, end = self.parseFunctionInputParams(codeBlock, match.end(), 1)


        if not(inputargs):
            print('[ERROR] When parsing macro ' + self.pattern + ': no input parameters!')
            exit()

        preContent = codeBlock[:match.start()]
        postContent = codeBlock[end:]

        indent = self.getIndentation(codeBlock, match.start())

        newContent = stateVar + '->ttadf_stop = 1;\n'

        if len(actor.outputs):
            for fifo in actor.outputs:
                newContent += indent + stateVar + '->' + actor.outputs[fifo].fifoId + '->production_stopped = 1;\n'

        if len(actor.inputs):
            for fifo in actor.inputs:
                newContent += indent + stateVar + '->' + actor.inputs[fifo].fifoId + '->consuming_stopped = 1;\n'
        newContent += indent + 'PT_EXIT(pt)'

        codeBlock = preContent + newContent + postContent

        return codeBlock


class TTADFParser:
    def __init__(self):
        self.defines = []

    def setDefines(self,defines):
        self.defines = defines


    def parseDirectives(self, actor):
        content = ""
        with open(actor.mainSourceFile, 'r') as content_sourcefile:
            content = content_sourcefile.read()

        content = comment_remover(content)

        match = re.search("\s*ACTORSTATE\s*" + actor.name + "\s*{", content)
        if (match):
            content = content[:match.start()]

            #content = content + '''\n#include "''' + actor.actorId + '''.h"'''

            #match = re.search("\s*"+actor.name+"_STATE\s*",content)

            #while (match):
            #    content = content[:match.start()] + actor.actorId+'_STATE '+ content[match.end():]
            #    match = re.search("\s*" + actor.name + "_STATE\s*", content)

            return content

        return None

    def parseHelperFunctions(self, actor):
        content = ""
        with open(actor.mainSourceFile, 'r') as content_sourcefile:
            content = content_sourcefile.read()

        content = comment_remover(content)

        match = re.search(
            "\sFINISH\s" + actor.name + "\s*\(\s*" + actor.name + "_STATE\s*\*\s*(.*?)\s*\)\s*{", content)
        if (match):
            curlBNb = 1
            stateVar = match.group(1)
            functionEnd = match.end()
            for char in content[match.end():]:
                functionEnd = functionEnd + 1
                if char == '{':
                    curlBNb = curlBNb + 1
                if char == '}':
                    curlBNb = curlBNb - 1
                if curlBNb == 0:
                    break

            content = content[functionEnd:]

            return content

        else:
            return None

    def parseStateStruct(self, actor):
        content = ""
        with open(actor.mainSourceFile, 'r') as content_sourcefile:
            content = content_sourcefile.read()

        content = comment_remover(content)

        match = re.search("\s*ACTORSTATE\s*" + actor.name + "\s*{", content)
        if (match):
            curlBNb = 1
            functionEnd = match.end()
            for char in content[match.end():]:
                functionEnd = functionEnd + 1
                if char == '{':
                    curlBNb = curlBNb + 1
                if char == '}':
                    curlBNb = curlBNb - 1
                if curlBNb == 0:
                    break

            redeclaration = 'typedef struct ' + actor.actorId + '_state_t{'
            structContent = redeclaration + content[match.end():functionEnd - 1]

            structContent = self.processMacros(structContent, actor, None)

            for port,inputFifo in actor.inputs.items():
                if not inputFifo:
                    print('[ERROR] Actor '+actor.actorId + ' input port "' + port +'" have not any fifo connection!\n' )
                    exit()
                core = actor.owner
                mem = inputFifo.owner


                if core.arch == 'TTA':
                    addrs = mem.getAddressSpaceForCore(core)
                    structContent += '   volatile p_fifo_as' + str(addrs) + ' ' + inputFifo.fifoId + ';\n'
                elif core.arch == 'X86':
                    structContent += '   volatile p_fifo ' + inputFifo.fifoId + ';\n'
                #structContent += '   uintptr_t ' + inputFifo.fifoId + '_write_no;\n'
                structContent += '   uintptr_t ' + inputFifo.fifoId + '_read_no;\n'


            for port,outputFifo in actor.outputs.items():
                core = actor.owner
                try:
                    mem = outputFifo.owner
                except AttributeError:
                    #print(outputFifo)
                    print('[ERROR] Actor ' +actor.actorId+' has unconnected port "'+ port +'"!')
                    #print(actor.outputs)
                    exit()

                if core.arch == 'TTA':
                    addrs = mem.getAddressSpaceForCore(core)
                    structContent += '   volatile p_fifo_as' + str(addrs) + ' ' + outputFifo.fifoId + ';\n'
                elif core.arch == 'X86':
                    structContent += '   volatile p_fifo ' + outputFifo.fifoId + ';\n'

                #structContent += '   uintptr_t ' + outputFifo.fifoId + '_write_no;\n'
                structContent += '   uintptr_t ' + outputFifo.fifoId + '_write_no;\n'


            structContent += '   int ttadf_nb_firings;\n'
            structContent += '   int ttadf_stop;\n'
            structContent += '   int ttadf_empty;\n'
            structContent += '   int ttadf_full;\n'
            structContent += '   unsigned int ttadf_id;\n'
            structContent += '   const char ttadf_actor_name['+str(len(actor.actorId)+1)+'];\n'
            structContent += '\n} ' + actor.actorId + '_STATE;\n'

            return structContent

        return None


    def parseInitFunction(self, actor):
        content = ""

        with open(actor.mainSourceFile, 'r') as content_sourcefile:
            content = content_sourcefile.read()

        content = comment_remover(content)

        match = re.search("\sINIT\s" + actor.name + "\s*\(\s*" + actor.name + "_STATE\s*\*\s*(.*?)\s*\)\s*{",
                          content)
        if (match):
            curlBNb = 1
            stateVar = match.group(1)
            functionEnd = match.end()
            for char in content[match.end():]:
                functionEnd = functionEnd + 1
                if char == '{':
                    curlBNb = curlBNb + 1
                if char == '}':
                    curlBNb = curlBNb - 1
                if curlBNb == 0:
                    break

            redeclaration = 'PT_THREAD(' + actor.actorId + '_INIT(struct pt *pt,' + actor.actorId + '_STATE * ' + stateVar + ')){\n'
            redeclaration += '    PT_BEGIN(pt);\n'

            fifoInitContent = ''

            fifoInitContent += '    static int ttadf_ok = 0;\n'

            for port,outputFifo in actor.outputs.items():
                core = actor.owner
                mem = outputFifo.owner

                if mem.type == "local":
                    fifoInitContent += '    ' + stateVar + '->' + outputFifo.fifoId + ' = (p_fifo) &' + outputFifo.fifoId + ';\n'
                    fifoInitContent += outputFifo.codeActionFifoInit(stateVar,'(uintptr_t) &'+outputFifo.fifoId+'_storage',core,'    ')

                else:
                    if core.arch == 'X86':
                        fifoInitContent += '    ' + stateVar + '->' + outputFifo.fifoId + ' = (volatile p_fifo) (' + outputFifo.fifoId.upper() +'_BASEADDR + ' +str(outputFifo.startAddr) + ');\n'
                    else:
                        addrs = mem.getAddressSpaceForCore(core)
                        fifoInitContent += '    ' + stateVar + '->' + outputFifo.fifoId + ' = (volatile p_fifo_as' + str(addrs) + ') ' + str(outputFifo.startAddr) + ';\n'
                    fifoInitContent += outputFifo.codeActionFifoInit(stateVar, str(outputFifo.startAddr + outputFifo.structSize), core, '    ')

            for port,inputFifo in actor.inputs.items():
                core = actor.owner
                mem = inputFifo.owner

                if mem.type == "local":
                    fifoInitContent = fifoInitContent + '    ' + stateVar + '->' + inputFifo.fifoId + ' = (p_fifo) &' + inputFifo.fifoId + ';\n'
                    fifoInitContent += inputFifo.codeActionFifoCheck(stateVar, str(inputFifo.capacity), str(inputFifo.tokenSizeInBytes), '(uintptr_t) &'+inputFifo.fifoId + '_storage','    ')
                else:
                    if core.arch == 'X86':
                        fifoInitContent += '    ' + stateVar + '->' + inputFifo.fifoId + ' = (volatile p_fifo) (' + inputFifo.fifoId.upper() +'_BASEADDR + ' + str(inputFifo.startAddr) + ');\n'
                    else:
                        addrs = mem.getAddressSpaceForCore(core)
                        fifoInitContent += '    ' + stateVar + '->' + inputFifo.fifoId + ' = (volatile p_fifo_as' + str(addrs) + ') ' + str(inputFifo.startAddr) + ';\n'
                    fifoInitContent += inputFifo.codeActionFifoCheck(stateVar, str(inputFifo.capacity), str(inputFifo.tokenSizeInBytes), str(inputFifo.startAddr + inputFifo.structSize), '    ')


            content = redeclaration + content[match.end():functionEnd - 1]


            content = content + 'PT_END(pt);\n}'

            content = self.processMacros(content,actor,stateVar)

            return content
        else:
            return None

    def parseFireFunction(self, actor):
        content = ""
        with open(actor.mainSourceFile, 'r') as content_sourcefile:
            content = content_sourcefile.read()

        content = comment_remover(content)

        # First find the FIRE function
        match = re.search("\sFIRE\s" + actor.name + "\s*\(\s*" + actor.name + "_STATE\s*\*\s*(.*?)\s*\)\s*{",
                          content)
        if (match):
            curlBNb = 1

            stateVar = match.group(1)

            functionEnd = match.end()
            for char in content[match.end():]:
                functionEnd = functionEnd + 1
                if char == '{':
                    curlBNb = curlBNb + 1
                if char == '}':
                    curlBNb = curlBNb - 1
                if curlBNb == 0:
                    break

            redeclaration = 'PT_THREAD(' + actor.actorId + '_FIRE(struct pt *pt,' + actor.actorId + '_STATE * ' + stateVar + ')){\n'
            redeclaration = redeclaration + '''    PT_BEGIN(pt);\n'''

            content = content[match.end():functionEnd-1] + '''    PT_END(pt);\n}\n'''
            fireF = redeclaration + content

            fireF = self.processMacros(fireF, actor, stateVar)


        else:
            print('[ERROR] No FIRE function for actor "'+ actor.actorId+'"')
            exit(0)

        return fireF

    def parseFinishFunction(self, actor):
        content = ""
        with open(actor.mainSourceFile, 'r') as content_sourcefile:
            content = content_sourcefile.read()
        content = comment_remover(content)

        match = re.search(
            "\sFINISH\s" + actor.name + "\s*\(\s*" + actor.name + "_STATE\s*\*\s*(.*?)\s*\)\s*{", content)
        if (match):
            curlBNb = 1
            stateVar = match.group(1)
            functionEnd = match.end()
            for char in content[match.end():]:
                functionEnd = functionEnd + 1
                if char == '{':
                    curlBNb = curlBNb + 1
                if char == '}':
                    curlBNb = curlBNb - 1
                if curlBNb == 0:
                    break

            redeclaration = 'int ' + actor.actorId + '_FINISH(' + actor.actorId + '_STATE * ' + stateVar + '){'
            content = redeclaration + content[match.end():functionEnd]

            content = self.processMacros(content, actor, stateVar)

            return content
        else:
            return None


    def parseOtherFunctions(self,actor):
        pass


    def processMacros(self, codeBlock, actor, stateVar):

        parserElemList = [ParseTTADFGenerateStart(),
                          ParseTTADFPortVar(),
                          ParseTTADFPortVectorVar(),
                          ParseTTADFPortWriteStart(),
                          ParseTTADFPortWriteEnd(),
                          ParseTTADFPortReadStart(),
                          ParseTTADFPortReadEnd(),
                          ParseTTADFPortWriteNStart(),
                          ParseTTADFPortWriteUpdate(),
                          ParseTTADFPortWriteNEnd(),
                          ParseTTADFPortReadNStart(),
                          ParseTTADFPortReadUpdate(),
                          ParseTTADFPortReadNEnd(),
                          ParseTTADFPortVectorReadStart(),
                          ParseTTADFPortVectorReadEnd(),
                          ParseTTADFPortVectorWriteStart(),
                          ParseTTADFPortVectorWriteEnd(),
                          ParseTTADFPortReadStartNonBlocking(),
                          ParseTTADFPortWriteStartNonBlocking(),
                          ParseTTADFPortReadEndNonBlocking(),
                          ParseTTADFPortWriteEndNonBlocking(),
                          ParseTTADFPortPopulation(),
                          ParseTTADFPortCapacity(),
                          ParseTTADFPortSetStopProduction(),
                          ParseTTADFPortSetStopConsuming(),
                          ParseTTADFPortIsConsumingStopped(),
                          ParseTTADFPortIsProductionStopped(),
                          ParseTTADFGetPort(),
                          ParseTTADFStop()
                          ]

        for parseelem in parserElemList:
            codeBlock = parseelem.search(codeBlock, actor, stateVar)

        return codeBlock


