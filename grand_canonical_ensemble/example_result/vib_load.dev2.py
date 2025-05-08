#!/bin/python

import os,sys
import pandas as pd
import numpy as np
import pickle

# from concurrent.futures import ProcessPoolExecutor

# constants ----
_wavenumber_to_ev = np.float128(1.239841984332e-4)
_kb = np.float128(8.617333262e-5)

#
# internal use functions 	-----------------------------------------------------
#
def expkbt(E,T):

	global _kb
	#E = np.float128(E)
	#T = np.float128(T)

	#try:
	#	ret = np.exp(-E/T/_kb)
	#except OverflowError:
	#	if -E/T/_kb > 500:
	#		ret = np.exp(500.)

	ret = np.exp(-E/T/_kb)
	return ret
		
def get_gz(csvdf,T,vib=False,pkldf=None):

	global _kb
	global _wavenumber_to_ev
	#u = np.float128(0.)	# _corr

	Elist = csvdf['energy'].values
	Egm = np.float128(Elist[0])		# global minimum

	T = np.float128(T)
	Z = np.float128(0.)
	G = np.float128(0.)

	if vib == False:

		for E in Elist:
			E = np.float128(E) - Egm
			Z += expkbt(E,T)
		
		Z = np.exp(-Egm/_kb/T) * Z	
		G = - _kb * T * np.log(Z)
		#print(Egm,-Egm/_kb/T,np.exp(-Egm/_kb/T),Z,G)
	#
	# include vibrational contributions
	#
	elif vib == True:
		#
		# looping thru structures / distinguished by 'taskid'
		#
		for E,taskid in zip(Elist,csvdf['taskid'].values):

			E = np.float128(E) - Egm
			ZE = expkbt(E,T)

			#
			# get freq info for this struct
			#
			freqlist = np.array(pkldf[taskid],dtype=np.float128)
			# add ZPE contribution - gamma point ?
			freq0_power = np.float128(0.)
			for freq in freqlist:
				freq0_power += (0.5 * freq * _wavenumber_to_ev)	
			Zvib0 = np.exp(-freq0_power/_kb/T)
	
			# add all vib contribution
			# NotImplemented

			# sum up
			Z += (ZE * Zvib0)

		# pull back Egm
		Z = np.exp(-Egm/_kb/T) * Z
		G = - _kb * T * np.log(Z)

	return np.float128(G),np.float128(Z)

# issue -> overflow	 ---------------------------
def get_grandZ(npZlist,npxlist,u,T):
	
	global _kb
	Zg = np.float128(0.)
	u = np.float128(u)
	T = np.float128(T)

	for Z,x in zip(npZlist,npxlist):
		Zg = Zg + np.exp(x*u/_kb/T) * Z
	
	return Zg # causing overflow
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ issue -> overflow

def get_wx(npZlist,npxlist,u,T):

	global _kb
	
	u = np.float128(u)
	wxlist = []	# return tmp

	for Z,x in zip(npZlist,npxlist):
		
		Zg = np.float128(0.)
		for Zp,xp in zip(npZlist,npxlist):
			Zg = Zg + np.exp((xp-x)*u/_kb/T) * Zp

		wx = Z/Zg
		wxlist.append(wx)

	return np.array(wxlist,dtype=np.float128)	# final type np.float128 numpy array


def get_expect_x(npxlist,npwxlist):

	expect_x = np.float128(0.)
	for x,wx in zip(npxlist,npwxlist):
		expect_x = expect_x + x*wx
	return expect_x


#
# inverting function <x>(u) ---> u(<x>)
#
def get_u_by_x(x,xlist,ulist):
	if len(xlist) != len(ulist):
		print(f'Err, xlist / ulist length are different ... something is wrong')
		sys.exit(1)
	if x < 0.0001 or x > 1.0:
		print(f'Err, x value must be in range [0.0001:1.0000]')
		sys.exit(1)
	# closest index (ci)
	ci = min(range(len(xlist)), key=lambda i: abs(xlist[i] - x))
	return ulist[ci]

def get_grand_pot(x_eval,T,npxlist,npZlist,expect_xlist,ulist):

	# x : pure input <x>
	# T : pure input
	
	# Zclist : Z canonical
	# xlist  : known x values
	# exlist / ulist for calculating chemical potential u(<x>)
	
	x_eval = np.float128(x_eval)
	T      = np.float128(T)
	#npexpect_xlist = np.array(expect_xlist,dtype=np.float128)
	#npulist = np.array(ulist,dtype=np.float128)

	global _kb
	
	gp = np.float128(0.)
	
	for x,Z in zip(npxlist,npZlist):
		gp += np.exp(x*get_u_by_x(x_eval,expect_xlist,ulist)/_kb/T) * Z
	
	gp = -_kb*T*np.log(gp)
	
	return x_eval, gp, get_u_by_x(x_eval,expect_xlist,ulist)

