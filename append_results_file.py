import os
import re
import argparse
from operator import itemgetter
import copy
import numpy as np
np.set_printoptions(formatter={'int':hex})



def parse_command_line():
    parser = argparse.ArgumentParser("Parse parsed log files")
    parser.add_argument('-l', '--result_log',    action='store',  required=True,  help="Output result log file")
    parser.add_argument('-f', '--attack_log',   action='store',   required=True, help="Input attack log file")
    return parser.parse_args()

args = parse_command_line()

if os.path.exists(args.result_log):
    append_write = 'a' # append if already exists
else:
    append_write = 'w' # make a new file if not

with open(args.result_log, append_write) as result_file:
    with open(args.attack_log, 'r') as attack_log:
        for line in attack_log:
            if "Number of needed guesses calculated" in line or "Found correct key, guess count:" in line:
                # Trim test trace number
                path, filename = os.path.split(args.attack_log)
                remove, keep = filename.split("_samples_",1)
                keep, remove = keep.split("_traces_", 1)
                num_traces = keep
                
                num_guesses = ""
                # Trim test result
                if "Number of needed guesses calculated = " in line:
                    remove, num_guesses = line.split("Number of needed guesses calculated = ", 1)
                else:
                    remove, num_guesses = line.split("Found correct key, guess count: ", 1)

                result_str = num_traces.ljust(5) + " traces = " + num_guesses
                result_file.write(result_str)
                
