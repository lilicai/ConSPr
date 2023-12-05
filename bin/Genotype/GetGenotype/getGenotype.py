import argparse
import sys
import glob
import re
import os
import subprocess
from numpy import loadtxt
import joblib
import pandas as pd
import numpy as np

def getContaminated(File):
	concordance = 0
	concordance_stat = '-'
	contamina_tumor_rate = 0
	contamina_tumor_stat = '-'
	contamina_normal_rate = 0
	contamina_normal_stat = '-'
	label = '-'
	with open(File,"r") as f:
		title = f.readline().strip().split('\t')
		for line in f:
			dat = dict(zip(title,line.strip().split('\t')))
			sample = dat['Sample']
			if 'Concordance' in dat:concordance = float(dat['Concordance'])
			if 'Concordance Stat' in dat:concordance_stat = dat['Concordance Stat']
			if 'Tumor sample contamination level' in dat:contamina_tumor_rate = float(dat['Tumor sample contamination level'])
			if 'Tumor Contamination Stat' in dat:contamina_tumor_stat = dat['Tumor Contamination Stat']
			if 'Normal sample contamination level' in dat:contamina_normal_rate = float(dat['Normal sample contamination level'])
			if 'Normal Contamination Stat' in dat:contamina_normal_stat = dat['Normal Contamination Stat']
	print(concordance,concordance_stat,contamina_tumor_rate,contamina_tumor_stat,contamina_normal_rate,contamina_normal_stat)
	return(concordance,concordance_stat,contamina_tumor_rate,contamina_tumor_stat,contamina_normal_rate,contamina_normal_stat)

def get_pollution_genetype(df_database_site,homo_peak):
	site_dic = df_database_site.T.to_dict()
	for pos in site_dic:
		ref = site_dic[pos]['ref']
		alt = site_dic[pos]['alt']
		tumor_fre = float(site_dic[pos]['Tumor_Frequency'])
		normal_fre = float(site_dic[pos]['Normal_Frequency'])
		normal_genetype = site_dic[pos]['Normal_Genetype']
		tumor_genetype = site_dic[pos]['Tumor_Genetype']
		wild_genetype = ref+ref
		het_genetype = ref+alt
		homo_genetype = alt+alt
		if normal_genetype == wild_genetype:
			pol_homo_fre = homo_peak
			pol_het_fre = 0.5*homo_peak
			pol_wild_fre = 0
			if abs(tumor_fre-pol_homo_fre) < abs(tumor_fre-pol_het_fre) and \
				abs(tumor_fre-pol_homo_fre) < abs(tumor_fre-pol_wild_fre):
				site_dic[pos]['Pollution_Genetype'] = homo_genetype
			elif abs(tumor_fre-pol_wild_fre) < abs(tumor_fre-pol_het_fre) and \
				abs(tumor_fre-pol_wild_fre) < abs(tumor_fre-pol_homo_fre):
				site_dic[pos]['Pollution_Genetype'] = wild_genetype
			else:
				site_dic[pos]['Pollution_Genetype'] = het_genetype
		elif normal_genetype == homo_genetype:
			pol_homo_fre = 100
			pol_het_fre = 100 - 0.5*homo_peak
			pol_wild_fre = 100 - homo_peak
			if abs(tumor_fre-pol_homo_fre) < abs(tumor_fre-pol_het_fre) and \
				abs(tumor_fre-pol_homo_fre) < abs(tumor_fre-pol_wild_fre):
				site_dic[pos]['Pollution_Genetype'] = homo_genetype
			elif abs(tumor_fre-pol_wild_fre) < abs(tumor_fre-pol_het_fre) and \
				abs(tumor_fre-pol_wild_fre) < abs(tumor_fre-pol_homo_fre):
				site_dic[pos]['Pollution_Genetype'] = wild_genetype
			else:
				site_dic[pos]['Pollution_Genetype'] = het_genetype
		elif normal_genetype == het_genetype:
			pol_homo_fre = min(0.5*(100-homo_peak)+homo_peak,100)
			pol_het_fre = 50
			pol_wild_fre = max(50 - homo_peak,0)
			#print(pos)
			#print(pol_homo_fre)
			#print(pol_het_fre)
			#print(pol_wild_fre)
			#print(tumor_fre)
			#print(normal_fre)
			if abs(tumor_fre-pol_homo_fre) < abs(tumor_fre-pol_het_fre) and \
				abs(tumor_fre-pol_homo_fre) < abs(tumor_fre-pol_wild_fre):
				site_dic[pos]['Pollution_Genetype'] = homo_genetype
			elif abs(tumor_fre-pol_wild_fre) < abs(tumor_fre-pol_het_fre) and \
				abs(tumor_fre-pol_wild_fre) < abs(tumor_fre-pol_homo_fre):
				site_dic[pos]['Pollution_Genetype'] = wild_genetype
			else:
				site_dic[pos]['Pollution_Genetype'] = het_genetype
			#print(site_dic[pos]['Pollution_Genetype'])
		else:
				site_dic[pos]['Pollution_Genetype'] = '-'
	return(site_dic)

