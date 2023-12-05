#! /usr/bin/env python3
# -*- coding: utf-8 -*-

'''
2023-10-18
该脚本用于统计ConPair软件得到的结果是否能进行下一步分析
输入是ConPair得到的concordance.xls和contamination.xls文件，从文件中提取出三个指标，任意一个不满足要求，认为Failure,否则Success：
1）N/T 两个样本的一致性 默认是必须大于等于99为同一样本，介于80~99有可能为被污染的同一样本，否则认为样本配对错误（官方建议99）
2）T样本污染程度 默认是必须小于等于0.5，否则认为样本存在污染（官方建议0.5）
3）N样本污染程度 默认是必须小于等于10，否则认为样本存在污染（根据模拟数据得到的cutoff）
4）用于计算的位点个数大于等于100，否则结果不可信

'''

import argparse
import sys
import os
import re
import glob

__author__ = 'Cai lili'
__mail__ = 'lilicai@chosenmedtech.com'

def readfile(Dict,File):
	with open(File,"r") as fi:
		for line in fi:
			key,value = line.strip().split(":")
			key = key.strip()
			value = value.strip().strip("%")
			Dict[key] = value
	return Dict

def getSiteNums(Dict,File):
	with open(File,"r") as fi:
		for line in fi:
			m = re.findall(r'^Based on (\d+)/(\d+) markers',line)
			if m:
				Dict['SiteNums'] = m[0][0]
				Dict['TotalNums'] = m[0][1]
	return Dict
			

def ConpairStat(args):
	infodict = {}
	infodict = readfile(infodict,args.concordance)
	infodict = getSiteNums(infodict,args.concordance)
	infodict = readfile(infodict,args.contamination)
	stat = "Success"
	stat_concordance = "Success"
	stat_contamination_tumor = "Success"
	stat_contamination_normal = "Success"
	stat_site_nums = "Success"
	Concordance = float(infodict["Concordance"])
	TotalNums = int(infodict["TotalNums"])
	SiteNums = int(infodict["SiteNums"])
	Nc = float(infodict["Normal sample contamination level"])
	Tc = float(infodict["Tumor sample contamination level"])
	if Concordance < args.fh or Nc > args.fn or Tc > args.ft or TotalNums < args.fs:
		stat = "Faliure"
	if Concordance < args.fh and Concordance > args.fl:
		stat_concordance = "Ambiguous"
	elif Concordance < args.fl:
		stat_concordance = "Faliure"
	if Nc > args.fn:
		stat_contamination_normal = "Faliure"
	if Tc > args.ft:
		stat_contamination_tumor = "Faliure"
	if SiteNums < args.fs:
		stat_site_nums = "Faliure"
	with open(args.outfile,"w") as fo:
		print("\t".join(["Sample","TotalNums","SiteNums","Site Nums Stat","Concordance","Concordance Stat","Normal sample contamination level","Normal Contamination Stat","Tumor sample contamination level","Tumor Contamination Stat","Stat"]))
		fo.write("\t".join(["Sample","TotalNums","SiteNums","Site Nums Stat","Concordance","Concordance Stat","Normal sample contamination level","Normal Contamination Stat","Tumor sample contamination level","Tumor Contamination Stat","Stat"])+"\n")
		print("\t".join(map(str,[args.prefix,TotalNums,SiteNums,stat_site_nums,Concordance,stat_concordance,Nc,stat_contamination_normal,Tc,stat_contamination_tumor,stat])))
		fo.write("\t".join(map(str,[args.prefix,TotalNums,SiteNums,stat_site_nums,Concordance,stat_concordance,Nc,stat_contamination_normal,Tc,stat_contamination_tumor,stat]))+"\n")

def main():
	parser=argparse.ArgumentParser(description=__doc__,
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog='Author:\t{0}\nMail:\t{1}'.format(__author__,__mail__))
	parser.add_argument('--fh',default=99,required=False,type=float,help='The Cutoff High (Minimum) of concordance')
	parser.add_argument('--fl',default=80,required=False,type=float,help='The Cutoff Low (Minimum) of concordance')
	parser.add_argument('--fn',default=10,required=False,type=float,help='The Cutoff (Maximum) of Normal contamination')
	parser.add_argument('--ft',default=0.5,required=False,type=float,help='The Cutoff (Maximum) of Tumor contamination')
	parser.add_argument('--fs',default=100,required=False,type=float,help='The Cutoff (Maximum) of Site Nums')
	parser.add_argument('--concordance',required=True,help='The concordance table is obtained from ConPair')
	parser.add_argument('--contamination',required=True,help='The contamination table is obtained from ConPair')
	parser.add_argument('--outfile','-o',required=True,help='Outfie')
	parser.add_argument('--prefix','-p',required=True,help='Prefix')
	parser.set_defaults(func=ConpairStat)
	args = parser.parse_args()
	args.func(args)

if __name__=="__main__":
	main()

