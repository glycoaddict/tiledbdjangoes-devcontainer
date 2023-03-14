from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

import pandas as pd
import numpy as np
from typing import List
import warnings
import configparser
import tiledbvcf as tv
import json
import re
import logging
import os
import datetime

from annoquery.models import Clinvars, Snps, Genes
from .utils.genotypeops import rowloop_index_a_with_b


logger = logging.getLogger('django')
logger.setLevel(logging.INFO)

config = configparser.ConfigParser()
config.read('staticfiles/tilequery/config.ini')
MEMORY_BUDGET_MB=int(config['TILEDB'].get('MEMORY_BUDGET_MB', '32000'))
URI=str(config['TILEDB'].get('URI', '/mnt/data/tileprism'))

# persistent vars:
pathogenic_vars = ['chr17:43124028-43124029', 'chr13:32340301-32340301', 'chr7:117559591-117559593', 'chr13:20189547-20189547', 'chr12:112477719-112477719', 'chr16:8811153-8811153', 'chr1:216247118-216247118', 'chr11:66211206-66211206', 'chr19:11116928-11116928', 'chr15:89327201-89327201', 'chrX:154030912-154030912', 'chr10:110964362-110964362', 'chr22:50627165-50627165', 'chr18:51078306-51078306', 'chr9:101427574-101427574', 'chr13:51944145-51944145', 'chr16:23636036-23636037', 'chr11:6617154-6617154', 'chr3:12604200-12604200', 'chr10:87933147-87933147', 'chr11:534289-534289', 'chr16:3243447-3243447', 'chr12:102840507-102840507', 'chr17:7674220-7674220', 'chr18:31592974-31592974', 'chr11:108251026-108251027', 'chr12:76347713-76347714', 'chr7:92501562-92501562', 'chr9:37783993-37783993', 'chr14:23426833-23426833', 'chr15:72346579-72346580', 'chr11:5226774-5226774', 'chr11:47337729-47337730', 'chr4:1801837-1801837', 'chr1:45331219-45331221', 'chr12:32802557-32802557', 'chr2:47803500-47803501', 'chr11:64759751-64759751', 'chr6:43007265-43007265', 'chr5:112839515-112839519', 'chr19:41970405-41970405', 'chr15:66436843-66436843', 'chr7:140801502-140801502', 'chr3:81648854-81648854', 'chr17:42903947-42903947', 'chr2:26195184-26195184', 'chr4:987858-987858', 'chr17:7222272-7222272', 'chr1:9726972-9726972', 'chr7:5986933-5986934', 'chr12:101753470-101753471', 'chr6:32040110-32040110', 'chr3:179234297-179234297', 'chr2:47414421-47414421', 'chr13:31269278-31269278', 'chr10:121520163-121520163', 'chr7:107683453-107683453', 'chr6:136898213-136898213', 'chr16:30737370-30737370', 'chr16:16163078-16163078', 'chr2:28776944-28776944', 'chr3:37047632-37047634', 'chr17:31214524-31214524', 'chr15:80180230-80180230', 'chr17:80118271-80118271', 'chr15:42387803-42387803', 'chr17:80212128-80212128', 'chr15:23645746-23645747', 'chr6:73644583-73644583', 'chr19:18162974-18162974', 'chrX:111685040-111685040', 'chr2:39022774-39022774', 'chr15:90761015-90761015', 'chr18:23536736-23536736', 'chr6:161785820-161785820', 'chr17:50167653-50167653', 'chr9:95172033-95172033', 'chr2:61839695-61839695', 'chr4:3493106-3493107', 'chr9:34649032-34649032', 'chr1:94029515-94029515', 'chr17:6425781-6425781', 'chr4:186274193-186274193', 'chr2:73914835-73914835', 'chr10:54317414-54317414', 'chr19:35831056-35831056', 'chr7:151576412-151576412', 'chr17:35103298-35103298', 'chr19:12649932-12649932', 'chr19:50323685-50323685', 'chr9:108899816-108899816', 'chr11:17531408-17531409', 'chr17:17216394-17216395', 'chr17:3499000-3499000', 'chr11:2167905-2167905', 'chr10:100749771-100749772', 'chrX:153932410-153932410', 'chr14:28767732-28767733', 'chr15:63060899-63060899', 'chr4:15567676-15567676']
LATEST_COUNT = 0

