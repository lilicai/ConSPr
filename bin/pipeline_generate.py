#! /usr/bin/env python3
'''
程序描述：
	在串流程的时候，其实是分为三步的，第一步实现每一个小脚本，第二步把相关的小脚本组合成一个模块，完成一个分析功能；第三步，把这些模块类似搭积木一样，进行组合，得到实现不同目标的流程。
	这个程序，就是在大家得到模块后，帮助排列组合的工具。
参数说明：
	-i ： 输入的配置文件，包含如何组合的规则
	-o ： 输出流程的目录
'''
# -*- coding: utf-8 -*-  
import argparse
import sys
import os
import re
bindir = os.path.abspath(os.path.dirname(__file__))
sys.path.append('{0}/lib'.format(bindir))
import parseConfig

__author__='Cailili'
__mail__= 'lilicai@chosenmed.com'

pat1=re.compile('^\s+$')
pat2=re.compile('\$\((\S+?)\)(\[\d+\])')
pat3 = re.compile('(Para_[A-Za-z0-9_-]+)\\\\?')
pat4 = re.compile('(DB_[A-Za-z0-9_-]+)\\\\?')
ReserveWord = ['OUTDIR','BIN','LOGFILE']
class Job:
	def __init__(self , name ) :#, memory , time, command, export, part):
		self.name = name
		self.Memory = '3G'
		self.Time = '10h'
		self.CPU = '3'
		self.Queue = 'sci.q'
		self.Export = ''
		self.Major = True
		self.Part = ''
		self.Thread = 1
		self.Qsub = True
		self.Node = ''
		self.Depend = []
	def addAtribute(self , key, value):
		if key in ['Name','Memory','Time','CPU','Export','Command','Part','Order','Queue' , 
				    'Thread' , 'Qsub' , 'Node' , 'Description', 'Input' , 'Output' , 'Env']:
			self.__dict__[key] = value
		elif key == 'Major':
			if value == 'T' or value == 'True':
				self.__dict__[key] = 'True'
			elif value == 'F' or value == 'False':
				self.__dict__[key] = 'False'
			else:
				print('Major	{0} is error,set True'.format(value))
		elif key == 'Depend':
			self.Depend = value.split(';')
		else:
			print('{0} is useless'.format(key))
	def format_command(self):
		output = ''
		tt = [] 
		for i in self.Command:
			mm = [] 
			for j in i.split():
				if pat2.search(j):
					j = pat2.sub(r'{\1\2}',j)
				if pat3.search(j):
					j = pat3.sub(r"{para[\1]}",j)
				if pat4.search(j):
					j = pat4.sub(r"{db[\1]}",j)
				for i in ReserveWord:
					j = j.replace(i,'{{{0}}}'.format(i))
				mm.append(j)
			tt.append(" ".join(mm))
		output = "\\n".join(tt) 
		#print(output)
		return [ len(tt),output]
	def output_info(self):
		part = ''
		para = [] 
		db = []
		for i in self.Command:
			if pat2.search(i):
				part = pat2.search(i).group(1)
			if pat3.search(i):
				para += pat3.findall(i)
			if pat4.search(i):
				db += pat4.findall(i)
#				para.append(pat3.search(i).group(1))
		return part,para,db

def ParseOneJob(content):
	'''command should be last attribute of a part
	'''
	cmd = []
	name , memory , time , export ,part = '', '','','' , ''
	for line in content:
		tmp = line.rstrip().split("\t")
		match =  pat2.search(line)
		if part == '' and match: part = match.group(1)
		if len(tmp) == 2 :
			key ,value = tmp[0], tmp[1]
			if key == 'Name':
				name = value
				a_job = Job(name)
			elif key == 'Command':
				#print(value)
				cmd.append(value)
			else:
				a_job.addAtribute(key, value)
		elif len(cmd) > 0 :
				cmd.append(line.rstrip())
	a_job.addAtribute('Command',cmd)
	if part != '':a_job.addAtribute('Part',part)
	#print(type(a_job),a_job.name)
	return a_job

