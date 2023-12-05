#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import sys
import os
import re
import glob
import subprocess
import time
bindir = os.path.abspath(os.path.dirname(__file__))

__author__ = 'Cailili'
__mail__ = 'lilicai@chosenmedtech.com'

def Getfastq(pattern,bamlist):
	Bam = [bam for bam in bamlist if re.findall(pattern+".*.bam",bam)]
	if len(Bam) == 0:
		sys.stderr.write("WARNING!!! 目录下没有发现{0}的bam文件\n".format(pattern))
		#exit(1)
	if len(Bam) >=2:
		sys.stderr.write("WARNING!!! 目录下发现{0}的多个bam文件\n".format(pattern))
	bam="".join(Bam)
	return bam

def labinfo2ini(args):
	subprocess.check_call("mkdir -p {0}".format(args.outdir),shell=True)
	bamlist=[]
	for bdir in args.bamdir:
		bamlist.extend(glob.glob(bdir + "/*/*/Map/*.rmdup.sort.bam"))
		bamlist.extend(glob.glob(bdir + "/*/*/*/Map/*.rmdup.sort.bam"))
		bamlist.extend(glob.glob(bdir + "/*.rmdup.sort.bam"))
	project_sh = open(args.outdir + "/Project.sh","w")
	pairdict = {}
	with open(args.libsampleinfo,"r",encoding='utf-8') as f1:
		for n,line in enumerate(f1):
			arr=line.strip().split("\t")
			if line.startswith("序号"):
				header = arr
				continue
			sampinfo = arr ; 
			header2info = dict(zip(header,sampinfo))
			labid_T = header2info["样本编号_肿瘤"]
			labid_N = header2info["样本编号_对照"]
			sampleid = header2info["订单编号"];
			samplebam_T=Getfastq(labid_T,bamlist)
			if not samplebam_T:continue
			samplebam_N=Getfastq(labid_N,bamlist)
			if not samplebam_N:continue
			if sampleid not in pairdict:pairdict[sampleid]={}
			pairdict[sampleid]["T"] = samplebam_T
			pairdict[sampleid]["N"] = samplebam_N
	for sampleid in pairdict:
		sampledir = args.outdir + "/" + sampleid
		subprocess.check_call("mkdir -p {0}/".format(sampledir),shell=True)
		sampleini = open("{0}/{1}/samplelist.ini".format(args.outdir,sampleid),"w")
		sampleini.write("[sample]\n")
		sampleini.write("\t".join([sampleid,pairdict[sampleid]["T"],pairdict[sampleid]["N"]])+"\n")
		sampleini.close()
		configprefix = "config_contamination"
		python3="/software/python3/Python-v3.7.0/bin/python3.7"
		configprefix += ".txt"
		configtxt = "{0}/PairConfig/{1}".format(bindir,configprefix)
		project_sh.write("{4} {0}/pipeline_generate.py -i {3} -o  {1} && {4} {1}/pipeline.py -i {1}/samplelist.ini  -o {1} -name {2} -r -b {0}\n".format(bindir,sampledir,args.name,configtxt,python3))
	project_sh.close()
					
def main():
	parser=argparse.ArgumentParser(description=__doc__,
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog='Author:\t{0}\nMail:\t{1}'.format(__author__,__mail__))
	parser.add_argument('--outdir',help='Output Dir[Required]',required=True)
	parser.add_argument('--libsampleinfo',required=True,help='Laboratory sample information sheet')
	parser.add_argument('--bamdir',nargs='+',required=False,help='bam dir')
	parser.add_argument('--name',required=True,help='Project name')
	parser.set_defaults(func=labinfo2ini)
	args = parser.parse_args()
	args.func(args)

if __name__=="__main__":
	main()

