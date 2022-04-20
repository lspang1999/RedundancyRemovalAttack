import argparse

parser = argparse.ArgumentParser("Redundancy Attack Key Guessing")
parser.add_argument("min_redundant_faults")
parser.add_argument("num_keys")
parser.add_argument("first_key_file")
parser.add_argument("key_log_file")
args = parser.parse_args()

# ASSUMPTION: test files end in two digits, where the first digit is the keyGate number and the second digit is the value at test

key_file_start = args.first_key_file[0:len(args.first_key_file)-6]
print(key_file_start)

key_log_file = open(args.key_log_file, 'w')

for i in range(0, int(args.num_keys)):
	faults_0 = 0
	faults_1 = 0
	try:
		fault_0_file = open(key_file_start + str(i) + str(0) + ".log", "r");
	except:
		faults_0 = 0
	else:
		for line in fault_0_file:
			# redundant vs aborted fault
			if 'Number of identified redundant faults' in line:
				split_line = line.split(": ")
				# print(split_line)
				faults_0 = int(split_line[1][:-1])
		fault_0_file.close()
	try:
		fault_1_file = open(key_file_start + str(i) + str(1) + ".log", "r");
	except:
		faults_1 = 0
	else:
		for line in fault_1_file:
			if 'Number of identified redundant faults' in line:
				split_line = line.split(": ")
				# print(split_line)
				faults_1 = int(split_line[1][:-1])
		fault_1_file.close()

	# print("keyGate" + str(i) + " faults_0 = " + str(faults_0))
	# print("keyGate" + str(i) + " faults_1 = " + str(faults_1))
	# Compare number of redundant faults
	if faults_0 > int(args.min_redundant_faults) and faults_0 > faults_1:
		# print("keyGate" + str(i) + " = 1")
		key_log_file.write("keyGate" + str(i) + " = 1\n")
	if faults_1 > int(args.min_redundant_faults) and faults_1 > faults_0:
		# print("keyGate" + str(i) + " = 0")
		key_log_file.write("keyGate" + str(i) + " = 0\n")

key_log_file.close()
	
		
	
