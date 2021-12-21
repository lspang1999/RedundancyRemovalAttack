import argparse
import subprocess

# THE ONE SCRIPT TO RUN ALL OTHER SCRIPTS. ONE SCRIPT TO RULE THEM ALL

# Arguments
parser = argparse.ArgumentParser("Redundancy Attack Key Guessing Full Script")
parser.add_argument("locked_circuit")
parser.add_argument("output_path")
parser.add_argument("top_level_module")
parser.add_argument("num_keys")
parser.add_argument("min_faults")
args = parser.parse_args()

# TODO: Either edit generate_shorted_key_files with output manually, or add argument
subprocess.run(['python3','generate_shorted_key_files.py',args.locked_circuit, args.output_path, args.top_level_module])

# for each file, convert to bench
for i in range(0, int(args.num_keys)):
	for j in range(0, 2):
		input_file = args.output_path + args.top_level_module + "_" + "keyGate" + str(i) + '_' + str(j) + ".v"
		# print(input_file)
		output_file = args.output_path + args.top_level_module + "_" + "keyGate" + str(i) + str(j) + ".bench"
		subprocess.run(['python3','ver2bench.py',input_file, '-o', output_file])

# for each bench file, remove floating input
for i in range(0, int(args.num_keys)):
	for j in range(0, 2):
		input_file = args.output_path + args.top_level_module + "_" + "keyGate" + str(i) + str(j) + ".bench"
		output_file = args.output_path + args.top_level_module + "_" + "new_keyGate" + str(i) + str(j) + ".bench"
		subprocess.run(['python3', 'convert_for_atalanta.py', input_file, output_file])
		
# for each bench file, run atalanta
for i in range(0, int(args.num_keys)):
	for j in range(0, 2):
		bench_file = args.output_path + args.top_level_module + "_" + "new_keyGate" + str(i) + str(j) + ".bench"
		subprocess.run(['atalanta', '-v', bench_file])
# run key guessing

first_key_file = args.top_level_module + "_" + "new_keyGate00.ufaults"
subprocess.call(['python3', 'redundancy_key_guessing.py', args.min_faults, args.num_keys, first_key_file])