#
# ---- function end ---- -------------------------------------------------------------------
#

csv_files = []
pkl_files = []
for s in range(25):
	csv_files.append(f'nconp{s}.csv')
	pkl_files.append(f'freq{s}.pkl')

root = os.getcwd()

# set path pkl files
for index,pklfile in enumerate(pkl_files):
	pkl_files[index] = os.path.join(os.path.join(root,'freq_pkl'),pklfile)

csvlist = []
pkllist = []

# logging imag freq taskids
imlog = open("imag_freqlist.txt", "a") 
imlog.write(' * imag frequency listing [taskid]\n')

for i, (csv,pkl) in enumerate(zip(csv_files,pkl_files)):		# 'i' is for file index !! not structure index

	# skip size = 0 (no Li)
	#if i == 0:
	#	csv_df = pd.read_csv(csv)
	#	pkl_df = None

	#	csvlist.append(csv_df)	# csvlist -> csv dataframe
	#	pkllist.append(pkl_df)	# pkllist -> pkl dataframe
	#	continue

	csv_df = pd.read_csv(csv)
	pkl_df = pd.read_pickle(pkl)

	taskid_list = csv_df['taskid'].tolist()

	print(f' * processing size {i} | data count {len(csv_df)} ...')
	_drop_cnt = 0
	imag_freqlist = []

	# 1st scan : looping imag freq
	for struct_no, taskid in enumerate(taskid_list):
	
		# get frequencies of a struct with 'taskid'
		freqlist = pkl_df[taskid]

		#for freq in freqlist:
		#	if freq < 0.:
		#		if freq > -10e-2:
		#			freq = 0
		#		imag_freqlist.append(freq)

		_isdropped = False

		for freq in freqlist:
			if freq < -0.5:
				imag_freqlist.append(taskid)

				csv_df = csv_df.drop(struct_no)
				#print(f'dropping taskid: {taskid}')
				_isdropped = True
				_drop_cnt = _drop_cnt + 1
				break

		if not _isdropped:
			pkl_df[taskid] = pkl_df[taskid][3:]
			
	imlog.write(f' * {_drop_cnt}/{len(taskid_list)} structures with imaginary frequencies were found : ')
	for imag_taskid in imag_freqlist:
		imlog.write(f' {imag_taskid},')
	imlog.write('\n')

	print(f' | {_drop_cnt}/{len(taskid_list)} structures with imaginary frequencies were found')

	# 2nd scan: check imag freqs (negative)
	#print(f' | second pass imag freq check | data count {len(csv_df)} ...')
	#taskid_list = csv_df['taskid'].tolist()
	#for struct_no,taskid in enumerate(taskid_list):

	#	freqlist = pkl_df[taskid]

	#	for freq in freqlist:
	#		if freq < 0.:
	#			print(f' @ Error imag freq filter failed ...')
	#			sys.exit()
	print(f' | finished')
	
	csvlist.append(csv_df)
	pkllist.append(pkl_df)

imlog.close() # close imag freq log
#
# ---------- upto here takes 40 - 60 seconds
#

#
# size & concentration(x) list
#
sizelist = [ i for i in range(25) ]
npxlist = np.array([ float(i)/24. for i in range(25) ], dtype=np.float128)


# recalibrating energy :

# some model parameters
_e_gulp_mn2O4 = -534.25669638*6.                                        # R - Mn24O48 energy - unitcell based -534.25669638
_LiOx         = +5.39171                                                # Li(g) -> Li(+)(g) + e-
_MnRe         = -51.2                                                   # Mn(4+)(g) + e- -> Mn(3+)(g)
# this may change
_corr         = +1.6510 + 5.7400                                        # 1.6510(eV): formation energy Li CRC : +159.3kJ/mol Li(g), + residual energy 5.740 (eV) # _corr = 7.391
# using sample count
_max_sample = 10000

tmp_csvlist = []		# processed csvlist
for s, csvdf in zip(sizelist,csvlist):

	if len(csvdf) > 10000:
		#csvdf = csvdf.sample(n=_max_sample, random_state=42)	# use same randseed to keep reproducibility
		csvdf = csvdf.head(10000)

	# Lithiation Reaction Energy converting
	csvdf['energy'] = (csvdf['energy'] - _e_gulp_mn2O4 + (_LiOx + _MnRe + _corr) * s )/24.
	#csvdf['energy'] = (csvdf['energy'] - _e_gulp_mn2O4 + (_LiOx + _MnRe + 0. ) * s )/24. # no chemical potential
	csvdf = csvdf.sort_values(by='energy',ascending=True)

	print(f' * reaction energy calculation ... size : {s}')
	#print(csvdf)
	tmp_csvlist.append(csvdf)

