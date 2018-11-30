import os
import re
import argparse
from operator import itemgetter
import copy
import numpy as np
import matplotlib.pyplot as plt

np.set_printoptions(formatter={'int':hex})

class CorrelationValue:
  subKey = 0
  rank = 1 # one indexed
  candidate = 0x2b
  peak = 0.05
  relativePeak = 0.05
  sample = 500

def printCorrelationValue(x):
    print("subKey: {} rank: {} candiate: {} peak: {} relativePeak: {} ".format(x.subKey, x.rank, hex(x.candidate), x.peak, x.relativePeak))


def parse_command_line():
    parser = argparse.ArgumentParser("Parse Jlsca log files")
    parser.add_argument('-i', '--input',    action='store',         required=True,  help="Input log file")
    parser.add_argument('-k', '--key',      action='store',         required=True,  help="Knownkey file")
    parser.add_argument('-p', '--plot',     action='store',         required=True,  help="Plot sample points")
    #parser.add_argument('-c', '--clean',    action='store_true',                    help="Clean test folder")

    return parser.parse_args()

args = parse_command_line()

knownKey = np.load(args.key).tolist()
# Regex used to match relevant loglines (in this case, a specific IP address)
line_regex = re.compile(r"target.*")
line_start_results = re.compile(r"Results @ .* rows,")
line_start_target_info = re.compile(r"target:.\d+,.phase:")
line_start_rank_data = re.compile(r"rank:")
line_start_referencestart = re.compile(r"referencestart:.*")
line_start_referenceend = re.compile(r"referenceend:.*")
line_Start_maxshift = re.compile(r"maxShift:.*")
line_start_corvalmin = re.compile(r"corvalMin:.*")
# Output file, where the matched loglines will be copied to
# output_filename = os.path.normpath(args.output)
# with open(output_filename, "w") as out_file:
#    out_file.write("")


FFT_referencestart = 0
FFT_referenceend = 0
FFT_maxshift = 0
FFT_corvalmin = 0.0

dataSet = []


# Open input file in 'read' mode
subKeyNumber = 0
firstParse = True
subtractFromParsedSubKeyNumber = 0
with open(args.input, "r") as log_file:
    # Loop over each log line
    for line in log_file:
        # If log line matches our regex, print to console, and output file
        if line_start_referencestart.search(line):
            FFT_referencestart = int(re.findall(r'referencestart: (\d+)', line)[0])
        if line_start_referenceend.search(line):
            FFT_referenceend = int(re.findall(r'referenceend: (\d+)', line)[0])
        if line_Start_maxshift.search(line):
            FFT_maxshift = int(re.findall(r'maxShift: (\d+)', line)[0])
        if line_start_corvalmin.search(line):
            FFT_corvalmin = float(re.findall(r'corvalMin: (\d\D\d+)', line)[0])

        if line_start_target_info.search(line):
            subKeyNumberString = re.findall(r'target:.(\d+)', line)
            subKeyNumber = int(subKeyNumberString[0])
            if firstParse:
                firstParse = False
                if subKeyNumber == 1:
                    subtractFromParsedSubKeyNumber = 1
            subKeyNumber -= subtractFromParsedSubKeyNumber
            #print line
            #print("Parsing log file for subKeyNumber: ", subKeyNumber)
            subByteGuesses = []
            dataSet.append(subByteGuesses)
        if line_start_rank_data.search(line):        
            test = ""
            if "candidate" in line and "@" in line:
                test  = re.findall(r'rank:[^\d]+(\d+), candidate: ([0][x]..), peak: (\d[.]\d+) @ (\d+)', line)
            elif "correct" in line and "@" in line:
                test  = re.findall(r'rank:[^\d]+(\d+), correct  : ([0][x]..), peak: (\d[.]\d+) @ (\d+)', line)
            elif "candidate" in line:
                test  = re.findall(r'rank:[^\d]+(\d+), candidate: ([0][x]..), . of peaks: (\d[.]\d+)', line)
            elif "correct" in line:
                test = re.findall(r'rank:[^\d]+(\d+), correct  : ([0][x]..), . of peaks: (\d[.]\d+)', line)
            
            #print(test)            
            currentCorVal = CorrelationValue()
            currentCorVal.rank = int(test[0][0])
            currentCorVal.candidate = int(str(test[0][1]), 16)
            currentCorVal.peak = float(test[0][2])
            currentCorVal.subKey = subKeyNumber
            if "@" in line:
                currentCorVal.sample = int(test[0][3])
            else:
                currentCorVal.sample = 0

            if currentCorVal.rank == 1:
                currentCorVal.relativePeak = 1
            else:
                currentCorVal.relativePeak = currentCorVal.peak/dataSet[subKeyNumber][0].peak
            dataSet[subKeyNumber].append(currentCorVal)

