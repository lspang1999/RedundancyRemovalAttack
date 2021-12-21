import argparse
import pyverilog.vparser.ast as vast
from pyverilog.vparser.parser import parse

from shared import *

def print_header(moddef):
    rslt = ""
    rslt += "# %s\n" % moddef.name
    rslt += "#\n"
    return rslt

def print_inputs(inputs):
    rslt = "\n"
    for i in inputs:
        rslt += "INPUT(%s)\n" % i.name
    return rslt

def print_outputs(outputs):
    rslt = "\n"
    for o in outputs:
        rslt += "OUTPUT(%s)\n" % o.name
    return rslt

def print_gates(moddef):
    rslt = "\n"
    for ilist in get_ilists(moddef):
        module = ilist.module
        # handle INV case
        if module == "INV":
            module = "NOT"
        output = get_ilist_name(ilist)
        inputs = get_ilist_inputs(ilist)
        rslt += "%s = %s(%s)\n" % (output, module, ", ".join(inputs))
    return rslt

def convert(verilog, output):
    ast, _ = parse([verilog], debug=False)
    moddef = ast.children()[0].children()[0]

    inputs = get_decl_names(moddef, vast.Input)
    outputs = get_decl_names(moddef, vast.Output)

    rslt = ""
    rslt += print_header(moddef)
    rslt += print_inputs(inputs)
    rslt += print_outputs(outputs)
    rslt += print_gates(moddef)

    if output is not None:
        with open(output, "w") as f:
            f.write(rslt)
    else:
        print(rslt)


def main():
    parser = argparse.ArgumentParser(description="Convert a verilog file to a .bench file")
    parser.add_argument("verilog", help="The verilog file")
    parser.add_argument("-o", "--output", help="The output .bench file. Otherwise it will print to the screen.")

    args = parser.parse_args()
    convert(args.verilog, args.output)

if __name__ == "__main__":
    main()