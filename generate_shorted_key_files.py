from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import argparse
import random
import json
from optparse import OptionParser
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyverilog
from pyverilog.vparser.parser import parse
import pyverilog.vparser.ast as vast

filename = r'C:\\Users\\lspan\\PycharmProjects\\lockingSchemes\\circuits\\c432_rll_8_ver2.v'
filelist = [filename]
ast, directives = parse(filelist)

ports = []
portList = []
declarations = []
InstanceDict = {}
InstanceListDict ={}



def getGates(astInst):
    allGates = {}
    c = astInst.children()
    # a mess of for loops to loop through all the children
    # printing types of variable was super helpful in understanding
    # Any ports (input or output) that are buses are named as following: bus[1] = bus 1
    # Since a " " character wouldn't appear normally in the name
    for SourceChild in c:
        if (isinstance(SourceChild, pyverilog.vparser.ast.Description)):
            # print("Description")
            DescChildren = SourceChild.children()
            for descChild in DescChildren:
                if (isinstance(descChild, pyverilog.vparser.ast.ModuleDef)):
                    # print("ModuleDef ")
                    moduleName = descChild.name
                    ModuleDefChildren = descChild.children()
                    for instList in ModuleDefChildren:
                        # If child is a PortList
                        if isinstance(instList, pyverilog.vparser.ast.Portlist):
                            portListChildren = instList.children()
                            for portIO in portListChildren:
                                # print(type(portIO))
                                if isinstance(portIO, pyverilog.vparser.ast.Port):
                                    ports.append(portIO)
                            # print(instList)
                            # print(type(instList))
                        # If child is a Decl
                        if isinstance(instList, pyverilog.vparser.ast.Decl):
                            declChildren = instList.children()
                            for declChild in declChildren:
                                # print("Decl: ")
                                # print(type(declChild))
                                declarations.append(declChild)
                        if isinstance(instList, pyverilog.vparser.ast.Paramlist):
                            moduleParamList = instList
                            # paramListChildren = instList.children()
                            # print(paramListChildren)
                            # print(type(paramListChildren))
                        # If child is an Instance List
                        if isinstance(instList, pyverilog.vparser.ast.InstanceList):
                            # print("InstanceList ")
                            # print(instList.module)
                            Instances = instList.children()
                            for instListChild in Instances:
                                if (isinstance(instListChild, pyverilog.vparser.ast.Instance)):
                                    # print("Instance child")
                                    # print("Instance portlist: ")
                                    # print(instListChild.portlist)
                                    # print(type(instListChild.portlist))
                                    # instListChild is an Instance object
                                    name = instListChild.name
                                    InstanceListDict[name] = instList
                                    InstanceDict[name] = instListChild
                                    output_inputs = []
                                    instChildren = instListChild.children()
                                    for instChild in instChildren:
                                        if (isinstance(instChild, pyverilog.vparser.ast.PortArg)):
                                            # print("PortArg: ")
                                            # print(type(instChild.argname))
                                            # rint(instChild.argname)
                                            PortArgChildren = instChild.children()
                                            for identifier in PortArgChildren:
                                                if (isinstance(identifier, pyverilog.vparser.ast.Pointer)):
                                                    # must be a bus
                                                    tempName = ""
                                                    intconst = 0
                                                    for idents in identifier.children():
                                                        # print("Pointer children")
                                                        # print(type(idents))
                                                        if isinstance(idents, pyverilog.vparser.ast.Identifier):
                                                            tempName = idents.name
                                                        if isinstance(idents, pyverilog.vparser.ast.IntConst):
                                                            intconst = idents.value
                                                    output_inputs.append(tempName + " " + str(intconst))
                                                if (isinstance(identifier, pyverilog.vparser.ast.Identifier)):
                                                    # print("Identifier")
                                                    # print(identifier)
                                                    output_inputs.append(identifier.name)
                                    # print(name)
                                    # print(output_inputs)
                                    allGates[name] = output_inputs
    return allGates, moduleName, moduleParamList

gateNodes, ModuleName, ModuleParamList = getGates(ast)

# print("printing declarations")
# # check how to print declarations
# for node in declarations:
#     print(node.name)
# print(InstanceDict)

print(gateNodes)
key_gates = {}

# Loop through all gates and identify key gates
for gate in gateNodes:
    if "key" in gate.lower():
        key_gates[gate] = gateNodes[gate]

print(key_gates)

# for each key gate, make a copy where gate is replaced by buffer (testing key = 0)
# and a copy where gate is replaced by an inverter (testing key = 1)

