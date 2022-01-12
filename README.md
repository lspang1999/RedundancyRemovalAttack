# MastersWork
Python files for redundancy removal attack

PREREQS: Atalanta, PyVerilog

TO RUN:
Run redundancy_removal_attack_main.py from a terminal. Include the following options. All are required.
  - locked_circuit: The file name of the locked circuit to run the attack on
  - output_path: Output directory to place genereated test copies of circuit in. InuNCLUDE BACKSLASH AT THE END OF PATH
  - top_level_module: Top level module name of locked circuit
  - num_keys: The number of keys in locked design
  - min_faults: If you have access to an unlocked oracle, run through Atalanta and report the number of redundant faults in design. If unknown, set this option to 0
 
 Note: The Atalanta log files generated during key guessing will be placed in working directory
 
 c880a_rll_19.v is included as a test to run through the attack. The corresponding key is also included to check accuracy. The attack should identify 7 keys correctly with this example.

