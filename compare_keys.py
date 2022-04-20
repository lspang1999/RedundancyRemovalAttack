log_file = open('c6288_synth_rll_tests.txt', 'a')
guessed_keys = open('c6288_rll_120_high_key_guess.txt', 'r')
correct_keys = open('c6288_rll_120_synth.key', 'r')

num_correct = 0
num_recovered = 0
current_guess = guessed_keys.readline()
for line in correct_keys:
	if current_guess == line:
		num_correct += 1
		num_recovered += 1
		current_guess = guessed_keys.readline()
		# print(current_guess)
	elif str(current_guess[0:-5]) == str(line[0:-5]):
		# print(current_guess[0:-5] + line[0:-5])
		print(current_guess + line)
		num_recovered += 1
		current_guess = guessed_keys.readline()

print('Number of correct keys:: ' + str(num_correct))
print('Number of keys recovered:: ' + str(num_recovered))
log_file.write(str(num_recovered) + '\t' + str(num_correct) + '\n')
guessed_keys.close()
correct_keys.close()
log_file.close()
