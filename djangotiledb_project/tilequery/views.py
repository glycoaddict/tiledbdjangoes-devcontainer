from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

import pandas as pd
from typing import List
import warnings
import configparser
import tiledbvcf as tv


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

# Create your views here.

@login_required
def index(request, methods=['GET', 'POST']): 

    def return_with_error(e:Exception, query_summary=None):
            warnings.warn(e.__str__())
            messages.add_message(request, messages.WARNING, e.__str__())
            context=dict(query_summary=query_summary)
            return render(request, 'tilequery/query.html', context)
    
    if request.method == 'POST':        
        
        regions=request.POST.get('regions').split(',')
        samples=request.POST.get('samples').split(',')
        attrs=request.POST.get('attrs').split(',')
        if all([x=='' for x in regions]) and (all([x=='' for x in samples]) if samples else True):
            w  = '<_query_tiledb> regions:List[str] must not be empty strings. Returning the possible samples and attributes you may query.'
            e = ValueError(w)
            df_help = _help_tiledb(request)             
            return return_with_error(e, query_summary=df_help.style.pipe(style_result_dataframe).render())       
        elif all([x=='' for x in regions]):
            regions = pathogenic_vars            
            messages.add_message(request, messages.WARNING, 'Region unspecified but samples specified, so a list of pathogenic variants from clinvar was substituted.')
            
        query_summary = pd.DataFrame([",".join(regions), ",".join(samples), ",".join(attrs)], columns=['query'], index=['regions', 'samples', 'attributes'])

        # print((regions), (samples), (attrs))
        
        try:
            df = _query_tiledb(request, regions=regions, samples=samples, attrs=attrs)
            df.index.name = 'S/N'
        except Exception as e:
            return return_with_error(e, query_summary=query_summary.style.pipe(style_result_dataframe).render())

        # # Tag with overlap of the original query
        # if 'pos_start' in df.columns and 'pos_end' in df.columns:
        #     answer_regions = df.loc[:, ['contig', 'pos_start', 'pos_end']]
        #     query_regions = pd.DataFrame([re.split(r':|-', x)[1:] for x in regions], columns=['q_contig', 'q_pos_start', 'q_pos_end'])
            
        df = dataframe_common_final_reformat(df)

        ### STYLE ####
        # final_content = df.to_html(classes=['table'], justify='center')
        # final_content = df.style.pipe(style_result_dataframe).to_html()        
        final_content = df.style.pipe(style_result_dataframe).render()
        ##############
        context =  dict(answer=final_content, query_summary=query_summary.style.pipe(style_result_dataframe).render())
        return render(request, 'tilequery/query.html', context)
        
    else:            
        return render(request, 'tilequery/query.html')    

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

@login_required
def _query_tiledb(request,
                  regions:List[str],
                  samples:List[str],
                  attrs:List[str]=['sample_name', 'alleles', 'fmt_GT', 'contig', 'pos_start'],
                #   attrs:Union[None, List[str]]=['sample_name', 'alleles', 'fmt_GT', 'contig', 'pos_start'], 
                  uri:str=URI, 
                  memory_budget_mb:int=MEMORY_BUDGET_MB)->pd.DataFrame:

    # if regions and sample are empty, return error
    # if regions empty but sample not empty, substitute the pathogenic var list.
    # if regions specified and sample specified, proceed as normal to extract all samples.
    
    cfg = tv.ReadConfig(memory_budget_mb=memory_budget_mb)
    ds = tv.Dataset(uri, mode='r', cfg=cfg, verbose=True)   
    df = ds.read(attrs=attrs, regions=regions, samples=samples)
    
    # if all([x=='' for x in regions]):   
    #     w  = '<_query_tiledb> regions:List[str] must not be empty strings'
    #     raise ValueError(w)
    return df

@login_required
def _help_tiledb(request,
                 uri:str=URI, 
                 memory_budget_mb:int=MEMORY_BUDGET_MB) -> pd.DataFrame:
    cfg = tv.ReadConfig(memory_budget_mb=memory_budget_mb)
    ds = tv.Dataset(uri, mode='r', cfg=cfg, verbose=True) 

    composer = [f'{",".join(ds.attributes())}', f'{",".join(ds.samples())}']
    
    return pd.DataFrame(composer, columns=['property'], index=['attributes', 'samples'])
 



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