# VCF header translation table
VCF_TRANSLATE = {
    'fmt_GT':'Genotype',
}

QUERY_OPTION = 'tilequery/query.html'

CHR_DICT_STR_TO_INT = {'chr1': 1, 'chr2': 2, 'chr3': 3, 
                       'chr4': 4, 'chr5': 5, 'chr6': 6, 
                       'chr7': 7, 'chr8': 8, 'chr9': 9, 
                       'chr10': 10, 'chr11': 11, 'chr12': 12, 
                       'chr13': 13, 'chr14': 14, 'chr15': 15, 
                       'chr16': 16, 'chr17': 17, 'chr18': 18, 
                       'chr19': 19, 'chr20': 20, 'chr21': 21, 
                       'chr22': 22, 'chrX': 23, 'chrY': 24}

CLINVAR_FIELDS = [f.name for f in Clinvars._meta.get_fields()]

CLINVAR_SEARCH_LIMIT = 0
SNP_SEARCH_FLAG = True
OVERALL_SEARCH_LIMIT = 1000

# pre-fetch the help file
def prefetch_helper_dataset():
    p = './DF_COMPOSER_prefetched.pkl'
    if os.path.exists(p):
        DF_COMPOSER = pd.read_pickle(p) 
    else:
        cfg = tv.ReadConfig(memory_budget_mb=MEMORY_BUDGET_MB)
        DS = tv.Dataset(URI, mode='r', cfg=cfg, verbose=False) 
        DF_COMPOSER = pd.DataFrame([f'{",".join(DS.attributes())}', f'{",".join(DS.samples())}'], 
                                columns=['property'], 
                                index=['attributes', 'samples'])
        DF_COMPOSER.to_pickle(p)
        
    return DF_COMPOSER

DF_COMPOSER = prefetch_helper_dataset()

# Create your views here.

@login_required
def index(request, methods=['GET', 'POST']): 

    def return_with_error(e:Exception, query_summary=None):
            warnings.warn(e.__str__())
            messages.add_message(request, messages.WARNING, e.__str__())
            context=dict(query_summary=query_summary)
            return render(request, QUERY_OPTION, context)
    
    if request.method == 'POST':     

        time_start = datetime.datetime.now()
        
        regions=request.POST.get('regions').split(',')
        samples=request.POST.get('samples').split(',')
        attrs=request.POST.get('attrs').split(',')
        clinvar_flag=request.POST.get('clinvar', False)
        hidenonvariants_flag=request.POST.get('hidenonvariants', False)
        genelist_flag=request.POST.get('genelist', False)
        
        if all([x=='' for x in regions]) and (all([x=='' for x in samples]) if samples else True):
            w  = '<_query_tiledb> regions:List[str] must not be empty strings. Returning the possible samples and attributes you may query.'
            e = ValueError(w)
            df_help = _help_tiledb(request)             
            return return_with_error(e, query_summary=df_help.style.pipe(style_result_dataframe).to_html())       
        elif all([x=='' for x in regions]):
            regions = pathogenic_vars            
            messages.add_message(request, messages.WARNING, 'Region unspecified but samples specified, so a list of pathogenic variants from clinvar was substituted.')
            
        # GENERATE QUERY SUMMARY
        query_summary = pd.DataFrame([",".join(regions), ",".join(samples), ",".join(attrs)], columns=['query'], index=['regions', 'samples', 'attributes'])

        # THE TILEDB SEARCH STARTS HERE        
        try:
            df = _query_tiledb(request, regions=regions, samples=samples, attrs=attrs, 
                               clinvar_flag=clinvar_flag, 
                               hidenonvariants_flag=hidenonvariants_flag,
                               genelist_flag=genelist_flag,
                               )
            df.index.name = 'S/N'
        except Exception as e:
            return return_with_error(e, query_summary=query_summary.style.pipe(style_result_dataframe).render())

        df = dataframe_common_final_reformat(df)

        time_end = datetime.datetime.now()
        elapsed_seconds = (time_end - time_start).seconds
        query_summary.loc['query_details'] = [f'time={elapsed_seconds} secs | SNP search={SNP_SEARCH_FLAG} | Clinvar search={clinvar_flag} | HideNonVariants={hidenonvariants_flag} | clinvar_limit={CLINVAR_SEARCH_LIMIT} | overall_limit = {OVERALL_SEARCH_LIMIT}']

        ### STYLE ####       
        final_content = df.style.pipe(style_result_dataframe).to_html()
        ##############
        context =  dict(answer=final_content, 
                        query_summary=query_summary.style.pipe(style_result_dataframe).to_html(), 
                        )
        return render(request, QUERY_OPTION, context)
        
    else:            
        return render(request, QUERY_OPTION)    

