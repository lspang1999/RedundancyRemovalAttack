from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import argparse
import random
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
# the next line can be removed after installation

import pyverilog
from pyverilog.vparser.parser import parse
import pyverilog.vparser.ast as vast

parser = argparse.ArgumentParser("Create test circuits for circuit with a camo gate")
parser.add_argument("original_circuit")
args = parser.parse_args()

filename = args.original_circuit
filelist = [filename]
ast, directives = parse(filelist)

ports = []
portList = []
declarations = []
InstanceDict = {}
InstanceListDict = {}

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

# replace camo gate with and and or
for i in range(0, 2):
    new_instance_dict = {}
    for gate in gateNodes.keys():
        if InstanceListDict[gate].module == 'camo':
            if i == 0:
               # change gate type to and
               oldGatePorts = gateNodes[gate]
               newInst = vast.Instance("and", gate, [vast.PortArg(None, vast.Identifier(oldGatePorts[0])),
                                                                  vast.PortArg(None, vast.Identifier(oldGatePorts[1])),
                                                                  vast.PortArg(None, vast.Identifier(oldGatePorts[2]))], ())
               new_instance_dict[gate] = vast.InstanceList(newInst.module, (), [newInst])
            if i == 1:
                # change gate type to or
                oldGatePorts = gateNodes[gate]
                newInst = vast.Instance("or", gate, [vast.PortArg(None, vast.Identifier(oldGatePorts[0])),
                                                       vast.PortArg(None, vast.Identifier(oldGatePorts[1])),
                                                       vast.PortArg(None, vast.Identifier(oldGatePorts[2]))], ())
                new_instance_dict[gate] = vast.InstanceList(newInst.module, (), [newInst])
        else:
            new_instance_dict[gate] = InstanceListDict[gate]

    portList = vast.Portlist(ports)
    newAST = vast.ModuleDef(ModuleName, ModuleParamList, portList, [vast.Decl(declarations), *new_instance_dict.values()])
    codegen = ASTCodeGenerator()
    rslt = codegen.visit(newAST)
    # newAST.show()
    #print(rslt)
    output_file = args.original_circuit[:-2]
    if i == 0:
        output_file = output_file + '_and.v'
    else:
        output_file = output_file + '_or.v'
    with open(output_file, 'w') as fo:
        fo.write(rslt)
