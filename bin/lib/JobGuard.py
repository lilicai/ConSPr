import threading
import time
import queue
import subprocess
import sys
import os
import re
import signal

def myTime():
	return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 


class MyThread(threading.Thread):
	def __init__(self ,  thread_name , logfile, cmd , major , depend = [] ):
		threading.Thread.__init__(self)
		#self.lock = lock
		self.name = thread_name
		self.cmd = cmd
		self.logfile = logfile
		self.major = major
		self.status = 'waiting' 
		self.depend = depend
	def run(self):
		#self.lock.acquire()
		self.logfile.write('[start]: {0} start at {1}\n'.format(self.name , myTime()))
		self.logfile.flush()
		print(self.cmd)
		if subprocess.call(self.cmd , shell=True) != 0 : 
			self.logfile.write('[break]: {0} break down at {1}\n'.format(self.name , myTime()))
			self.logfile.flush()
			self.status = 'break'
			#sys.exit()
		#if self.status == True:
		else:
			self.logfile.write('[finish]: {0} finish at {1}\n'.format(self.name , myTime()))
			self.logfile.flush()
			self.status = 'finish'
		#self.lock.release()

def run(jobs , logfile , OUTDIR):
	cmdfinish = "mkdir -p {0}/data/ && touch {0}/data/Analysis.Finish".format(OUTDIR)
	cmderror = "mkdir -p {0}/data/ && touch {0}/data/Analysis.Failure".format(OUTDIR)
	for order in sorted(jobs):
		break_list = []
		m = []
		for a_job in jobs[order]:
			if a_job.status == 'finish' : continue
			for pre_job in a_job.depend:
				while not pre_job.status == 'finish': 
					if pre_job.status == 'waiting':
						time.sleep(300)
					elif pre_job.status == 'break' :
						pre_job.logfile.write('#{0} break, Sorry,goodbye\n'.format(pre_job.name))
						subprocess.call(cmderror , shell=True)
						sys.exit("{0} break, Sorry,goodbye".format(pre_job.name))
						#sys.exit("Sorry,goodbye")
			a_job.start()  
			if a_job.major == True : m.append(a_job)
		for a_job in m:
			a_job.join()
			time.sleep(60)
		for a_job in jobs[order]:
			if a_job == '' : continue
			if a_job.status == 'break' :
				a_job.logfile.write('#{0} break, Sorry,goodbye\n'.format(a_job.name))
				subprocess.call(cmderror , shell=True)
				if a_job in m :
					break_list.append(a_job.name)
				else :
					pass
		if len(break_list) > 0 : 
			subprocess.call(cmderror , shell=True)
			sys.exit("{0} break, Sorry,goodbye\n".format("|".join(break_list)))
	logfile.write('[done]: all analysis finish at {0}\n'.format(myTime()))
	subprocess.call(cmdfinish , shell=True)
	

def RemoveFinish(jobs, finish):
	for order in jobs:
		for count, a_job in enumerate(jobs[order]):
			if a_job.name in finish:
				a_job.status='finish'
	return jobs

def ReadLog(logfile):
	pat1 = re.compile('^\s+$')
	finish = []
	if not os.path.isfile(logfile):
		return finish
	else:
		with open(logfile,'r') as f_file:
			for line in f_file:
				if line.startswith('#') or re.search(pat1,line):continue
				tmp=line.rstrip().split()
				if line.startswith('[finish]:'):
					finish.append(tmp[1])
		return finish

def signal_term_handler(signal , frame , logfile ):
	logfile.write('[break]: system was break down at {0}\n'.format( myTime()))
	sys.exit(0)