# class tiledb:
#     def __init__(self, uri:str=URI, memory_budget_mb:int=MEMORY_BUDGET_MB) -> None:
#         # load database        
#         cfg = tv.ReadConfig(memory_budget_mb=memory_budget_mb)
#         self.ds = tv.Dataset(uri, mode='r', cfg=cfg, verbose=True)   
        
#         pass

#     def _query_tiledb(self, regions:List[str],
#                   samples:Union[None, List[str]],
#                   attrs:List[str]=['sample_name', 'alleles', 'fmt_GT', 'contig', 'pos_start'],                   
#                   )->pd.DataFrame:

#         df = self.ds.read(attrs=attrs, regions=regions, samples=samples)
#         return df

# @login_required
def _query_tiledb(request,
                  regions:List[str],
                  samples:List[str],
                  attrs:List[str]=['sample_name', 'id', 'alleles', 'fmt_GT', 'contig', 'pos_start', 'pos_end', 'info_AF'],
                #   attrs:Union[None, List[str]]=['sample_name', 'alleles', 'fmt_GT', 'contig', 'pos_start'], 
                  uri:str=URI, 
                  memory_budget_mb:int=MEMORY_BUDGET_MB,
                  clinvar_flag=False,
                  hidenonvariants_flag=False,
                  genelist_flag=False,
                  )->pd.DataFrame:

    flags = {'clinvar_flag':clinvar_flag,
             'hidenonvariants_flag':hidenonvariants_flag,
             'genelist_flag':genelist_flag,
             }

    # if regions and sample are empty, return error
    # if regions empty but sample not empty, substitute the pathogenic var list.
    # if regions specified and sample specified, proceed as normal to extract all samples.
    
    cfg = tv.ReadConfig(memory_budget_mb=memory_budget_mb)
    ds = tv.Dataset(uri, mode='r', cfg=cfg, verbose=False)   
    df = ds.read(attrs=attrs, regions=regions, samples=samples)

    messages.add_message(request, messages.INFO, f'{df.shape[0]} records found.')

    if (df.shape[0] > 0) and (hidenonvariants_flag or clinvar_flag or genelist_flag):
        df = df.loc[filter_genotype_to_variants_only_output_mask(df.fmt_GT), :]

    if OVERALL_SEARCH_LIMIT and (df.shape[0] > OVERALL_SEARCH_LIMIT):
        messages.add_message(request, messages.WARNING, f'More than {OVERALL_SEARCH_LIMIT} records retrieved. Not executing gene/snp/clinvar search.')
        return df

    if (df.shape[0] > 0) and (clinvar_flag or genelist_flag):
        df = _append_tiledb_with_annotation(df, flags=flags)
    
    return df

@login_required
def _help_tiledb(request,
                 uri:str=URI, 
                 memory_budget_mb:int=MEMORY_BUDGET_MB) -> pd.DataFrame:
    # cfg = tv.ReadConfig(memory_budget_mb=memory_budget_mb)
    # ds = tv.Dataset(uri, mode='r', cfg=cfg, verbose=True) 

    # composer = [f'{",".join(ds.attributes())}', f'{",".join(ds.samples())}']
    # composer = [f'{",".join(DS.attributes())}', f'{",".join(DS.samples())}']
    
    # return pd.DataFrame(composer, columns=['property'], index=['attributes', 'samples'])
    return DF_COMPOSER
 