print("")
print("######################")
print("Number of subKeys to test:    ", len(dataSet))
print("Number of candidates per key: ", len(dataSet[0]))

#print("FFT Settings: ")
#print("Reference start: {}".format(FFT_referencestart))
#print("Reference end: {}".format(FFT_referenceend))
#print("MaxShift: {}".format(FFT_maxshift))
#print("CorvalMin: {}".format(FFT_corvalmin))

print("Correct positions: ")

f, (ax1, ax2) = plt.subplots(1, 2)
f.set_size_inches(18.5, 10.5, forward=True)
for i, subKey in enumerate(dataSet):
    for rank in subKey:
        if rank.candidate==knownKey[i]:
            print("Subkey: {:>3}, rank: {:>3}, peak: {:f}, relative peak: {:f}, sample point: {:>4}".format(i, rank.rank, rank.peak, rank.relativePeak, rank.sample))
            ax1.bar([i],[rank.sample])
            #plt.text(i, rank.sample, str(rank.sample))
            ax1.text(i-0.42, rank.sample+13, str(rank.sample), color='blue', va='center')
            break
print("")



#plt.ylabel('Sample point')
#plt.xlabel('SubKey')
ax1.set_title("Correct candidate's sample points")
ax2.set_title("Best guesse's sample points")
ax1.set(ylabel='Sample point')
ax1.set(xlabel='SubKey')
ax2.set(ylabel='Sample point')
ax2.set(xlabel='SubKey')


print("Best guesses: ")
#plt.subplots(2,1,2)
for i, subKey in enumerate(dataSet):
    print("Subkey: {:>3}, rank: {:>3}, peak: {:f}, relative peak: {:f}, sample point: {:>4}".format(i, subKey[0].rank, subKey[0].peak, subKey[0].relativePeak, subKey[0].sample))
    ax2.bar([i],[subKey[0].sample])
    #plt.text(i, rank.sample, str(rank.sample))
    ax2.text(i-0.42, subKey[0].sample+13, str(subKey[0].sample), color='blue', va='center')


plt_name = args.input.replace(".log", "")
plt.savefig(plt_name + '.pdf')
if args.plot == '1':
    plt.show()


relativePeakList = []
for i, subKey in enumerate(dataSet):
    subKeyCandidateList = []
    for candidate in subKey:
        subKeyCandidateList.append(candidate.relativePeak)
    relativePeakList.append(subKeyCandidateList)


# These are the colors that will be used in the plot
color_sequence = ['#1f77b4', '#aec7e8', '#ff7f0e', '#ffbb78', '#2ca02c',
                  '#98df8a', '#d62728', '#ff9896', '#9467bd', '#c5b0d5',
                  '#8c564b', '#c49c94', '#e377c2', '#f7b6d2', '#7f7f7f',
                  '#c7c7c7', '#bcbd22', '#dbdb8d', '#17becf', '#9edae5']


y_pos = 0
fig2, (ax3) = plt.subplots() # two axes on figure
fig2.set_size_inches(18.5, 10.5, forward=True)
ax3.set_title("Relative correlation")
ax3.set(ylabel='Relative correlation per guess')
ax3.set(xlabel='Guess number')

for subKey in range(0,16):
    ax3.plot(range(0,256),relativePeakList[subKey], color=color_sequence[subKey], label=str(subKey))
    #ax3.text(270, y_pos, str(subKey), fontsize=14, color=color_sequence[subKey])
    y_pos += 15