def get_database(databasefile,tumor_site_dic,normal_site_dic,prefix,consistency_cutoff,outdir,contaFile):
	database_dic = {}
	genetype_site_info_dic = {}
	genetype_site_info_dic['Sample']=prefix
	with open(databasefile,"r") as f:
		for line in f:
			dat = line.strip().split('\t')
			ch = dat[0]
			start = dat[1]
			ref = dat[3]
			alt = dat[4]
			pos = "_".join([dat[0],str(dat[1])])
			tumor_genetype = 'Tumor_Genetype'
			normal_genetype = 'Normal_Genetype'
			tumor_fre = 'Tumor_Frequency'
			normal_fre = 'Normal_Frequency'
			if pos not in database_dic:database_dic[pos] = {}
			database_dic[pos]['ref'] = ref
			database_dic[pos]['alt'] = alt
			if pos in tumor_site_dic:
				database_dic[pos][tumor_genetype] =tumor_site_dic[pos]['genetype']
				database_dic[pos][tumor_fre] = tumor_site_dic[pos]['fre']
			else:
				database_dic[pos][tumor_genetype] = ref+ref
				database_dic[pos][tumor_fre] = '0'
			if pos in normal_site_dic:
				database_dic[pos][normal_genetype] =normal_site_dic[pos]['genetype']
				database_dic[pos][normal_fre] = normal_site_dic[pos]['fre']
			else:
				database_dic[pos][normal_genetype] = ref+ref
				database_dic[pos][normal_fre] = '0'
	df_database_site = pd.DataFrame.from_dict(database_dic,orient='index')
	convert_dict = {normal_fre:float,
					tumor_fre:float}
	df_database_site = df_database_site.astype(convert_dict)

	#print(df_database_site)
	pair_genetype_outfile = outdir+'/'+ prefix + '.pair.genetype_result.xls'
	df_database_site.to_csv(pair_genetype_outfile,sep="\t")

	##contamina info
	(concordance,concordance_stat,contamina_tumor_rate,contamina_tumor_stat,contamina_normal_rate,contamina_normal_stat) = getContaminated(contaFile)
	print(contaFile)
	print("===========")
	print(concordance,concordance_stat,contamina_tumor_rate,contamina_tumor_stat,contamina_normal_rate,contamina_normal_stat)

	##pollution genetype
	if(contamina_tumor_stat == 'Faliure'):
		#以数据库中的位点为准
		pollution_dic = get_pollution_genetype(df_database_site,contamina_tumor_rate)
		print(df_database_site.shape)
		df_pollution_result = pd.DataFrame.from_dict(pollution_dic,orient='index')
		pollution_genetype_outfile = outdir+'/'+ prefix + '.sample.pollution.genetype.xls'
		df_pollution_result.to_csv(pollution_genetype_outfile,sep="\t")
		#normal或tumor中发生突变的位点为准
		df_database_site['sum'] = df_database_site[tumor_fre] + df_database_site[normal_fre]
		df_database_change_site = df_database_site[df_database_site['sum'] != 0]
		del df_database_change_site['sum']
		del df_database_site['sum']
		pollution_change_dic = get_pollution_genetype(df_database_change_site,contamina_tumor_rate)
		print(df_database_change_site.shape)
		df_pollution_change_result = pd.DataFrame.from_dict(pollution_change_dic,orient='index')
		pollution_change_genetype_outfile = outdir+'/'+ prefix + '.sample.pollution.change.genetype.xls'
		df_pollution_change_result.to_csv(pollution_change_genetype_outfile,sep="\t")
		#以normal中发生突变的位点为准
		print(df_database_site.shape)
		df_database_changeN_site = df_database_site[df_database_site['Normal_Frequency'] != 0]
		pollution_changeN_dic = get_pollution_genetype(df_database_changeN_site,contamina_tumor_rate)
		print(df_database_changeN_site.shape)
		pollution_changeN_dic = get_pollution_genetype(df_database_changeN_site,contamina_tumor_rate)
		df_pollution_changeN_result = pd.DataFrame.from_dict(pollution_changeN_dic,orient='index')
		pollution_changeN_genetype_outfile = outdir+'/'+ prefix + '.sample.pollution.changeN.genetype.xls'
		df_pollution_changeN_result.to_csv(pollution_changeN_genetype_outfile,sep="\t")

	return(df_database_site)

