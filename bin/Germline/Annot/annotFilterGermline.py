import os
import re
import sys
import argparse


sys.path.append(os.path.dirname(__file__))
import annotFilterCommon as aFC


if __name__ == '__main__':

	parser = argparse.ArgumentParser(description = 'Filter GATK HaploTyperCaller Annot Result')
	parser.add_argument('-s', '--sample',help = 'sample name',required = True)
	parser.add_argument('-vcf', '--vcf',help = 'vcf file',required = True)
	parser.add_argument('-d', '--min_alt_depth',help = 'min alt depth', type = int, default = 50)

	args		 	= vars(parser.parse_args())
	sample			= args['sample']
	in_vcf			= args['vcf']
	min_alt_depth	= args['min_alt_depth']
	#clinvar_origin	= args['clinvar_origin']
	o_dir = os.path.dirname(os.path.realpath(in_vcf))	

	''' out file name '''
	f_all_out			= open(o_dir  + '/' + sample + '.Germline.All.Annot.xls','w')
	
	''' print title '''
	out_all_title = aFC.get_title('ALL_Germline')
	f_all_out.write('\t'.join(out_all_title) + '\n')

	### main process ############################################################################
	with open(in_vcf, 'r') as f:
		for line in f:
			if line.startswith("#"):continue
			dat 		= line.strip().split('\t')
			line_dic	= {}
			if dat[3] == '0' or dat[4] == '0' : continue
			
			idd = '_'.join([dat[0],dat[1],dat[1],dat[3],dat[4]])
			line_dic['ID'] 		= idd
			line_dic['Sample']	= sample
			line_dic['IDD'] 	= '_'.join([sample,line_dic['ID']])
			line_dic['Filter']	= dat[6]
			line_dic['Chr']		= dat[0]
			line_dic['Start']	= dat[1]
			line_dic['End']		= int(dat[1])+len(dat[4])-1
			line_dic['Ref']		= dat[3]
			line_dic['Alt']		= dat[4]

			############################## 01 basic information ##################################################
			''' get variant type '''
			line_dic['Variant_type'] = aFC.get_variant_type(line_dic)
	
			''' get FILTER info '''
			line_dic['FILTER_flag'] = True if 'PASS' in line_dic['Filter'] else False	

			############################## 02 stat ###############################################################
			''' get sample stats '''
			stats_info 		= dat[7]
			stats_title 	= dat[8]
			stats_sample 	= dat[9]
			info_list 		= stats_info.split(';')

			(gt,depth,ref_depth,alt_depth,ratio) = aFC.get_stat_haplotypercaller(stats_title,stats_sample)
			line_dic['GT'] 			= gt
			line_dic['Coverage'] 	= depth
			line_dic['Ref_Reads'] 	= ref_depth
			line_dic['Alt_Reads'] 	= alt_depth
			line_dic['Var'] 		= ratio			
			
			############################## 03 filter ###############################################################
			''' qc filter '''
			line_dic['QC_flag'] = aFC.filter_qc_germline(min_alt_depth,depth,alt_depth,ratio)

			############################## 06 write out ############################################################

			''' 06-1 write all the variants to output '''
			f_all_out.write(aFC.write_out(line_dic,out_all_title))