def ReadJob(f_file):
	content = []
	names = []
	job_list = {}
	for line in f_file:
		if line.startswith('#') or re.search(pat1,line):continue
		#tmp = line.rstrip().split("\t")
		if line.startswith(r'[Job Start]'):
			content = []
		elif line.startswith(r'[Job End]'):
			a_job = ParseOneJob(content)
			if a_job.name not in names:
				names.append(a_job.name)
			else:
				print("{0} is repeat , pls use the other name".format(a_job.name))
				sys.exit()
			order = int(a_job.Order)
			if not order in job_list:
				job_list[order] = []
			job_list[order].append(a_job)
		else:
			content.append(line)
	return job_list 

def output(jobs , f_out):
	script = '''
\'''
Parameters:
	-i , --input : 输入的项目配置文件
	-b , --bin : 程序调用的相关程序路径，与流程配置文件中的${BIN}对应
	-t , --thread: 线程数，如果定义了这个，那么会覆盖流程配置文件中的CPU
	-q , --queue : 指定的队列，如果定义了这个，则会覆盖流程配置文件中的队列
	-P , --P : 指定的qsub的Project队列，默认是none，即为普通项目，如果需要加急，可以设置为vip（全小写）
	-o , --outdir: 输出目录，与流程配置文件中的$(OUTDIR)对应
	-name,--name : 任务名称
	-j,   --jobid: 任务前缀，默认为name
	-r,   --run  : 是否自动投递任务，默认为不投递任务，但会在${OUTDIR}/shell中生成脚本，可以进行检查
	-c,   --continue: 在qsub下有效（设置了-r，但不设置-n），如果某一步分析中没有完成全部任务，如果不指定则从头运行该步所有任务，指定则完成该步剩余未完成任务
	-a,   --add   : 是否只运行加测的样品，如果指定则只运行加测的样品。注意的是，-a不可与-c同时使用。如果使用-a，需要将之前的log文件删除干净，否则不会运行任务；
	-quota, --quota : 分析目录的配额，是之前找文明申请的大小。默认是1000G，请根据实际情况进行调整。
\'''
#! /usr/bin/env python3
# -*- coding: utf-8 -*-  
import argparse
import sys
import os
import re
bindir = os.path.abspath(os.path.dirname(__file__))
sys.path.append('{0}/lib'.format(bindir))
import parseConfig
import JobGuard
import subprocess

__author__='Cailili'
__mail__= 'lilicai@chosenmed.com'

pat1=re.compile('^\s+$')

def main():
	parser=argparse.ArgumentParser(description=__doc__,
			formatter_class=argparse.RawDescriptionHelpFormatter,
			epilog='author:\\t{0}\\nmail:\\t{1}'.format(__author__,__mail__))
	parser.add_argument('-i','--input',help='input file',dest='input',type=open,required=True)
	parser.add_argument('-b','--bin',help='bin dir',dest='bin',default=os.path.dirname(bindir))
	parser.add_argument('-t','--thread',help='thread number ',dest='thread',type=int)
	parser.add_argument('-q','--queue',help='computer queue name ',dest='queue')
	parser.add_argument('-P','--P',help='Project in qsub ',dest='qsub_P' , default='none')
	parser.add_argument('-o','--outdir',help='output file',dest='outdir',required=True)
	parser.add_argument('-name','--name',help='project name',dest='name',required=True)
	parser.add_argument('-j','--jobid',help='job id prefix',dest='jobid',default='')
	parser.add_argument('-r','--run',help='run script file',dest='run',action='store_true')
	parser.add_argument('-c','--continue',help='continue unfinish job in each shell',dest='continues',action='store_true')
	#parser.add_argument('-n','--nohup',help='qsub or nohup mission',dest='nohup',action='store_true')
	parser.add_argument('-quota','--quota',help='disk quota ',dest='quota',default = '1000G')
	parser.add_argument('-a','--add',help='add sequencing sample process, True -- only run added sequence sample ,False* -- run all samples',dest='add',action='store_true')
	args=parser.parse_args()

	OUTDIR = parseConfig.getab(args.outdir)
	BIN=os.path.realpath(args.bin)
	LOGFILE = '{0}/log.txt'.format(OUTDIR)
	
	#cmdrm = "rm  {0}/data/Analysis* ".format(OUTDIR)
	#subprocess.call(cmdrm , shell=True)

	job_not_continue = ' -nc '
	if args.continues : job_not_continue = ' '

	if args.jobid == '' : args.jobid = args.name
	config ,para, db , orders  = parseConfig.ReadConfig(args.input)
	shell_dir = '{0}/shell/'.format(OUTDIR)
	parseConfig.makedir(shell_dir)
	logfile = '{0}/log.txt'.format(shell_dir)
	finish_obj = JobGuard.ReadLog(logfile)
	log = open(logfile,'a')
	log.write('#pipeline version : {0}\\n'.format(BIN))
	guard_script = '{0}/guard.py'.format(shell_dir)
	job_list = {}
	all_job_list = {}
'''

	for order in sorted(jobs):
		for count , a_job in  enumerate(jobs[order]):
			index = '{0}_{1}'.format(order , count)
			if a_job.Part == '':
				script += '''
	shsh = '{{0}}/v{0}_{1.name}.sh'.format(shell_dir)
	with open(shsh , 'w') as f_out:
		cmds = []
		cpu = parseConfig.cpu(args.thread , 1 , '{1.CPU}' )
		queue = parseConfig.queue(args.queue , '{1.Queue}')
		cmds.append('{2[1]}'.format( para = para, OUTDIR = OUTDIR , BIN = BIN , db = db , LOGFILE = LOGFILE ))
		f_out.write('\\n'.join(sorted(set(cmds))) + '\\n')
	if not {1.Qsub} :
		if "{1.Node}" == '':
			a_cmd = 'perl {{1}}/src/multi-process.pl -cpu {{2}} --lines {2[0]} {{0}}'.format(shsh , bindir, cpu)
		else :
			a_cmd = 'ssh {1.Node} 2> /dev/null "perl {{1}}/src/multi-process.pl -cpu {{2}} --lines {2[0]} {{0}}"'.format(shsh , bindir, cpu)
	else:
		a_cmd = '{{1}}/src/qsub_sge --resource vf={1.Memory}  --queue {{4}}  {{0}}'.format(shsh , bindir, cpu , args.jobid , queue , job_not_continue , args.qsub_P)
	if len( {1.Depend} ) == 0 : 
		a_thread = JobGuard.MyThread('{0}_{1.name}' , log , a_cmd, {1.Major})
	else : 
		a_thread = JobGuard.MyThread('{0}_{1.name}' , log , a_cmd, {1.Major} , [ all_job_list[i] for i in {1.Depend} ])
	all_job_list[ '{1.name}' ] = a_thread
	if not int({3}) in job_list: job_list[int({3})] = []
	job_list[int({3})].append(a_thread)
'''.format(index ,  a_job , a_job.format_command() , order )
			else:
				#print(a_job.name)
				script += '''
	run_sample = config['{1.Part}']
	pre_job_count = 0 
	if args.add :
		run_sample , pre_job_count = parseConfig.chooseSamples(run_sample, orders['{1.Part}'])
	#print(run_sample)
	if len(run_sample) > 0 :
		shsh = '{{0}}/v{0}_{1.name}.sh'.format(shell_dir)
		with open(shsh, 'w') as f_out:
			cmds = []
			cpu = parseConfig.cpu(args.thread , len(run_sample), '{1.CPU}' )
			queue = parseConfig.queue(args.queue , '{1.Queue}')
			for {1.Part} in sorted(run_sample):
				cmds.append('{2[1]}'.format(para=para , {1.Part} ={1.Part} ,OUTDIR=OUTDIR, BIN=BIN,db=db,LOGFILE=LOGFILE) )
			f_out.write("\\n".join(sorted(set(cmds))) + '\\n')
		if not {1.Qsub} :
			if "{1.Node}" == '':
				a_cmd = 'perl {{1}}/src/multi-process.pl -cpu {{2}} --lines {2[0]} {{0}}'.format(shsh , bindir, cpu)
			else:
				a_cmd = 'ssh {1.Node} 2> /dev/null "perl {{1}}/src/multi-process.pl -cpu {{2}} --lines {2[0]} {{0}}"'.format(shsh , bindir, cpu)
		else:
			a_cmd = '{{1}}/src/qsub_sge --resource vf={1.Memory}  --queue {{4}} {{0}}  '.format(shsh ,bindir, cpu, args.jobid , queue , job_not_continue , args.quota)
		if len( {1.Depend} ) == 0 : 
			a_thread = JobGuard.MyThread('{0}_{1.name}' , log , a_cmd, {1.Major})
		else : 
			a_thread = JobGuard.MyThread('{0}_{1.name}' , log , a_cmd, {1.Major} , [ all_job_list[ i ] for i in {1.Depend} ])
		all_job_list[ '{1.name}' ] = a_thread
		if not int({3}) in job_list: job_list[int({3})] = []
		job_list[int({3})].append(a_thread)
	else:
		print("{{0}} is empty".format("config['{1.Part}']"))
'''.format(index ,  a_job , a_job.format_command(), order)

	script +='''
	home_dir = os.environ['HOME']
	parseConfig.makedir('{0}/.mission'.format(home_dir))
	if not os.path.isfile('{0}/.mission/.pipeline.log'.format(home_dir)):
		os.system('touch {0}/.mission/.pipeline.log'.format(home_dir))
	
	tag = 0 
	with open('{0}/.mission/.pipeline.log'.format(home_dir),'r') as super_log:
		for line in super_log:
			if line.startswith('#') or re.search(pat1,line):continue
			tmp = line.rstrip().split()
			if tmp[0] == args.name:
				tag = 1
				if tmp[1] == os.path.abspath(args.outdir):
					tag = 2
	
	if tag == 0 : 
		with open('{0}/.mission/.pipeline.log'.format(home_dir),'a') as super_log:
			super_log.write('{0}\\t{1}\\n'.format(args.name , os.path.abspath(args.outdir)))
	elif tag == 2 :
		print("\033[1;31;40m" + "Warings: {0} was existed already in your log file, please check it".format(args.name) + "\033[0m")
	elif tag == 1 :
		print("\033[1;31;40m" + "Warings: {0} was existed already in your log file,  and have different analysis directory , we should add this new dir at the end of log file ,please check it".format(args.name) + "\033[0m")
		with open('{0}/.mission/.pipeline.log'.format(home_dir),'a') as super_log:
			super_log.write('{0}\\t{1}\\n'.format(args.name , os.path.abspath(args.outdir)))
	
	job_list = JobGuard.RemoveFinish(job_list,finish_obj)
	if args.run == True:
		JobGuard.run(job_list , log , OUTDIR)
	log.close()

if __name__ == '__main__':
	main()
'''
	f_out.write(script)

