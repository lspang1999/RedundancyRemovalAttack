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

def main():
    INFO = "Verilog code parser"
    VERSION = pyverilog.__version__
    USAGE = "Usage: python example_parser.py file ..."

    argParser = argparse.ArgumentParser(description="Insert logic locking on selected circuit")
    argParser.add_argument("unlocked_filename", help="The unlocked benchmark file")
    argParser.add_argument("key_filename", help="The unlocked benchmark file")
    argParser.add_argument("locked_filename", help="The locked benchmark file")
    args = argParser.parse_args()
    filelist = [args.unlocked_filename]
    ast, directives = parse(filelist)

    #quick method to parse through the key
    def KeyParse(key_file):
        with open(key_file, "r") as keyStream:
            key = keyStream.readline()
            if(key):
                return key
        return None

    keys = KeyParse(args.key_filename)


    #first step is to go through all the nodes and select the proper ones for selection
    print(type(ast))
    gates = {}
    ports = []
    declarations = []
    #InstanceDict is a dict of the Instance objects with the names of the gate as the keys
    InstanceDict = {}
    #InstanceListDict is a dict of the InstanceList objects with the name of the gate as keys. Used for updated ModuleDef call
    InstanceListDict ={}

    #modifying this method to give gates, ports, declarations, and everything needed to recreate the original AST
    #allgates[name] = [outputName, inputName, inputName2, input3, ...]
    def getGates(astInst):
        allGates = {}
        c = astInst.children()
        #a mess of for loops to loop through all the children
        #printing types of variable was super helpful in understanding
        #Any ports (input or output) that are buses are named as following: bus[1] = bus 1
        #Since a " " character wouldn't appear normally in the name
        for SourceChild in c:
            if (isinstance(SourceChild, pyverilog.vparser.ast.Description)):
                #print("Description")
                DescChildren = SourceChild.children()
                for descChild in DescChildren:
                    if (isinstance(descChild, pyverilog.vparser.ast.ModuleDef)):
                        #print("ModuleDef ")
                        moduleName = descChild.name
                        ModuleDefChildren = descChild.children()
                        for instList in ModuleDefChildren :
                            #If child is a PortList
                            if isinstance(instList, pyverilog.vparser.ast.Portlist):
                                portListChildren = instList.children()
                                for portIO in portListChildren:
                                    print(type(portIO))
                                    if isinstance(portIO,pyverilog.vparser.ast.Port):
                                        ports.append(portIO)
                                #print(instList)
                                #print(type(instList))
                            # If child is a Decl
                            if isinstance(instList, pyverilog.vparser.ast.Decl):
                                declChildren = instList.children()
                                for declChild in declChildren:
                                    #print("Decl: ")
                                    #print(type(declChild))
                                    declarations.append(declChild)
                            if isinstance(instList, pyverilog.vparser.ast.Paramlist):
                                moduleParamList = instList
                                #paramListChildren = instList.children()
                                #print(paramListChildren)
                                #print(type(paramListChildren))
                            # If child is an Instance List
                            if isinstance(instList, pyverilog.vparser.ast.InstanceList):
                                print("InstanceList ")
                                print(instList.module)
                                Instances = instList.children()
                                for instListChild in Instances:
                                    if (isinstance(instListChild, pyverilog.vparser.ast.Instance)):
                                        #print("Instance child")
                                        #print("Instance portlist: ")
                                        #print(instListChild.portlist)
                                        #print(type(instListChild.portlist))
                                        #instListChild is an Instance object
                                        name = instListChild.name
                                        InstanceListDict[name] = instList
                                        InstanceDict[name] = instListChild
                                        output_inputs = []
                                        instChildren = instListChild.children()
                                        for instChild in instChildren:
                                            if (isinstance(instChild, pyverilog.vparser.ast.PortArg)):
                                                #print("PortArg: ")
                                                #print(type(instChild.argname))
                                                #rint(instChild.argname)
                                                PortArgChildren = instChild.children()
                                                for identifier in PortArgChildren:
                                                    if (isinstance(identifier, pyverilog.vparser.ast.Pointer)):
                                                        #must be a bus
                                                        tempName = ""
                                                        intconst = 0
                                                        for idents in identifier.children():
                                                            print("Pointer children")
                                                            print(type(idents))
                                                            if isinstance(idents, pyverilog.vparser.ast.Identifier):
                                                                tempName = idents.name
                                                            if isinstance(idents, pyverilog.vparser.ast.IntConst):
                                                                intconst = idents.value
                                                        output_inputs.append(tempName+" "+ str(intconst))
                                                    if (isinstance(identifier, pyverilog.vparser.ast.Identifier)):
                                                        #print("Identifier")
                                                        #print(identifier)
                                                        output_inputs.append(identifier.name)
                                        #print(name)
                                        #print(output_inputs)
                                        allGates[name] = output_inputs
        return allGates, moduleName, moduleParamList

    gateNodes, ModuleName, ModuleParamList = getGates(ast)
    #ast.show()
    #directives seem to be lines that do not pertain to the ast structure. Like timescale

    print(gateNodes)
    print(ModuleName)
    print(ModuleParamList)

    #random gate selection
    def random_selection(nodes, keys):
        numKeys = len(keys)
        print(numKeys)
        counter = 0
        keynodes = {}
        while counter < numKeys:
            temp = random.sample(list(nodes), 1)[0]
            """temp is a string somehow"""
            while keynodes.get(temp) != None:
                temp = random.sample(list(nodes), 1)[0]
            keynodes[temp] = nodes[temp]
            counter += 1
        return keynodes

    # randomly selects nodes not already in keynodes. Built to work with sll
    def random_selection_with_preselected_keynodes(nodes, num_keys, keynodes, selected_nodes):
        counter = 0
        print(num_keys)
        while counter < num_keys:
            temp = random.sample(list(nodes), 1)[0]
            """temp is a string somehow"""
            exit_loop = False
            while not exit_loop:
                for i in range(0, len(nodes[temp])):
                    if nodes[temp][i] not in selected_nodes:
                        if temp in keynodes.keys():
                            current_value = keynodes.pop(temp)
                            current_value.append(nodes[temp][i])
                            keynodes[temp] = current_value
                        else:
                            keynodes[temp] = [nodes[temp][i]]
                        selected_nodes.append(nodes[temp][i])
                        exit_loop = True
                        break  # break from for loop
                temp = random.sample(list(nodes), 1)[0]
            counter += 1
        return keynodes


    # method for getting fan in/fanout of nodes
    def getFanInfo(nodes):
        fanInfo = {}
        for name in nodes.keys():
            fanin = len(nodes[name]) - 1
            fanout = 0
            for val in nodes.values():
                if name in val:
                    fanout = fanout + 1
            fanInfo[name] = [fanin, fanout]
        return fanInfo

    #logic-cone based gate selection
    def logic_cone_selection(nodes, keys):
        numKeys = len(keys)
        """so the original algorithm does this with modules, but we are just going with one module for now"""
        maxFI = 1
        maxFO = 1
        keynodes = {}
        pIndex = {}
        #format of fanInfo is fanInfo[name] = [fanin, fanout]
        fanInfo = getFanInfo(nodes)
        for name in nodes.keys():
            io = nodes[name]
            fanout = fanInfo[name][1]
            fanin = fanInfo[name][0]
            if maxFI < fanin:
                maxFI = fanin
            if maxFO < fanout:
                maxFO = fanout
        for name in nodes.keys():
            pIndex[name] = 0.5 * fanInfo[name][0] / maxFI + 0.5 * fanInfo[name][1] / maxFO
        pIndexSorted = sorted(pIndex.items(), key=lambda kv: kv[1])
        print(type(pIndexSorted))
        pIndexSorted.reverse()
        #pIndexSorted = pIndex.sorted()
        counter = 0
        while len(keynodes) < numKeys:
            n = pIndexSorted.pop(counter)
            print(n)
            if n[0] not in keynodes.keys():
                keynodes[n[0]] = nodes[n[0]]
                counter=counter+1
        return keynodes

    # sll without use of ATPG: trying to force pairwise secure relationships
    def strong_logic_locking_selection(nodes, key_list):
        numKeys = len(key_list)
        counter = 0
        keynodes = {}
        selected_nodes = []  # list of nodes to ensure that nodes aren't repeated

        for name in nodes.keys():
            # find gate that has one non-input key gate (and is not already a key gate)
            if len(nodes[name]) > 2 and ("I" not in nodes[name][1] or "I" not in nodes[name][2]):
                # if both gate inputs are non circuit inputs, insert key gate on both
                if "I" not in nodes[name][1] and nodes[name][1] not in selected_nodes:
                    keynodes[name] = [nodes[name][1]]
                    selected_nodes.append(nodes[name][1])
                    counter += 1
                if "I" not in nodes[name][2] and counter < numKeys and nodes[name][2] not in selected_nodes:
                    if name in keynodes.keys():
                        current_value = keynodes.pop(name)
                        current_value.append(nodes[name][2])
                        keynodes[name] = current_value
                    else:
                        keynodes[name] = [nodes[name][2]]
                    counter += 1
                    selected_nodes.append(nodes[name][2])
                # insert key gate at output of selected gate unless a literal output
                if counter < numKeys and nodes[name][0] not in selected_nodes and "O" not in nodes[name][0]:
                    if name in keynodes.keys():
                        current_value = keynodes.pop(name)
                        current_value.append(nodes[name][0])
                        keynodes[name] = current_value
                    else:
                        keynodes[name] = [nodes[name][0]]
                    counter += 1
                    selected_nodes.append(nodes[name][0])
            if counter >= numKeys:
                break
        return keynodes

    # Done: Adapt method for multiple inputs
    # Done: Add adapted random selection if all ideal nodes have been selected
    # Done: Base literal inputs on inputted list of inputs, not by name
    # This is a copy I can make improvements to the method without breaking the old method
    def modified_strong_logic_locking(nodes, key_list):
        numKeys = len(key_list)
        counter = 0
        keynodes = {}
        selected_nodes = []  # list of nodes to ensure that nodes aren't repeated
        port_names = []  # keeps track of circuit input and output from parsed ports

        # populate port_names
        for port in ports:
            port_names.append(port.name)
        # print("Ports:")
        # print(port_names)

        for name in nodes.keys():
            # find gate that has one non-input key gate (and is not already a key gate)
            if len(nodes[name]) > 2:
                add_at_output = False
                add_at_input = False
                for i in range(1, len(nodes[name])):
                    # or conditions with add at input to indicates one input has already been added. Not a
                    # perfect fix for adding at all inputs of a chosen gate, but it catches more inputs that without
                    # the condition.
                    if (nodes[name][i] not in port_names and nodes[name][i] not in selected_nodes and counter < numKeys)\
                            or add_at_input:
                        if name in keynodes.keys():
                            current_value = keynodes.pop(name)
                            current_value.append(nodes[name][i])
                            keynodes[name] = current_value
                        else:
                            keynodes[name] = [nodes[name][i]]
                        counter += 1
                        selected_nodes.append(nodes[name][i])
                        # since a gate has been added to at least one input, allow addition at output
                        add_at_output = True
                    # if input is already on selected nodes, allow addition at other inputs
                    elif nodes[name][i] in selected_nodes:
                        add_at_input = True
                # add at output
                if nodes[name][0] not in selected_nodes and nodes[name][0] not in port_names and add_at_output \
                        and counter < numKeys:
                    if name in keynodes.keys():
                        current_value = keynodes.pop(name)
                        current_value.append(nodes[name][0])
                        keynodes[name] = current_value
                    else:
                        keynodes[name] = [nodes[name][0]]
                    counter += 1
                    selected_nodes.append(nodes[name][0])
            if counter >= numKeys:
                break
        # if counter hasn't reached numKeys, still need to place more key gates
        if counter < numKeys:
            keynodes = random_selection_with_preselected_keynodes(nodes, numKeys - counter, keynodes, selected_nodes)
            print("Random selection used")
        print("Number of keys:: " + str(numKeys))
        return keynodes

    #print(gateNodes.keys())
    RkeyNodes = random_selection(gateNodes, keys)
    print("Random Key nodes selected: ")
    print(RkeyNodes)

    # logicKeyNodes = logic_cone_selection(gateNodes, keys)
    # print("Logic cone based selection nodes selected:")
    # print(logicKeyNodes)

    # sllKeyNodes = strong_logic_locking_selection(gateNodes, keys)
    # print("Poor SLL based selection nodes selected:")
    # print(sllKeyNodes)

    # mod_sll_keynodes = modified_strong_logic_locking(gateNodes, keys)
    # print("Modified SLL nodes selected:")
    # print(mod_sll_keynodes)

    # separate method since sll creates list of nodes
    def sll_key_gate_addition():
        # create the new key input first, and add it to the Decl's and PortList
        print(ports)
        counter = 0
        keyList = list(keys)
        print(keyList)
        for selNodeName in RkeyNodes.keys():
            newSelGateOutput = None
            newSelGateInputs = []
            for i in range(0, len(RkeyNodes[selNodeName])):
                keyName = "keyInput" + str(counter)

                ports.append(vast.Port(keyName, None, None, None))
                newWireName = "keyWire" + str(counter)
                gateName = "keyGate" + str(counter)
                # create new key gate node
                oldInst = InstanceDict[selNodeName]
                oldSelGatePorts = gateNodes[selNodeName]
                oldSelGate = InstanceListDict[selNodeName]


                # pick wire from current gate's list of nodes to add keys to
                current_wire = RkeyNodes[selNodeName][i]

                # check if input
                is_input = oldSelGatePorts[0] != current_wire

                if is_input:
                    # if we have a space in the port name, then it's a bus
                    if " " not in current_wire:
                        if keyList[counter] == '0':
                            newInst = vast.Instance("xor", gateName, [vast.PortArg(None, vast.Identifier(newWireName)),
                                                                      vast.PortArg(None, vast.Identifier(current_wire)),
                                                                      vast.PortArg(None, vast.Identifier(keyName))], ())
                        else:
                            newInst = vast.Instance("xnor", gateName,
                                                    [vast.PortArg(None, vast.Identifier(newWireName)),
                                                     vast.PortArg(None, vast.Identifier(current_wire)),
                                                     vast.PortArg(None, vast.Identifier(keyName))], ())
                    else:
                        wirelist = current_wire.split()
                        intVal = wirelist[1]
                        outputName = wirelist[0]
                        # print("INT VAL: ")
                        # print(intVal)
                        if keyList[counter] == '0':
                            newInst = vast.Instance("xor", gateName, [
                                vast.PortArg(None, vast.Identifier(newWireName)),
                                vast.PortArg(None,
                                             vast.Pointer(vast.Identifier(outputName), vast.IntConst(int(intVal)))),
                                vast.PortArg(None, vast.Identifier(keyName))], ())
                        else:
                            newInst = vast.Instance("xnor", gateName, [
                                vast.PortArg(None, vast.Identifier(newWireName)),
                                vast.PortArg(None,
                                             vast.Pointer(vast.Identifier(outputName), vast.IntConst(int(intVal)))),
                                vast.PortArg(None, vast.Identifier(keyName))], ())

                    newSelGateInputs.append(newWireName)
                # add key gate if it's an output
                else:
                    # if we have a space in the port name, then it's a bus
                    if " " not in current_wire:
                        if keyList[counter] == '0':
                            newInst = vast.Instance("xor", gateName, [vast.PortArg(None, vast.Identifier(current_wire)),
                                                                      vast.PortArg(None, vast.Identifier(newWireName)),
                                                                      vast.PortArg(None, vast.Identifier(keyName))], ())
                        else:
                            newInst = vast.Instance("xnor", gateName, [vast.PortArg(None, vast.Identifier(current_wire)),
                                                                       vast.PortArg(None, vast.Identifier(newWireName)),
                                                                       vast.PortArg(None, vast.Identifier(keyName))], ())
                    else:
                        wirelist = current_wire.split()
                        intVal = wirelist[1]
                        outputName = wirelist[0]
                        # print("INT VAL: ")
                        # print(intVal)
                        if keyList[counter] == '0':
                            newInst = vast.Instance("xor", gateName, [
                                vast.PortArg(None, vast.Pointer(vast.Identifier(outputName), vast.IntConst(int(intVal)))),
                                vast.PortArg(None, vast.Identifier(newWireName)),
                                vast.PortArg(None, vast.Identifier(keyName))], ())
                        else:
                            newInst = vast.Instance("xnor", gateName, [
                                vast.PortArg(None, vast.Pointer(vast.Identifier(outputName), vast.IntConst(int(intVal)))),
                                vast.PortArg(None, vast.Identifier(newWireName)),
                                vast.PortArg(None, vast.Identifier(keyName))], ())

                    newSelGateOutput = newWireName
                #print(dir(newInst))
                # add new instances
                InstanceListDict[gateName] = vast.InstanceList(newInst.module, (), [newInst])
                # append to the declarations
                declarations.append(vast.Wire(newWireName))
                declarations.append(vast.Input(keyName))
                counter += 1

            # modify old gate by creating new gate based off of old one
            # for loop to array of vast.IOports to create the new PortList
            newSelGatePorts = []
            # check if there's a new gate output
            if newSelGateOutput is not None:
                newSelGatePorts.append(vast.PortArg(None, vast.Identifier(newSelGateOutput)))
            else:
                newSelGatePorts.append(vast.PortArg(None, vast.Identifier(oldSelGatePorts[0])))
            oldSelGatePorts.pop(0)  # remove output from oldSelGatePorts
            input_counter = 0
            for p in oldSelGatePorts:
                # some of these could be buses as well
                if p in RkeyNodes[selNodeName]:
                    #print(input_counter, p)
                    #print(newSelGateInputs)
                    newSelGatePorts.append(vast.PortArg(None, vast.Identifier(newSelGateInputs[input_counter])))
                    input_counter += 1
                else:
                    if " " not in p:
                        newSelGatePorts.append(vast.PortArg(None, vast.Identifier(p)))
                    else:
                        pList = p.split()
                        busInt = pList[1]
                        pName = pList[0]
                        newSelGatePorts.append(
                            vast.PortArg(None, vast.Pointer(vast.Identifier(pName), vast.IntConst(int(busInt)))))

            modifiedSelGate = vast.Instance(oldInst.module, selNodeName, newSelGatePorts, ())

            # now add the newKeyGate to InstanceListDict, and replace the old gate with new modified gate
            InstanceListDict.pop(selNodeName)
            InstanceListDict[selNodeName] = vast.InstanceList(modifiedSelGate.module, (), [modifiedSelGate])



        portList = vast.Portlist(ports)

        # New moduleDef and visit nodes
        newAST = vast.ModuleDef(ModuleName, ModuleParamList, portList,
                                [vast.Decl(declarations), *InstanceListDict.values()])
        return newAST

    # newAST = sll_key_gate_addition()
    # codegen = ASTCodeGenerator()
    # rslt = codegen.visit(newAST)
    # newAST.show()
    # with open(r'C:\Users\lspan\PycharmProjects\lockingSchemes\circuits\sample_locked.v', 'w') as fo:
    #     fo.write(rslt)



    for lineno, directive in directives:
        print('Line %d : %s' % (lineno, directive))

    #create the new key input first, and add it to the Decl's and PortList
    print(ports)
    counter=0
    keyList = list(keys)
    for selNodeName in RkeyNodes.keys():
        keyName = "keyInput"+str(counter)

        ports.append(vast.Port(keyName, None, None, None))
        newWireName = "keyWire"+str(counter)
        gateName = "keyGate"+str(counter)
        #create new key gate node
        oldInst = InstanceDict[selNodeName]
        oldSelGatePorts = RkeyNodes[selNodeName]
        oldSelGate = InstanceListDict[selNodeName]

        oldSelGateOutput = oldSelGatePorts.pop(0)
        #oldSelGatePorts should now have the output popped off
        #if we have a space in the port name, then it's a bus
        if " " not in oldSelGateOutput:
            if keyList[counter] == '0':
                newInst = vast.Instance("xor", gateName, [vast.PortArg(None, vast.Identifier(oldSelGateOutput)),
                                                          vast.PortArg(None, vast.Identifier(newWireName)),
                                                          vast.PortArg(None, vast.Identifier(keyName))], ())
            else:
                newInst = vast.Instance("xnor", gateName, [vast.PortArg(None, vast.Identifier(oldSelGateOutput)),
                                                           vast.PortArg(None, vast.Identifier(newWireName)),
                                                           vast.PortArg(None, vast.Identifier(keyName))], ())
        else:
            outputlist = oldSelGateOutput.split()
            intVal = outputlist[1]
            outputName = outputlist[0]
            #print("INT VAL: ")
            #print(intVal)
            if keyList[counter] == '0':
                newInst = vast.Instance("xor", gateName, [vast.PortArg(None, vast.Pointer(vast.Identifier(outputName), vast.IntConst(int(intVal)))),
                                                          vast.PortArg(None, vast.Identifier(newWireName)),
                                                          vast.PortArg(None, vast.Identifier(keyName))], ())
            else:
                newInst = vast.Instance("xnor", gateName, [vast.PortArg(None, vast.Pointer(vast.Identifier(outputName), vast.IntConst(int(intVal)))),
                                                           vast.PortArg(None, vast.Identifier(newWireName)),
                                                           vast.PortArg(None, vast.Identifier(keyName))], ())

        #modify old gate by creating new gate based off of old one
        #for loop to array of vast.IOports to create the new PortList
        newSelGatePorts = []
        newSelGatePorts.append(vast.PortArg(None, vast.Identifier(newWireName)))
        for p in oldSelGatePorts:
            #some of these could be buses as well
            if " " not in p:
                newSelGatePorts.append(vast.PortArg(None, vast.Identifier(p)))
            else:
                pList = p.split()
                busInt = pList[1]
                pName = pList[0]
                newSelGatePorts.append(vast.PortArg(None, vast.Pointer(vast.Identifier(pName), vast.IntConst(int(busInt)))))

        modifiedSelGate = vast.Instance(oldInst.module, selNodeName,newSelGatePorts, ())

        #now add the newKeyGate to InstanceListDict, and replace the old gate with new modified gate
        InstanceListDict[gateName] = vast.InstanceList(newInst.module, (), [newInst])
        InstanceListDict.pop(selNodeName)
        InstanceListDict[selNodeName] = vast.InstanceList(modifiedSelGate.module, (), [modifiedSelGate])
        #append to the declarations
        declarations.append(vast.Wire(newWireName))
        declarations.append(vast.Input(keyName))
        counter = counter+1

    portList = vast.Portlist(ports)

    #New moduleDef and visit nodes
    newAST = vast.ModuleDef(ModuleName, ModuleParamList, portList, [vast.Decl(declarations), *InstanceListDict.values()])
    codegen = ASTCodeGenerator()
    rslt = codegen.visit(newAST)
    # newAST.show()
    #print(rslt)
    #print(keyList)
    with open(args.locked_filename, 'w') as fo:
        fo.write(rslt)
    #Print the new verilog!


if __name__ == '__main__':
    main()
