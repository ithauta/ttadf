
from functools import reduce

from lxml import etree, objectify
from optparse import OptionParser
from subprocess import call, check_output
from shutil import copy2
import os
import re
from TTADF_Tools import *

class Network:
    def __init__(self, networkFilename):
        with open(networkFilename) as f:
            self.xml_network = f.read()

        self.network = objectify.fromstring(self.xml_network)
        self.defines = self.getDefines()
        self.checkXMLPragmas()
        self.network = objectify.fromstring(self.xml_network)

    def getDefines(self):
        return self.defines

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

        match = re.search('#PRAGMA\s*GENERATE',self.xml_network)
        while match:

            inputargs, end = self.parsePragmaParams(self.xml_network, match.end(), 3)

            iterator = inputargs[0]
            initVal = inputargs[1]
            toVal = inputargs[2]

            if not (inputargs):
                print('[ERROR] When parsing PRAGMA TTADF_GENERATE: could not find 3 input parameters!')
                exit()

            endMatch = re.search('#PRAGMA END GENERATE',self.xml_network[match.start():])

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


            generateBlock = self.xml_network[end:endMatch.start()+match.start()]

            newContent = ''
            for i in range(int(initVal),int(toVal)):
                newContent += generateBlock.replace('$'+iterator+'$',str(i))


            preContent = self.xml_network[:match.start()]
            postContent = self.xml_network[endMatch.end()+match.start():]

            self.xml_network = preContent + newContent + postContent
            match = re.search('#PRAGMA\s*GENERATE', self.xml_network)


    def replaceWithDefines(self,string):
        #print(string)
        for label,value in self.defines.items():
            string = string.replace(str(label),str(value))
        #print(string)
        return string


    def getDefines(self):
        defineDict = {}
        try:
            for define in self.network.define:
                defineDict[define.get("label")] = define
        except AttributeError:
            pass
        return defineDict

    def replaceWithDefines(self,string):
        #print(string)
        #print('-->')
        for label,value in self.defines.items():
            string = string.replace(str(label),str(value))
        #print(string)
        return string

    def getNetworkName(self):
        return self.network.get("name")

    def printActorData(self, actor):
        for self.child in actor.name:
            print("Name: " + self.child)

    def findActorById(self, actorId):
        for self.actor in self.network.actor:
            if self.actor.get("id") == actorId:
                return self.actor
        return None

    def findFifoById(self, fifoId):
        for self.fifo in self.network.fifo:
            if self.fifo.get("id") == fifoId:
                    return self.fifo
        return None