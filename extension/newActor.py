#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Example of extensions template for inkscape

'''

import inkex       # Required
import simplestyle # will be needed here for styles support
import os          # here for alternative debug method only - so not usually required
# many other useful ones in extensions folder. E.g. simplepath, cubicsuperpath, ...

from math import cos, sin, radians

__version__ = '0.2'

inkex.localize()




def processPortList(ports):

    l = []
    for i in ports.split(';'):
        l.append(i.strip())

    return l

### Your main function subclasses the inkex.Effect class

class AddActor(inkex.Effect): # choose a better name
    
    def __init__(self):
        " define how the options are mapped from the inx file "
        inkex.Effect.__init__(self) # initialize the super class
        
        # Two ways to get debug info:
        # OR just use inkex.debug(string) instead...
        try:
            self.tty = open("/dev/tty", 'w')
        except:
            self.tty = open(os.devnull, 'w')  # '/dev/null' for POSIX, 'nul' for Windows.
            # print >>self.tty, "gears-dev " + __version__
            
        # Define your list of parameters defined in the .inx file
        self.OptionParser.add_option("", "--actorName",
                                     action="store", type="string",
                                     dest="actorName", default='actor',
                                     help="command line help")
        
        self.OptionParser.add_option("", "--actorId",
                                     action="store", type="string",
                                     dest="actorId", default='actorId',
                                     help="command line help")
        
        self.OptionParser.add_option("", "--sourcefile",
                                     action="store", type="string", 
                                     dest="sourcefile", default='actor.c',
                                     help="command line help")

        self.OptionParser.add_option("", "--stopNetwork",
                                     action="store", type="inkbool", 
                                     dest="stopNetwork", default=False,
                                     help="command line help")
                                     
        self.OptionParser.add_option("", "--inputPorts", # note no cli shortcut
                                     action="store", type="int",
                                     dest="inputPorts", default=0,
                                     help="command line help")

        self.OptionParser.add_option("", "--inputPortList",
                                     action="store", type="string",
                                     dest="inputPortList", default='i1,i2',
                                     help="Units this dialog is using")

        self.OptionParser.add_option("", "--outputPorts", # note no cli shortcut
                                     action="store", type="int",
                                     dest="outputPorts", default=0,
                                     help="command line help")

        self.OptionParser.add_option("", "--outputPortList",
                                     action="store", type="string",
                                     dest="outputPortList", default='o1,o2',
                                     help="Units this dialog is using")
       

        self.OptionParser.add_option("", "--accuracy", # note no cli shortcut
                                     action="store", type="int",
                                     dest="accuracy", default=0,
                                     help="command line help")

        # here so we can have tabs - but we do not use it directly - else error
        self.OptionParser.add_option("", "--active-tab",
                                     action="store", type="string",
                                     dest="active_tab", default='title', # use a legitmate default
                                     help="Active tab.")
        


### -------------------------------------------------------------------
### This is your main function and is called when the extension is run.
    
    def effect(self):
        actorname = self.options.actorName
        actorId = self.options.actorId
        sourcefile = self.options.sourcefile
        inputports = self.options.inputPorts
        inputportlist = self.options.inputPortList
        outputports = self.options.outputPorts
        outputportlist = self.options.outputPortList
        
        
        inputportlist = processPortList(inputportlist)
        outputportlist = processPortList(outputportlist)
        
        if len(inputportlist) is not inputports:
            inkex.errormsg(_("Number of input ports not match the input port name list."))
            inkex.errormsg(_(str(inputports)+" defined but "+str(len(inputportlist))+" has name!"))
            exit()
        
        if len(outputportlist) is not outputports:
            inkex.errormsg(_("Number of output ports not match the output port name list."))
            inkex.errormsg(_(str(outputports)+" defined but "+str(len(outputportlist))+" has name!"))
            exit()
        

        
        
        # This finds center of current view in inkscape
        t = 'translate(%s,%s)' % (self.view_center[0], self.view_center[1] )
        # Make a nice useful name
        g_attribs = { inkex.addNS('label','inkscape'): actorname,
                      'transform': t,
                      inkex.addNS('actorname','dataflow'): actorname}
        # add the group to the document's current layer
        topgroup = inkex.etree.SubElement(self.current_layer, 'g', g_attribs )
        
        # Create SVG Path under this top level group
        # define style using basic dictionary
        actor_style = { 'stroke':"#000000" , 'stroke-width': 2, 'fill':"#ffdd55" }
        # convert style into svg form (see import at top of file)
        actor_attribs = { 'style': simplestyle.formatStyle(actor_style),
         'id': actorId, 'width': "100" , 'height': "100" }
        # add path to scene
         
        
        x = 5
        y = -10
        for inputPort in inputportlist:
            port_style = { 'stroke':"#000000" , 'stroke-width': 1, 'fill':"#ffdd55" }
            port_attribs = { 'style': simplestyle.formatStyle(port_style),
             'id': inputPort, 'width': "10" , 'height': "10", 'x': str(x) , 'y': str(y)}
            portNode = inkex.etree.SubElement(topgroup, inkex.addNS('rect','svg'), port_attribs )
            
            x = x + 20
            
        y = 99
        x = 5
        for outputPort in outputportlist:
            port_style = { 'stroke':"#000000" , 'stroke-width': 1, 'fill':"#ffdd55" }
            port_attribs = { 'style': simplestyle.formatStyle(port_style),
             'id': outputPort, 'width': "10" , 'height': "10", 'x': str(x) , 'y': str(y)}
            portNode = inkex.etree.SubElement(topgroup, inkex.addNS('rect','svg'), port_attribs )
            
            x = x + 20
 
        
        actorNode = inkex.etree.SubElement(topgroup, inkex.addNS('rect','svg'), actor_attribs )

if __name__ == '__main__':
    e = AddActor()
    e.affect()

# Notes

