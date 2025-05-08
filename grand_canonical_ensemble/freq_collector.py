#!/bin/python

import sys,os
import numpy as np
import pandas as pd
import pickle

from concurrent.futures import ProcessPoolExecutor

'''
	read-in files
'''

root = '/mnt/lustre/a2fs-work2/work/e05/e05/uccahaq/klmc/_data/_ok/'

freq_file_root = []				# path to csvfile
csvlist = []				# csvfiles path

size = []
xlist = []

read_check = []				# check csv file exists
for i in range(2):
	# file_path = os.path.join(root,f'VO_{i}')
	freq_file_root.append(os.path.join(root,f'VO_{i}'))				# frequency calculation files root

	file_path = os.path.join('/mnt/lustre/a2fs-work2/work/e05/e05/uccahaq/klmc/_data/GC/',f'E_VO_{i}.csv')					# file path 'nconp{i}.csv'

	if not os.path.exists(file_path):
		print(file_path)
		print(f'file not found at: {file_path}',file=sys.stderr)
#		sys.exit()

	csvlist.append(file_path)
	size.append(i)
	xlist.append(float(i)/180.)

print(' ! preparing csv files done')

'''
	read-in csv-files
'''
dflist = []			# include 'dataframe'(s) of generic GULP calculation result
freqlist = []		# include 'dict'(s) of GULP calculation frequencies



def task_process(arg):

	'''
		processing frequencies
		given taskid, read file and return taskid and frequencies
	'''
	taskid, file_path = arg

	freqlist = []
	with open(file_path,'r') as f:
		for line in f:
			freqlist.append(float(line.strip()))

	return taskid, freqlist

for csvfile,s in zip(csvlist,size):
	df = pd.read_csv(csvfile)

	# --- energy calibration in 'df'

	# --- energy calibration done
	dflist.append(df)

	#print(freq_file_root[s]) # checked

	#
	# --- read in gamma point frequencies
	#
	#if s != 0:	# s : size
	if True:
		freq_summary = {}	# save this into 'pkl'

		print(f'writing pkl for the size = {s} ...')

		# get taskid list
		taskid_list = df['taskid'].tolist()
		print(taskid_list)
		# sys.exit()

		# taskid_path map object generation
		taskid_path_map = [] 
		for taskid in taskid_list:
			gulp_output_path = os.path.join(freq_file_root[s],f'A{taskid}')
			gulp_output_freq_path = os.path.join(gulp_output_path,'freq.txt')

			taskid_path_map.append((taskid,gulp_output_freq_path))	# set map fpr PoolExecutor	- input 'taskid'/'freq.txt file path'

		# dict
		freq_summary = {}
		with ProcessPoolExecutor(max_workers=32) as executor:
			for result in executor.map(task_process,taskid_path_map):
				freq_summary[result[0]] = result[1]
				# result[0] = taskid, result[1] = frequency_list

		with open(f'freq{s}.pkl','wb') as f:
			pickle.dump(freq_summary,f)
