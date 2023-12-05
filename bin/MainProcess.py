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
sys.path.append('{0}/lib'.format(bindir))
import parseConfig
import JobGuard

__author__ = 'Cailili'
__mail__ = 'lilicai@chosenmedtech.com'


def MainProcess(args):
	analysisdir = args.outdir+"/Analysis"
	bamdir = " ".join(args.bamdir)
	parameter = ""
	a_cmd = "python3 {0}/labinfo2ini.py --outdir  {1} --libsampleinfo  {2} --bamdir  {3} --name  {4} {5}".format(bindir,analysisdir,args.libsampleinfo,bamdir,args.name,parameter)
	print(a_cmd+"\n")
	subprocess.check_call(a_cmd,shell=True)
	a_cmd = 'perl {0}/src/multi-process.pl -cpu {1} {2}/Project.sh'.format(bindir,args.cpu,analysisdir)
	print(a_cmd+"\n")
	subprocess.check_call(a_cmd,shell=True)

def main():
	parser=argparse.ArgumentParser(description=__doc__,
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog='Author:\t{0}\nMail:\t{1}'.format(__author__,__mail__))
	parser.add_argument('--outdir',help='Output Dir[Required]',required=True)
	parser.add_argument('--libsampleinfo',required=True,help='Laboratory sample information sheet')
	parser.add_argument('--bamdir',nargs='+',required=False,help='Bam dir')
	parser.add_argument('--cpu',required=False,default=20,type=int,help='The maximum number of samples to be delivered.')
	parser.add_argument('-name','--name',help='project name',dest='name',required=True)
	parser.set_defaults(func=MainProcess)
	args = parser.parse_args()
	args.func(args)

if __name__=="__main__":
	main()

