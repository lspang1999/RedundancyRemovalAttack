import argparse

parser = argparse.ArgumentParser("Making Atalanta happy")
parser.add_argument("input_file_name")
parser.add_argument("output_file_name")
args = parser.parse_args()
input_file = open(args.input_file_name, "r");
output_file = open(args.output_file_name, "w");
# grab first line to determine floating input to remove
# ASSUMPTION: file ends with "keyGate### with last number being digit under test
module = input_file.readline()
split_module = module.split("keyGate")
input_number = split_module[1][:-2]
# print(module)
floating_input = "keyInput" + input_number
# print(floating_input)
output_file.write(module)
for line in input_file:
	if floating_input + ')' not in line:
		output_file.write(line)
input_file.close()
output_file.close()
