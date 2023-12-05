import argparse
import sys
import glob
import re
import os
import subprocess
import xgboost
from numpy import loadtxt
from xgboost import XGBClassifier 
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.metrics import confusion_matrix
import statsmodels.nonparametric.api as smnp
import joblib
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
'''
该脚本用于污染源样本查询
输入是本软件推测出的污染源基因型文件sample.pollution.genetype.xls和疑似污染源样本集的突变文件，将推测的污染源基因型和疑似污染源的样本集中的样本两两进行基因型一致性比较，大于给定的阈值，认为是污染源样本,否则不是污染源样本：
1）计算两个样本基因型一致性时使用的位点总数为污染源基因型文件sample.pollution.genetype.xls中的总位点
2）如果疑似污染源样本集中基因型一致性大于等于阈值0.9时，认为该样本为污染源样本
3）如果疑似污染源样本集中的样本均小于阈值0.9时，认为污染源不包含在疑似污染源样本集
'''

def  merge_pollutions(pollufile,indir,site_dic,cutoff,pollutionCutoff,outdir,prefix):
	variant_dic = {}
	sample_dic = {}
	variantfiles = glob.glob(indir + "/*xls")
	for variantfile in variantfiles:
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
				alle = 'NA'
				if ref == '-' or alt == '-' or len(ref) > 1 or len(alt) >1 : continue
				if int(depth) < int(cutoff): continue
				if genetype == '1/1'or genetype == '1':
					alle = alt+alt
				elif genetype == '0/1':
					alle = ref+alt
				pos = "_".join([ch,str(start)])
				if sample not in variant_dic:variant_dic[sample] = {}
				variant_dic[sample][pos] = alle
				sample_dic[sample] = sample

	pollution_variant_dic = {}
	for sample in sample_dic:
		if sample not in pollution_variant_dic:pollution_variant_dic[sample] = {}
		for pos in site_dic:
			if pos not in variant_dic[sample]:
				ref,alt = site_dic[pos].split("_")
				pollution_variant_dic[sample][pos] = ref+ref
			else:
				pollution_variant_dic[sample][pos] = variant_dic[sample][pos]

	df_pollution_variant = pd.DataFrame.from_dict(pollution_variant_dic)
	df_pollution_genetype = pd.read_csv(pollufile,sep="\t",index_col=0)
	df_merge = pd.merge(df_pollution_genetype['Pollution_Genetype'],df_pollution_variant,left_index=True,right_index=True)

	pollution_source_dic = {}
	for i in(range(1,df_merge.shape[1])):
		if df_merge.columns[i] not in pollution_source_dic:pollution_source_dic[df_merge.columns[i]] = {}
		#pollution_source_dic[df_merge.columns[i]]['isSame'] = df_merge[df_merge.columns[0]] == df_merge[df_merge.columns[i]]
		all_genetype = (df_merge[df_merge.columns[0]] == df_merge[df_merge.columns[i]]).value_counts()
		pollution_source_dic[df_merge.columns[i]]['Same_Genetype_Nums'] = all_genetype.loc[True]
		pollution_source_dic[df_merge.columns[i]]['Diff_Genetype_Nums'] = all_genetype.loc[False] if False in all_genetype else 0
		pollution_source_dic[df_merge.columns[i]]['All_Site_Nums'] = pollution_source_dic[df_merge.columns[i]]['Same_Genetype_Nums'] + pollution_source_dic[df_merge.columns[i]]['Diff_Genetype_Nums']
		pollution_source_dic[df_merge.columns[i]]['Consistency_Percent'] = round(pollution_source_dic[df_merge.columns[i]]['Same_Genetype_Nums']/pollution_source_dic[df_merge.columns[i]]['All_Site_Nums'],2)
		if pollution_source_dic[df_merge.columns[i]]['Consistency_Percent'] > pollutionCutoff:
			pollution_source_dic[df_merge.columns[i]]['Pollution_Flag'] = 'True'
		else:
			pollution_source_dic[df_merge.columns[i]]['Pollution_Flag'] = 'Flase'

	df_pollution_source = pd.DataFrame.from_dict(pollution_source_dic)
	pollution_outfile = outdir+'/'+ prefix + '.pollotion.source_result.xls'
	df_pollution_source.to_csv(pollution_outfile,sep="\t")

def get_site(databasefile):
	database_dic = {}
	with open(databasefile,"r") as f:
		title = f.readline().strip().split('\t')
		for line in f:
			dat = line.strip().split('\t')
			pos = dat[0]
			database_dic[pos] = "_".join([dat[1],dat[2]])
	return(database_dic)

''' main '''
if __name__ == '__main__':
	parser=argparse.ArgumentParser(description = 'get hotpot site depth,alt,fre')
	parser.add_argument('--outdir','-o',required=False,default="./",help="Outdir [optional, Default: ./]")
	parser.add_argument('--baseline','-b',required=False,help="Dir of model file [Required]")
	parser.add_argument('--prefix','-p',required=True,help=" file  name [Required]")
	parser.add_argument('--pollution','-po',required=True,help=" Pollution_Genetype file [Required]")
	parser.add_argument('--indir','-i',required=True,help=" normal germline file   [Required]")
	parser.add_argument('--pollutionCutoff','-pc',required=False,default=0.9,help="pollution sources  cutoff  default 0.9")
	args=vars(parser.parse_args())

	subprocess.check_call("mkdir -p {0}".format(args['outdir']),shell=True)
	#01.get.database.germline.site
	if args['baseline']:
		site_dic = get_site(args['baseline'])
	else:
		site_dic = get_site(args['pollution'])
	#02.merge.pollution.source.germline.site
	if os.path.exists(args['pollution']):
		normal_site_dic = merge_pollutions(args['pollution'],args['indir'],site_dic,30,args['pollutionCutoff'],args['outdir'],args['prefix'])
	#03.get.database.site,merge_tumor_normal,consistency
	#merge_pair_site(tumor_site_dic,normal_site_dic,database_dic)
	#04.statistic diff and features
	#get_features_file(df_database_site,prefix,outdir)
	#06.consistency
