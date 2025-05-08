#!/bin/python

import pickle
import sys

size = sys.argv[1]
taskid = int(sys.argv[2])

with open(f'freq{size}.pkl','rb') as f:
	freq_pkl = pickle.load(f)

# size 1 taskid 123
for freqs in freq_pkl[taskid]:
	print(freqs)

print(f'length : {len(freq_pkl)}')
