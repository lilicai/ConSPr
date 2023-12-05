#!/usr/bin/perl

##  multi-process.pl -- control processes running with specified CPU number, 
##	read command from a file, each process can have more than one orderd
##	commands, but they should be put in the same one line, seperated by 
##	semicolon, for example: echo hello; sleep 3; perl test.pl; 

# Author: Fan Wei, fanw@genomics.org.cn

## Date: 2007-1-18

## 本程序的核心想法来源于李俊。
## 注意调用fork的时候非常危险，请万勿随意修改，本程序曾把北京的大型机搞死过两次。

## log
# 1. add renohup function 
#
use strict;
use Getopt::Long;
use Data::Dumper;


my $program_name=$1 if($0=~/([^\/]+)$/);
my $usage=<<USAGE; #******* Instruction of this program *********# 

Program: control multiple processes running

Usage: perl $program_name  <command_file>  
	-cpu <int>	number of CPU to use, default=3
	-cmd		output the commands but not execute
	--lines <num>     set number of lines to form a job, default 1
	-verbose	output information of running progress
	-help		output help information to screen

USAGE

my %opts;
GetOptions(\%opts, "cpu:s","cmd!","verbose!","help!" , "lines:s");
die $usage if ( @ARGV==0 || defined($opts{"help"}));

#****************************************************************#
#--------------------Main-----Function-----Start-----------------#
#****************************************************************#

#my$Lines = $opts{"lines"} || 1 ;
my$Lines = 1;

my $owner = `whoami`;

my $work_shell = $ARGV[0];
my $work_shell_file_error = $work_shell.".$$.log";
my $work_shell_dir = $work_shell.".$$.shell";
`mkdir -p $work_shell_dir` unless ( -d $work_shell_dir);

open IN, $work_shell ||die "cannot open $work_shell\n";
my @cmd;
my $line_mark = 0;
my $single_cmd = ''; 
while (<>) {
	chomp;
	s/&$//g;
	next if(! /\S+/);
	if ($line_mark % $Lines == 0) {
		$single_cmd = ""
	}
	$single_cmd .= "$_ &&  ";
	if ($line_mark % $Lines == $Lines - 1) {
		push @cmd, $single_cmd;
	}
	$line_mark++;
}
close IN;

my @cmd2 ; 
my $count = "00000" ; 
foreach my$i(@cmd){
	$count ++ ;
	open OUT,">$work_shell_dir/work_$count.sh"||die "cannot open $work_shell_dir/work_$count.sh";
	print OUT "$i echo This-Work-is-Completed!\n" ;
	close OUT ;
	push @cmd2 , "$work_shell_dir/work_$count.sh" ;
}

if(exists $opts{cmd}){
	foreach  (@cmd) {
		print $_."\n";
	}
	exit;
}

Multiprocess(\@cmd2, $work_shell_file_error , $opts{cpu}  );



#****************************************************************#
#------------------Children-----Functions-----Start--------------#
#****************************************************************#

##use mutiple CPUs at the same time
#########################################
sub Multiprocess{
	my $cmd_ap = shift;
	my $work_shell_file_error = shift;
	my $max_cpu = shift || 3; 
	my $total = @$cmd_ap;
	my$finish_num = 0;
	open LOG ,">>$work_shell_file_error" || die "cannot open $work_shell_file_error\n";
	print STDERR "\n\tcmd num:  $total\n\tcpu num:  $max_cpu\n\n" if ( exists $opts{verbose} );

	my %report;
	for (my $i=1; $i<=10; $i++) {
		$report{int $total/10*$i}=$i*10;
	}
	my $unfinish_flag = 0; 
	pipe(READ, WRITE); 
	for (my $i=0; $i<$total; $i++) {
		printf STDERR ("\tthrow out  %d\%\n",$report{$i+1}) if (exists $opts{verbose} && exists $report{$i+1});
		my $cmd=$$cmd_ap[$i];
		if ( fork() ) { 
			wait if($i+1 >= $max_cpu); ## wait unitl all the child processes finished
		}else{
			my $count = 0 ;
			while ($count < 5){
				if ( system ( "sh $cmd 1>$cmd.o$count 2>$cmd.e$count")){
					$count ++ ; 
					print LOG "[Process]: $cmd  $finish_num/$total failed , repeat $count time\n";
				}else{
					print WRITE "finish\t" ;
					$count = 10 ;
				}
			}
			exit;     #child process
		}
		sleep 1;
	}
	while (wait != -1) { sleep 1; }
	close WRITE;
	$unfinish_flag = <READ>;
	$finish_num += scalar(split(/\s+/, $unfinish_flag) );
	print LOG "[Process]: $finish_num/$total finished\n";
	close LOG;
	close READ; 
	if ( $finish_num == $total  ){
		print STDERR "\tAll tasks done\n" if ( exists $opts{verbose} );
	}else {
		print STDERR " some script was break\n";
		die;
	}
}
