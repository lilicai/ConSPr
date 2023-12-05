# ConSPr

Contamination Source Predictor（ConSPr）: A software for contamination purity estimation, contamination genotype prediction, and contamination source tracing

ConSPr is a fast and robust method designed for cross-individual contamination level estimation, contamination source genotype inference and contamination source finding in customized panel experiments. Importantly, our method of estimating contamination in the tumor samples is not affected by copy number changes and is able to detect contamination levels as low as 1%,and When the pollution source is a single sample and the pollution proportion exceeds 5%, the pollution source can be accurately identified.

* Version: 1.0.0
* Author: cailili
* Contact: lilicai@chosenmedtech.com

**Required input files:** two bam files (tumor, normal)

**Required software:** GATK 3 and GATK 4 , Conpair,python 3 , scipy, numpy, pandas,java

**Required data:** Human genome file (GRCh37,GRCh38) ,bed,dbsnp


GRCh37:

The fasta file can be downloaded from: ftp://ftp.1000genomes.ebi.ac.uk/vol1/ftp/technical/reference/human_g1k_v37.fasta.gz  

In order to be able use the fasta file as a reference 2 additional files are required:`human_g1k_v37.dict`, `human_g1k_v37.fa.fai`  

To create these files please follow: http://gatkforums.broadinstitute.org/gatk/discussion/1601/how-can-i-prepare-a-fasta-file-to-use-as-reference

The dbSNP file can be download from:
ftp:/gsapubftp-anonymous@ftp.broadinstitute.org/bundle/hg19/dbsnp 138.hg19.vcf.gz

GRCh38:

The fasta file can be downloaded from: http://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.fa.gz

In order to be able use the fasta file as a reference 2 additional files are required:`hg38.dict`, `hg38.fa.fai`

To create these files please follow: http://gatkforums.broadinstitute.org/gatk/discussion/1601/how-can-i-prepare-a-fasta-file-to-use-as-reference

The dbSNP file can be download from:ftp:/gsapubftp-anonymous@ftp.broadinstitute.org/bundle/hg38/dbsnp_138.hg38.vcf.gz

# Manual

**Dependencies:**
* perl 5.28.1 or higher
* python 3.8.8 or higher
* numpy 1.7.0 or higher 
* scipy 0.14.0 or higher 
* pandas 1.2.4 or higher
* GATK 3.7
* GATK 4.1.9.0 or higher  
* java 1.8.0_202 or higher
* conpair  [https://github.com/nygenome/Conpair]

**Modify Configuration file:**
```
vi  ConSPr/bin/Config_Contamination.txt
PERL = ${your_perl}
PYTHON3 = ${your_python3}
JAVA=${your_java}
gatk=${your_gatk3}
GATK=${your_gatk4}
ref=${your_genome_dir}/human_g1k_v37.fasta
ref_fai=${your_genome_dir}/human_g1k_v37.fasta.fai
ref_dict=${your_genome_dir}/human_g1k_v37.dict
ref_2bit=${your_genome_dir}/human_g1k_v37.fasta.2bit
realign_599=${your_file_dir}/align.bed
realign_autoChr=${your_file_dir}/autoChr.bed
dbsnp=${your_file_dir}/dbsnp_138.hg19.vcf
baseline=${your_file_dir}/compair.vcf
```

**Write Samplelist:**
In order to ensure that the input bam file can be found, please link the bam file to a directory, and the bam file suffix is sample_T.rmdup.sort.bam
```
序号  订单编号	样本编号_肿瘤	样本编号_对照
1     Prefix_N  Sample_T        Sample_N
```


**Most common usage and additional options:**   
To run ConSPr:
```
$(python3) ${ConSPr}/bin/MainProcess.py --outdir ${outdir} --libsampleinfo  Samplelist --bamdir  ${bam_dir} --name 20231030
Optional:
--help                               show help message and exit
--outdir OUTDIR                      Output Dir[Required]
--libsampleinfo LIBSAMPLEINFO        Laboratory sample information sheet
--cpu CPU                            The maximum number of samples to be delivered.
--name NAME                          project name

```

Searching for sources of contamination in a library of candidate contamination samples:

```  
${python3} ${ConSPr}/bin/Source/find.py --outdir ${outdir} --baseline ${baseline} --prefix ${prefix} --pollution ${pollutionfile} --indir ${candidate_database} --pollutionCutoff ${pollutioncutoff}

Optional:
--help                                show help message and exit
--outdir OUTDIR                       Outdir
--baseline BASELINE                   Dir of model file 
--prefix PREFIX                       file name
--pollution POLLUTION                 Pollution_Genetype_file
--indir INDIR                         normal germline files
--pollutionCutoff POLLUTIONCUTOFF     pollution sources cutoff default 0.9 
```  

**Contamination**  
```
An example of a contamination file can be viewed here: ([`contamination.stat.xls`](${ConSPr}/example/sample1/sample1/Pair/Contamina/Conpair/sample1_contamination.stat.xls)). 
```

**Contamination Genotype**
```
An example of a genetype file can be viewed here: ([`pollution.change.genetype.xls`](ConSPr/example/sample1/sample1/Pair/Genotype/sample1.sample.pollution.change.genetype.xls)).
```

**Contamination Source**
```
An example of a pollution sample source file can be viewed here: ([`pollution.source_result.xls`](ConSPr/example/sample1/source/sample.pollotion.source_result.xls)).
```