csvlist = tmp_csvlist
# ---- Setting Temperature
try:
	_T = np.float128(float(sys.argv[1]))
except:
	_T = np.float128(300.)

try:
	_vib_flag = sys.argv[2]
	if _vib_flag == '-vib':
		_include_vib = True
except:
	_include_vib = False

print(f' * start ensemble analysis')
print(f' | temperature (K)     = {_T}')
print(f' | including vibration = {_include_vib}')

#
# G,Z =  def get_gz(csvdf,T,vib=False):
#
npGlist = np.zeros(len(csvlist),dtype=np.float128)
npZlist = np.zeros(len(csvlist),dtype=np.float128)

for s, (csvdf,pkldf) in enumerate(zip(csvlist,pkllist)):

	print(f' * processing partition function Z : size {s}')
	#if s == 0:	# skip case s == 0 - really?
	#	Gc,Zc = get_gz(csvdf,_T,vib=False)
	#	print(pkldf) # expected -> None
	#elif s > 0:
	#	Gc,Zc = get_gz(csvdf,_T,vib=_include_vib,pkldf=pkldf)

	Gc,Zc = get_gz(csvdf,_T,vib=_include_vib,pkldf=pkldf)		# MUST INCLUDE VIB FOR X = 0 Otherwise -> ERRRRRORRRRR!!!
	#print(Gc,Zc)
	npGlist[s] = Gc
	npZlist[s] = Zc
	#print(npGlist[s],npZlist[s])

print(f' * calculation of canonical G / Z done ...')
'''
	writing G x
'''
if _include_vib == False:
	fname = f'vib_Gx{_T}.out'
elif _include_vib == True:
	fname = f'vvib_Gx{_T}.out'
with open(fname,'w') as f:
	f.write(f'x, G, T={_T}, Ecorr={_corr}\n')
	for x,G in zip(npxlist,npGlist):
		f.write(f'{x}, {G}\n')
#for G,Z in zip(npGlist,npZlist):
#	#print('%20.8e%20.8e' % (G,Z))	# printing 'inf'
#	print(G,Z)						# printing fine
#	#print(f' | G : {G} / Z : {Z}') # printing 'inf'
#	#print(f' | G : {np.float128(G)} / Z : {np.float128(Z)}') # printing 'inf'
#	#print(f' | G : {G:.8e} / Z : {Z:.8e}')	# printing 'inf'
#for Z in npZlist:
#	print(Z,Z-100000000)

#
# Chemical potential set
#
_bin = 3000
_rbin = _bin - 1000
_du  = 0.0025
ulist = [ float(i)*_du for i in range(-_bin,+_rbin+1)]
print(f'chemical potential u: window [ {-_bin*_du} : {+_rbin*_du} ]')
npulist = np.array(ulist,dtype=np.float128)

#
# calculate <x> for given 'u' & '_T'
#
expect_xlist = []
for u in ulist:
	
	#Zg = get_grandZ(npZlist,npxlist,u,_T)	# overflow error

	npwxlist = get_wx(npZlist,npxlist,u,_T)
	expect_x = get_expect_x(npxlist,npwxlist)
	expect_xlist.append(expect_x)

	'''
		note
		(1) u vs x plot ...  chemical potential vs <x>
		(2) x vs -u plot ... <x> vs cell voltage
	'''
#
# inversion check
#
if _include_vib == False:
	fname = f'vib_invcheck{_T}.out'
elif _include_vib == True:
	fname = f'vvib_invcheck{_T}.out'
with open(fname,'w') as f:
	input_x = [0.01,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,0.995]
	for x in input_x:
		f.write(f'{x}\t {get_u_by_x(x,expect_xlist,ulist)}\n')

if _include_vib == False:
	fname = f'vib_raw{_T}.out'
elif _include_vib == True:
	fname = f'vvib_raw{_T}.out'
with open(fname,'w') as f:
	f.write('x_LiConc, u, -u\n')
	for x,u in zip(expect_xlist,ulist):
		f.write('%.8f, %.8f, %.8f\n' % (x,u,-u))

'''
	invert function
'''
_bin = 2000
_dx  = 1./_bin
ixlist = [ float(i)*_dx for i in range(1,_bin+1)]
npixlist = np.array(ixlist,dtype=np.float128)

if _include_vib == False:
	fname = f'vib_T{_T}_all.out'
elif _include_vib == True:
	fname = f'vvib_T{_T}_all.out'
with open(fname,'w') as f:
	f.write('x_LiConc, GrandPotential, u, -u\n')
	for x_eval in npixlist:
		x,gp,u = get_grand_pot(x_eval,_T,npxlist,npZlist,expect_xlist,ulist)
		f.write("%.8f, %.8f, %.8f, %.8f\n" % (x,gp,u,-u))

'''
	observable calculation
'''
# NotImplemented
