key = ""
with open('c6288_rll_120_synth/c6288_rll_120.key', 'r') as keyfile:
	key = keyfile.readline()
new_key_file = open('c6288_rll_120_synth.key', 'w')
for i in range(0, len(key)):
	new_key_file.write('keyGate' + str(i) + ' = ' + key[i] + '\n')
new_key_file.close()

