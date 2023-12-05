import os
import re
import sys
import argparse


def split_stat(FORMAT,STAT,length):
	FORMAT = FORMAT.split(':')
	STAT = dict(zip(FORMAT,STAT.split(':')))
	#GT :  AD       :  DP    :GQ	:PL
	#1/2:  1,295,118:  414   :99	:20675,3740,2197,12297,0,11456	
	STAT_LIST = []
	for n in range(0,length):
		res = ''
		for title in FORMAT:
			if title == 'GT':
				res += '0/1:'
			elif title == 'AD':
				AD = STAT['AD'].split(',')
				res += AD[0] + ',' + AD[n+1] + ':'
			elif title == 'PL':
				PL = STAT['PL'].split(',')
				res += ','.join([PL[n*3],PL[n*3+1],PL[n*3+2]]) + ':'
			else:
				res += STAT[title] + ':'
		res = res.strip(':')
		STAT_LIST.append(res)
	return(STAT_LIST)

def split_info(INFO,length):
	m = re.match(r'AC=(.*?);AF=(.*?);(.*);MLEAC=(.*?);MLEAF=(.*?);(.*)$',INFO)
	if m :
		AC = m.group(1).split(',')
		AF = m.group(2).split(',')
		MLEAC = m.group(4).split(',')
		MLEAF = m.group(5).split(',')
		
		INFO_LIST = []
		for n in range(0,length):
			res = 'AC=' + AC[n] + ';AF=' + AF[0] + ';' + m.group(3) + ';MLEAC=' + MLEAC[n] + ';MLEAF=' + MLEAF[0] + ';' + m.group(6)
			INFO_LIST.append(res)
			
		return(INFO_LIST)
	else:
		return(INFO)
		
''' '''
if __name__ == '__main__':
	parser = argparse.ArgumentParser(description = 'split GATK vcf')
	parser.add_argument('-vcf', '--vcf',help = 'vcf file',required = True)
	parser.add_argument('-out', '--out',help = 'out file name',required = True)
	
	args = vars(parser.parse_args())
	f_in = args['vcf']
	f_out = args['out']
	
	with open(f_in, 'r') as f, open(f_out,'w') as fw:
		res = ''
		i	= 0
		for lane in f:
			if lane.startswith('##'):
				res += lane
				continue
			if lane.startswith('#CHROM'):
				title = lane.strip().split('\t')
				res += lane
				continue
			dat = lane.strip().split('\t')
			#dat_dic = dict(zip(title,dat))
			if ',' in dat[4]:
				i+=1
				ALT = dat[4].split(',')
				length = len(ALT)
				
				STAT_LIST = split_stat(dat[8],dat[9],length)
				INFO_LIST = split_info(dat[7],length)

				for N in range(0, length):
					#print(dat[1],STAT_LIST[N])
					res += '\t'.join([dat[0],dat[1],dat[2],dat[3],ALT[N],dat[5],dat[6],INFO_LIST[N],dat[8],STAT_LIST[N]]) + '\n'
			else:
				res += lane 
		print('All %s site split' %i)
		fw.write(res)
				
					
					
			
