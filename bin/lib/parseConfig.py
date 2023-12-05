import re
import sys
import os
import time
pat1=re.compile('^\s+$')


def ReadConfig(f_file):
	pat = re.compile('\[(\S+)\]')
	record = {}
	para = {}
	db = {}
	header = ''
	count = {} 
	s_index = {} ## to record table occurence time 
	for line in f_file:
		if line.startswith('#') or re.search(pat1,line):continue
		if line.startswith('['):
			match = pat.search(line)
			if match :
				header = match.group(1)
				if header not in count : 
					count[header] = 0
					record[header] = []
					s_index[header] = []
				else:
					count[header] += 1 
		else:
			if header == 'Para':
				tmp = [i.strip() for i in line.rstrip().split('=',1) ]
				if len(tmp) < 2 :
					print("Error:{0} is lack of value".format(line.rstrip()))
					sys.exit(1)
				else:
					para[tmp[0]] = tmp[1]
			if header == 'DB':
				tmp = [i.strip() for i in line.rstrip().split('=',1) ] 
				if len(tmp) < 2 :
					print("Error:{0} is lack of value".format(line.rstrip()))
					sys.exit(1)
				else:
					db[tmp[0]] = tmp[1]
			else:
				tmp = line.rstrip().split('\t')
				record[header].append(tmp)
				s_index[header].append(count[header])
	return record,para,db,s_index

def makedir(indir):
	os.popen('mkdir -p {0}'.format(indir))
	time.sleep(1)

def getab(indir):
	return os.path.abspath(indir)

def cpu(default, lines, set):
	if not default == None:
		return default
	if set.find('N') > -1 :
		return int(eval(set.replace('N',str(lines))))+1
	else:
		return int(set)

def queue(default , set_value):
	if not default == None : 
		return default
	else:
		return set_value

def chooseSamples(all_samples , sample_order):
	'''choose the last order samples, all_samples = [s1,s2,s4,s5], sample_order=[0,1,2,2], then return [s4,s5]
	'''
	if len(sample_order) == 0:
		return [] , 0 
	else:
		choose_number = sample_order[-1]
		choose_samples =  [j for i,j in enumerate(all_samples) if sample_order[i] == choose_number] 
		pre_count = len(all_samples) - len(choose_samples)
		return choose_samples , pre_count