def output_config(jobs, f_para):
	region = []
	paras = []
	dbs = []
	#db_part = {}
	#para_part = {}
	dbs_output = ''
	paras_output = ''
	#print(jobs)
	for i in sorted(jobs):
		for a_job in jobs[i]:
			dbs_output += '#{0.name}\n'.format(a_job)
			paras_output += '#{0.name}\n'.format(a_job)
			a_region , para ,db  = a_job.output_info()
			if not a_region == '': region.append(a_region)
			#paras += para
			for a_db in db :
				if not a_db in dbs :
					dbs_output += '{0}=\n'.format(a_db)
					dbs.append(a_db)
			for a_para in para:
				if not a_para in paras:
					paras_output += '{0}=\n'.format(a_para)
					paras.append(a_para)
#			dbs += db
	for i in list(set(region)):
		f_para.write('[{0}]\n'.format(i))
	f_para.write('[Para]\n')
	#for i in list(set(paras)):
	#	f_para.write('{0}=\n'.format(i))
	f_para.write(paras_output)
	f_para.write('[DB]\n')
	#for i in list(set(dbs)):
	#	f_para.write('{0}=\n'.format(i))
	f_para.write(dbs_output)

def main():
	parser=argparse.ArgumentParser(description=__doc__,
			formatter_class=argparse.RawDescriptionHelpFormatter,
			epilog='author:\t{0}\nmail:\t{1}'.format(__author__,__mail__))
	parser.add_argument('-i','--input',help='input file',dest='input',type=open,required=True)
	#parser.add_argument('-c','--config',help='config example file',dest='config',type=open,required=True)
	parser.add_argument('-o','--outdir',help='outdir',dest='outdir',required=True)
	#parser.add_argument('-p','--para',help='output para file',dest='para',type=argparse.FileType('w'),required=True)
	args=parser.parse_args()

	jobs = ReadJob(args.input)
	parseConfig.makedir(args.outdir)
	with open('{0}/pipeline.py'.format(args.outdir),'w') as f_output:
		output(jobs , f_output)
	with open('{0}/config_example.txt'.format(args.outdir),'w') as f_output:
		output_config(jobs , f_output) 
	os.popen('cp -r {0}/lib {0}/src {1}'.format(bindir,args.outdir))

if __name__ == '__main__':
	main()