# Place a legend to the right of this smaller subplot.
plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
plt_name = args.input.replace(".log", "")
plt.savefig(plt_name + '_correlation.pdf')
if args.plot == '1':
    plt.show()


#exit()
exepectedSamplePoints = [36,104,128,78,34,81,146,54,21,114,132,74,13,109,160,44]



print("Applying filter")
#plt.subplots(2,1,2)
window = 55
adjustedDataSet = []

for i, subKey in enumerate(dataSet):
    tempList = []
    numApproved = 1
    for j,candidate in enumerate(subKey):
        if exepectedSamplePoints[i] - window < candidate.sample < exepectedSamplePoints[i] + window:
            candidate.rank = numApproved
            numApproved += 1
            tempList.append(candidate)
    print("Subkey {}: number of candidates after filter: {}".format(str(i).ljust(2), len(tempList)))
    adjustedDataSet.append(tempList) 




print("Correct positions after filter: ")

for i, subKey in enumerate(adjustedDataSet):
    for rank in subKey:
        if rank.candidate==knownKey[i]:
            print("Subkey: {:>3}, rank: {:>3}, peak: {:f}, relative peak: {:f}, sample point: {:>4}".format(i, rank.rank, rank.peak, rank.relativePeak, rank.sample))
            break
print("")




print("Best after filter guesses: ")
for i, subKey in enumerate(adjustedDataSet):
    print("Subkey: {:>3}, rank: {:>3}, peak: {:f}, relative peak: {:f}, sample point: {:>4}".format(i, subKey[0].rank, subKey[0].peak, subKey[0].relativePeak, subKey[0].sample))


print("######################")
# The Sub-Optimal sorting algorithm
#print("Fill out global list G with highest relative correlation values in descending order,")
#print("while testing if the new element in G is the correct one")
G = []
#G = sorted(dataSet, key=lambda relativePeak: )

#G = sorted(dataSet, key=itemgetter())

#print "Subkey 10, rank 80 peak correlation: ", dataSet[10][79].relativePeak
#print "Subkey 10, rank 80 peak correlation: {}".format(hex(dataSet[10][79].candidate))
#exit()
#print("Initialise g[] with top candidates from attack")
g = []
index_list = []
g.append([])
index_list.append([])

for i in range(0, 16):
    g[0].append(dataSet[i][0].candidate)
    index_list[0].append(dataSet[i][0].rank)
guessCount = 1


if g[0] == knownKey:
    print("Found correct key, guess count: ", guessCount)
    print("######################")
    exit()

g.append([])
for i in range(0, 16):
    g[1].append(adjustedDataSet[i][0].candidate)
    index_list[1].append(adjustedDataSet[i][0].rank)
guessCount = 1

if g[1] == knownKey:
    print("Found correct key , guess count (after filter): ", guessCount)
    print("######################")
    exit()


correct_candidates = []
min_corRelPeak = 1
for i, subKey in enumerate(dataSet):
    for rank in subKey:
        if rank.candidate==knownKey[i]:
           correct_candidates.append(rank)
           if rank.relativePeak < min_corRelPeak:
                print("Minimum correlation value: {}".format(rank.relativePeak))
                print("Subkey nr: {} Rank nr: {}".format(i, rank.rank))
                min_corRelPeak = rank.relativePeak
           break

numberOfNeededGuesses = 1

corValPeakIndexesList = []
for i, subKey in enumerate(dataSet):
    for rank in subKey:
        if  not rank.relativePeak >= min_corRelPeak:
            corValPeakIndexesList.append(rank.rank-1)
            print("Candidate index needed: {}".format(rank.rank-1))
            break
        if rank.rank == 256:
            corValPeakIndexesList.append(rank.rank)
            print("Candidate index needed: {}".format(rank.rank))
            break





for index in corValPeakIndexesList:
    numberOfNeededGuesses = numberOfNeededGuesses * index
print("Number of needed guesses calculated = {}".format(numberOfNeededGuesses))
print("######################")

exit()