for key_gate in key_gates.keys():
    for i in range(0, 2):
        new_instance_dict = {}
        if i == 0:
            # replace with buffer
            for gateName in gateNodes.keys():
                if gateName is key_gate:
                    oldSelGatePorts = gateNodes[gateName]
                    oldSelGate = InstanceListDict[gateName]
                    oldSelGateOutput = oldSelGatePorts[0]
                    newInst = oldSelGate # instantiate newInst to something to make Python compile
                    # make buffer instance with non key input as input
                    if " " not in oldSelGateOutput:
                        # output is a wire case
                        # determine which output is not the key input (also relies on naming conventions)
                        wireName = ""
                        if "keyInput" in oldSelGatePorts[1].lower():
                            wireName = oldSelGatePorts[2]
                        else:
                            wireName = oldSelGatePorts[1]
                        newInst = vast.Instance("BUF", gateName,
                                                [vast.PortArg(None, vast.Identifier(oldSelGateOutput)),
                                                 vast.PortArg(None, vast.Identifier(wireName))], ())

                        # remove key input from ports and declarations
                        # ports.remove(wireName)
                        # declarations.remove(wireName)

                    else:
                        # output is part of a bus case
                        outputlist = oldSelGateOutput.split()
                        intVal = outputlist[1]
                        outputName = outputlist[0]
                        # determine which output is not the key input (also relies on naming conventions)
                        wireName = ""
                        if "keyInput" in oldSelGatePorts[1].lower():
                            wireName = oldSelGatePorts[2]
                        else:
                            wireName = oldSelGatePorts[1]
                        newInst = vast.Instance("BUF", gateName, [vast.PortArg(None, vast.Pointer(
                        vast.Identifier(outputName), vast.IntConst(int(intVal)))),
                                                               vast.PortArg(None,
                                                                            vast.Identifier(wireName))], ())
                    new_instance_dict[gateName] = vast.InstanceList(newInst.module, (), [newInst])
                    # remove key input from ports and declarations
                    # ports.remove(wireName)
                    # declarations.remove(wireName)
                else:
                    # add gate back to AST
                    new_instance_dict[gateName] = InstanceListDict[gateName]
        else:
            # add inverter instead
            for gateName in gateNodes.keys():
                if gateName is key_gate:
                    oldSelGatePorts = gateNodes[gateName]
                    oldSelGate = InstanceListDict[gateName]
                    oldSelGateOutput = oldSelGatePorts[0]
                    newInst = oldSelGate # instantiate newInst to something to make Python compile
                    # make buffer instance with non key input as input
                    if " " not in oldSelGateOutput:
                        # output is a wire case
                        # determine which output is not the key input (also relies on naming conventions)
                        wireName = ""
                        if "keyInput" in oldSelGatePorts[1].lower():
                            wireName = oldSelGatePorts[2]
                        else:
                            wireName = oldSelGatePorts[1]
                        newInst = vast.Instance("INV", gateName,
                                                [vast.PortArg(None, vast.Identifier(oldSelGateOutput)),
                                                 vast.PortArg(None, vast.Identifier(wireName))], ())
                        # remove key input from ports and declarations
                        # ports.remove(wireName)
                        # declarations.remove(wireName)

                    else:
                        # output is part of a bus case
                        outputlist = oldSelGateOutput.split()
                        intVal = outputlist[1]
                        outputName = outputlist[0]
                        # determine which output is not the key input (also relies on naming conventions)
                        wireName = ""
                        if "keyInput" in oldSelGatePorts[1].lower():
                            wireName = oldSelGatePorts[2]
                        else:
                            wireName = oldSelGatePorts[1]
                        newInst = vast.Instance("INV", gateName, [vast.PortArg(None, vast.Pointer(
                        vast.Identifier(outputName), vast.IntConst(int(intVal)))),
                                                               vast.PortArg(None,
                                                                            vast.Identifier(wireName))], ())
                    new_instance_dict[gateName] = vast.InstanceList(newInst.module, (), [newInst])
                    # remove key input from ports and declarations
                    # ports.remove(wireName)
                    # declarations.remove(wireName)
                else:
                    # add gate back to AST
                    new_instance_dict[gateName] = InstanceListDict[gateName]
        # create new file
        print(ports)
        print(declarations)
        portList = vast.Portlist(ports)
        new_module_name = ModuleName + '_' + key_gate + str(i)
        newAST = vast.ModuleDef(new_module_name, ModuleParamList, portList,
                                [vast.Decl(declarations), *new_instance_dict.values()])
        codegen = ASTCodeGenerator()
        rslt = codegen.visit(newAST)
        # newAST.show()
        # print(node.name)
        file_name = key_gate + '_' + str(i)
        with open(
                r'C:\\Users\\lspan\\PycharmProjects\\lockingSchemes\\circuits\\c432_rll_8_ver2\\c432_rll_8' +
                file_name + '.v',
                'w') as fo:
            fo.write(rslt)
        fo.close()
