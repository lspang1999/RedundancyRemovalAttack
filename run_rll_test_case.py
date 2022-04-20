import subprocess
import random

num_tests = 1

log_file = open('c6288_rll_tests.txt', 'w')
log_file.write('Recovered\tCorrect\n')
log_file.close()

key_size = 120

for i in range(0, num_tests):
	# input key and make keys.key file
	key = ''
	for j in range(0, key_size):
		key_bit = random.randint(0, 1)
		# key_bit = '1'
		key += str(key_bit)
	print(str(len(key)) + ' ' + key)
	with open('keys.key', 'w') as keyfile:
		keyfile.write(key)

	# make rll copy
	subprocess.run(['python3', 'logic_locking_parser-Copy.py', 'c6288.v', 'keys.key', 'c6288_rll_120.v'])

	# make directory
	subprocess.run(['mkdir', 'c6288_rll_120_test_circuits/'])

	# run redundancy attack
	subprocess.run(['python3', 'redundancy_removal_attack_main.py', 'c6288_rll_120.v', 'c6288_rll_120_test_circuits/', 'c6288', '120', '0', 'c6288_rll_120_key_guess.txt'])

	# generate keys.key into format for key comparison
	subprocess.run(['python3', 'make_key_file_from_binary.py'])

	# compare keys
	subprocess.run(['python3', 'compare_keys.py'])

	# cleanup
	# subprocess.run(['rm', '-r', 'c6288_rll_120_test_circuits/'])
	# subprocess.run(['rm', 'c6288_rll_120.v'])
	subprocess.run(['rm', 'keys.key'])
	# subprocess.run(['rm', 'c6288_rll_120.key'])
	# subprocess.run(['rm', 'c6288_rll_120_key_guess.txt'])
