import copy
import random
import pyverilog.vparser.ast as vast

def get_node_from_name(moddef, name):
    ilists = list(filter(lambda x: isinstance(x, vast.InstanceList), moddef.children()[5:]))
    return list(filter(lambda x: x.children()[0].name == name, ilists))[0]

def get_node_from_output(moddef, output_name):
    ilists = list(filter(lambda x: isinstance(x, vast.InstanceList), moddef.children()[5:]))
    return list(filter(lambda x: x.children()[0].children()[0].children()[0].name == output_name, ilists))[0]

def get_decl_names(moddef, cls):
    decl = [n for n in moddef.children() if len(n.children()) > 0 and isinstance(n.children()[0], cls)]
    names = [c for n in decl for c in n.children()]
    return names

def get_ilists(moddef):
    ilists = [n for n in moddef.children() if isinstance(n, vast.InstanceList)]
    return ilists

def get_ilist_names(moddef):
    ilists = [n for n in moddef.children() if isinstance(n, vast.InstanceList)]
    names = [get_ilist_name(n) for n in ilists]
    return names

def find_last_input(moddef):
    for index in range(2, len(moddef.children())):
        if isinstance(moddef.children()[index].children()[0], vast.Input) and not isinstance(moddef.children()[index + 1].children()[0], vast.Input):
            return index

    return -1

def create_key(moddef, key_name):
    portlist = moddef.children()[1]
    ports = list(portlist.ports)
    items = list(moddef.items)

    port = vast.Port(key_name, None, None, None)
    ports.append(port)

    last_input_index = find_last_input(moddef)
    # Not sure why it is -1, some difference between .items and .children()
    items.insert(last_input_index - 1, vast.Decl([vast.Input(key_name)]))

    portlist.ports = tuple(ports)
    moddef.items = tuple(items)

    return vast.Input(key_name)

def create_ilist(moddef, module, name, output, inputs, add_wire = True):
    wires = list(moddef.children()[4].list)
    items = list(moddef.items)

    out_port = vast.PortArg(None, vast.Identifier(output))
    in_ports = [vast.PortArg(None, vast.Identifier(name)) for name in inputs]

    portlist = (out_port, *in_ports)
    parameterlist = ()
    instance = vast.Instance(module, name, portlist, parameterlist)
    ilist = vast.InstanceList(module, (), (instance,))

    if add_wire:
        wires.append(vast.Wire(output))
    items.append(ilist)

    moddef.children()[4].list = tuple(wires)
    moddef.items = tuple(items)

    return ilist

def find_Y_candidate(moddef, randomize):
    if randomize:
        candidates = get_ilist_names(moddef)
    else:
        candidates = get_decl_names(moddef, vast.Output)

    return copy.deepcopy(random.choice(candidates))

def create_key_inputs(moddef, count):
    ports = list(moddef.children()[1].ports)
    inputs = list(moddef.children()[2].list)

    keys = [None] * count

    for index in range(count):
        name = "keyIn_0_%i" % (index)
        port = vast.Port(name, None, None, None)
        ports.append(port)

        keys[index] = vast.Input(name)
        inputs.append(keys[index])

    moddef.children()[1].ports = tuple(ports)
    moddef.children()[2].list = tuple(inputs)

    return keys

def get_ilist_name(ilist):
    return ilist.children()[0].children()[0].children()[0].name

def get_ilist_inputs(ilist):
    return [c.children()[0].name for c in ilist.children()[0].children()[1:]]

def verilog_zip(moddef, gate_type, signals1, signals2, name):
    gates = [None] * len(signals1)

    for i in range(len(signals1)):
        instance = "%s_%s_%i" % (name, gate_type, i)
        output = "%s_%s_output_%i" % (name, gate_type, i)
        gate = create_ilist(moddef, gate_type, instance, output, [signals1[i], signals2[i]])
        gates[i] = gate

    return gates