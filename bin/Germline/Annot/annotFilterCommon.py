import os
import re
import sys
import json


####################################### lib path  #####################################################
B_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(B_DIR,'conf'))
import settings
sys.path.append(settings.LIB_DIR)

#################################### Annot Need Files #################################################
out_all_title_pair = ['Sample','Chr','Start','End','Ref','Alt',
				'GT','Coverage','Ref_Reads','Alt_Reads','Var',
				'N_GT','N_Coverage','N_Ref_Reads','N_Alt_Reads','N_Var',
]

out_all_title_germline = ['Sample','Chr','Start','End','Ref','Alt',
				'GT','Coverage','Ref_Reads','Alt_Reads','Var',
				'Filter','FILTER_flag','QC_flag','Variant_type'
]


#######################################################################################################
''' get variant type '''
def get_variant_type(dat):
	(ch,start,end,ref,alt) = (dat['Chr'],dat['Start'],dat['End'],dat['Ref'],dat['Alt'])
	ref_len = len(ref)
	alt_len = len(alt)
	typ = ''
	if (ref_len == 1 and ref != '-' ) and (alt_len == 1 and alt != '-'):    # A C
		typ = 'snv'
	elif ref == '-' or  alt.startswith(ref):    #-  A   #A  AT  #AT ATAC
		typ = 'ins'
	elif alt == '-' or ref.startswith(alt):     #T  -   #TA T   #TTA    TT
		typ = 'del'
	else :
		typ = 'mnv'
	return(typ)


''' get GATK HaploTyperCaller stat '''
def get_stat_haplotypercaller(title,value):

	format_dic = [
				'GT:AD:DP:GQ:PL',
				'GT:AD:DP:GQ:PGT:PID:PL:PS',
				'GT:AD:AF:DP:F1R2:F2R1:OBAM:OBAMRC:OBF:OBP:OBQ:OBQRC:PGT:PID:PS:SB',
				'GT:AD:AF:DP:F1R2:F2R1:OBAM:OBAMRC:OBF:OBP:OBQ:OBQRC:SB',
				'GT:AD:AF:DP:F1R2:F2R1:OBAM:OBAMRC:PGT:PID:PS:SB',
				'GT:AD:AF:DP:F1R2:F2R1:OBAM:OBAMRC:SB',
	]

	#GT     : AD      :DP    :GQ   :PL  
	#0/1    : 74,281  :402   :99   :7144,0,1756

	title_list 	= title.split(':')
	value_list 	= value.split(':')
	dat_dic 	= dict(zip(title_list,value_list))

	if title in format_dic:
		(ref_depth,alt_depth) = dat_dic['AD'].split(',')
		if dat_dic['DP'] == '0' : 
			var = '0.00%'
		else:
			var = '%.2f' %(float(dat_dic['AF'])*100) + '%' if 'AF' in dat_dic else '%.2f' %(int(alt_depth)/int(dat_dic['DP'])*100) + '%'
	else:
		raise TypeError ('The title : ' + title + ' is error, please check it')

	if dat_dic['GT'] == '0|1' : dat_dic['GT'] = '0/1'
	if dat_dic['GT'] == '1|1' : dat_dic['GT'] = '1/1'
	return(dat_dic['GT'],dat_dic['DP'],ref_depth,alt_depth,var)

''' filter qc germline '''
def filter_qc_germline(min_alt_depth,depth,alt_depth,ratio):
	ratio = float('%.4f' % (float(ratio.strip('%'))/100))
	qc_flag = True if ratio > 0.1 and int(alt_depth) >= min_alt_depth else False
	return(qc_flag)

#######################################################################################################	
''' get title '''
def get_title(typ):
	if typ == 'ALL_Single':
		return(out_all_title_single)
	elif typ == 'ALL_Germline':
		return(out_all_title_germline)
	elif typ == 'ALL_Pair':
		return(out_all_title_pair)
	elif typ == 'SUB':
		return(out_sub_title)
	elif typ == 'TSO500':
		return(out_all_title_single_ts0500)
	elif typ == 'Check':
		return(out_sub_check_title)
	else:
		raise TypeError ('%s is wrong, it must be ALL or SUB not others' %typ)	
		

########################################################################################################
''' write all filter site : to clinic'''
def write_all_filter_site(dat):
	all_filter_flag = False

	if dat['QC_flag'] and dat['Annot_flag'] :
		if dat['Func_flag'] and dat['Exon_func_flag'] : all_filter_flag = True
		if dat['White_flag'] : all_filter_flag = True

	return(all_filter_flag)


''' write all title out '''
def write_out(dat,title_list):
	data_filter_list = []
	for title in title_list:
		if title in dat:
			data_filter_list.append(str(dat[title]))
		else:
			raise TypeError ('<%s> is not in level title' %title)
	return('\t'.join(data_filter_list) + '\n')