def get_site(variantfile,cutoff):
	variant_dic = {}
	with open(variantfile,"r") as f:
		title = f.readline().strip().split('\t')
		for line in f:
			dat = dict(zip(title,line.strip().split('\t')))
			sample = dat['Sample']
			ch = dat['Chr']
			start = dat['Start']
			ref = dat['Ref']
			alt = dat['Alt']
			genetype = dat['GT']
			depth = dat['Coverage']
			fre = dat['Var'].replace("%","")
			alle = 'NA'
			if ref == '-' or alt == '-' or len(ref) > 1 or len(alt) >1 : continue
			if int(depth) < int(cutoff): continue
			if genetype == '1/1'or genetype == '1':
				alle = alt+alt
			elif genetype == '0/1':
				alle = ref+alt
			pos = "_".join([ch,str(start)])
			if pos not in variant_dic:variant_dic[pos] = {}
			variant_dic[pos]['genetype'] = alle
			variant_dic[pos]['fre'] = fre
	return(variant_dic)


''' main '''
if __name__ == '__main__':
	parser=argparse.ArgumentParser(description = 'get hotpot site depth,alt,fre')
	parser.add_argument('--outdir','-o',required=False,default="./",help="Outdir [optional, Default: ./]")
	parser.add_argument('--baseline','-m',required=True,help="Dir of model file [Required]")
	parser.add_argument('--prefix','-p',required=True,help=" file  name [Required]")
	parser.add_argument('--tumorfile','-t',required=True,help=" tumor germline file   [Required]")
	parser.add_argument('--normalfile','-n',required=True,help=" normal germline file   [Required]")
	parser.add_argument('--contafile','-cf',required=True,help=" contamina file   [Required]")
	parser.add_argument('--consistencyCutoff','-cc',required=False,default=0.6,help="depth  cutoff  default 0.6")
	parser.add_argument('--UpdHomoCutoff','-uoc',required=False,default=0.1,help="UPD Homo diff rate  cutoff  default 0.1")
	parser.add_argument('--UpdHetCutoff','-uec',required=False,default=0.7,help="UPD Homo diff rate  cutoff  default 0.7")
	parser.add_argument('--cutoff','-c',required=False,default=30,help="depth  cutoff  default 30")
	args=vars(parser.parse_args())

	subprocess.check_call("mkdir -p {0}".format(args['outdir']),shell=True)
	#01.get.tumor.germline.site
	tumor_site_dic = get_site(args['tumorfile'],args['cutoff'])
	#02.get.normal.germline.site
	normal_site_dic = get_site(args['normalfile'],args['cutoff'])
	#03.get.database.site,merge_tumor_normal,consistency
	print(args['contafile'])
	df_database_site =  get_database(args['baseline'],tumor_site_dic,normal_site_dic,args['prefix'],args['consistencyCutoff'],args['outdir'],args['contafile'])
	#merge_pair_site(tumor_site_dic,normal_site_dic,database_dic)
	#04.statistic diff and features
	#get_features_file(df_database_site,prefix,outdir)
	#06.consistency