def _append_tiledb_with_annotation(df, 
                                   chromosome_label =   'contig', 
                                   start_label      =   'pos_start',
                                   stop_label      =   'pos_end',
                                   genotype_label   =   'fmt_GT',
                                   allele_label     =   'alleles',
                                   af_label         =   'info_AF',
                                   show_only_alt    =   True,
                                   flags            =   {},
                                   ):
    """Needs at least the [chr, start, stop, genotype[0,1], allele[A,T]]. For the given dataframe
    of variants, append with the annotations from clinvar, dbsnp, refgene.

    `show_only_alt` == True : means that variants with genotype [0 0] will be discarded automatically
    """    
    # get unique set of chr,start,stop,allele, which may be greater 
    # than the inputted search because of multiple hits or different
    # alleles.

    # res_df_gene = pd.DataFrame(np.nan, index=df.index, columns=['gene_symbol','gene_product'])

    # do gene search which doesn't need the allele explosion operation. so may have to skip some rows. could skip based on the index.
    # NB this is SLOW. faster way would be to find a super set of the region being queried, get a list of all the genes
    # in that region, then match region to gene. That way I only query the database once!
    def genelist_lookup_inside_loop(row:pd.Series):
        gene_hit_items = (Genes.objects.filter(chromosome=row.loc['chr_int'])
                          .order_by('start')
                          .filter(start__lte=row.loc[start_label], 
                                  stop__gte=row.loc[stop_label],
                                  )
                          )
        # gene_hit = gene_hit_items.first()
        # return [gene_hit.gene, gene_hit.product] if gene_hit else [np.nan, np.nan]

        if gene_hit_items:
            gene_hits = ';'.join((list(set([re.sub(r'^gene\=', '', f'{g.gene}') for g in gene_hit_items]))))
        else:
            gene_hits = np.nan
        return gene_hits

    def search_for_snp_and_clinvar(s:pd.Series):
        if s.loc['id'] != ".":
            snp = s.loc['id']
        else:
            # # SNPS
            if SNP_SEARCH_FLAG:
                logger.info(f'search_for_snp_and_clinvar:input `s`: {s.shape}')
                snp_hits = list(Snps.objects.filter(chr=s.loc[chromosome_label], 
                                                    start=s.loc[start_label]).filter(
                                                        stop=s.loc[stop_label],
                                                        alt=s.loc['alt_allele'],
                                    )
                                )
                logger.info(f'search_for_snp_and_clinvar: snp_hits length: {len(snp_hits)}')
                
                # for now, just take the first hit. May decide to change in future.
                if snp_hits:
                    snp = snp_hits[0].rsid
                else:
                    snp = '-'
            else:
                snp = '-'

        # CLINVAR
            
        clinvar_hits = list(Clinvars.objects.filter(
            chromosome=s.loc['chr_int'],
            start=s.loc[start_label],
            stop=s.loc[stop_label],
            alternateallelevcf=s.loc['alt_allele'],
        ))
        logger.info(f'search_for_snp_and_clinvar: clinvar_hits length: {len(clinvar_hits)}')
        
        if clinvar_hits:
            clin = [clinvar_hits[0].id, clinvar_hits[0].alleleid, clinvar_hits[0].type, 
                    clinvar_hits[0].name, clinvar_hits[0].geneid, clinvar_hits[0].genesymbol, 
                    clinvar_hits[0].hgnc_id, clinvar_hits[0].clinicalsignificance, clinvar_hits[0].clinsigsimple, 
                    clinvar_hits[0].lastevaluated, clinvar_hits[0].rsid, clinvar_hits[0].nsvesv, 
                    clinvar_hits[0].rcvaccession, clinvar_hits[0].phenotypeids, clinvar_hits[0].phenotypelist, 
                    clinvar_hits[0].origin, clinvar_hits[0].originsimple, clinvar_hits[0].assembly, 
                    clinvar_hits[0].chromosomeaccession, clinvar_hits[0].chromosome, clinvar_hits[0].start, clinvar_hits[0].stop, 
                    clinvar_hits[0].referenceallele, clinvar_hits[0].alternateallele, clinvar_hits[0].cytogenetic, 
                    clinvar_hits[0].reviewstatus, clinvar_hits[0].numbersubmitters, clinvar_hits[0].guidelines, 
                    clinvar_hits[0].testedingtr, clinvar_hits[0].otherids, clinvar_hits[0].submittercategories,
                    clinvar_hits[0].variationid, clinvar_hits[0].positionvcf, clinvar_hits[0].referenceallelevcf,
                    clinvar_hits[0].alternateallelevcf, clinvar_hits[0].order]
        else:
            clin = ['-'] * len(CLINVAR_FIELDS)
        return [snp] + clin

    # script starts here

    df = df.copy()

    # parse the alleles and GT into set of alt genotypes, padding extra cells with with np.nan
    # gts = convert_pd_series_of_arrays_to_padded_np_array(df.loc[:, genotype_label])
    # als = convert_pd_series_of_arrays_to_padded_np_array(df.loc[:, allele_label])
    alt_allele_lists = df.apply(rowloop_index_a_with_b, axis=1, a_label=allele_label, b_label=genotype_label)
    df['alt_allele'] = alt_allele_lists

    alt_af_lists = df.apply(rowloop_index_a_with_b, axis=1, a_label=af_label, b_label=genotype_label, subtract_one=True)
    df['alt_af'] = alt_af_lists

    ### remove rows with NO ALT GENOTYPE. The assumption is that it will be a normal phenotype so not interesting
    if show_only_alt:
        df.dropna(axis=0, how='any', subset='alt_allele', inplace=True)
        if df.shape[0] == 0:
            return df
        
    
    df['chr_int'] = df.loc[:, chromosome_label].map(CHR_DICT_STR_TO_INT)
    
    # gene_hit_names = np.array([g.gene for g in gene_hit_items])
    # unique_hits, indices, counts = np.unique(gene_hit_names, return_index=True, return_counts=True)
    # count_sorted_index = np.argsort(counts)            
    # return [gene_hit_items[int(count_sorted_index[-1])].gene, gene_hit_items[int(count_sorted_index[-1])].product,]

    if flags.get('genelist_flag', False):
        res_df_gene = pd.DataFrame(
            df.apply(genelist_lookup_inside_loop, axis=1, result_type='expand').values,
            columns=['gene'],
            # columns=['gene','product']
            )
        logger.info('res_df_gene done')
        df = pd.concat([df.reset_index(drop=True), res_df_gene], axis=1)
    
    # explodes more than one nonzero allele to multiple lines, because rsid and clinvar search will require the alt allele
    df = df.explode(['alt_allele', 'alt_af']).reset_index(drop=True)

    if flags.get('clinvar_flag', False):
        # apply a search limit so as not to make the user wait for so long, and also avoid a mistakenly large query.
        if CLINVAR_SEARCH_LIMIT:
            clinvar_result_df = df.iloc[:CLINVAR_SEARCH_LIMIT].apply(search_for_snp_and_clinvar, axis=1, result_type='expand')
        else:
            clinvar_result_df = df.apply(search_for_snp_and_clinvar, axis=1, result_type='expand')
            
        snp_clinvar_result = pd.DataFrame(clinvar_result_df.values,
                                        columns=['rsid'] + CLINVAR_FIELDS)

        logger.info('snp_clinvar_result done')
        df = pd.concat([df, snp_clinvar_result], axis=1)

    
    return df


###### UTILS ###################################

def convert_pd_series_of_arrays_to_padded_np_array(s:pd.Series, fillna_value=np.nan):
    return pd.DataFrame(s.tolist()).fillna(fillna_value).to_numpy()

def filter_genotype_to_variants_only_output_mask(s:pd.Series) -> np.array:
    """assumes that the max columns of gts is 2"""
    gts = convert_pd_series_of_arrays_to_padded_np_array(s, 0)
    if gts.shape[1] > 2:
        warnings.warn('<filter_genotype_to_variants_only>:fmt_GT had more than 2 strands. Truncating to 2 only.')
        gts = gts.iloc[:, :2]
    arr = gts == 0
    arr2 = gts == -1
    mask = ~(np.einsum('i,i->i', arr[:,0], arr[:,1]) | np.einsum('i,i->i', arr2[:,0], arr2[:,1]))
    
    
    return mask

###### STYLERS #################################
cell_hover = {  # for row hover use <tr> instead of <td>
    'selector': 'tr:hover',
    'props': [('background-color', '#ffffb3')]
}

generic_cell = {
    'selector': 'table',
    'props': [('text-align', 'center')]
    }

def style_result_dataframe(styler):
    styler.set_table_attributes('class="table"')    
    styler.set_table_styles([generic_cell, cell_hover], overwrite=True)    
    return styler

def dataframe_common_final_reformat(df):
    xdf = df.copy()

    # renameing should be last step
    xdf.rename(columns=VCF_TRANSLATE, inplace=True)    
    return xdf

#######################################



