from typing import Union
import pandas as pd
import numpy as np
import sys
from pathlib import Path
import datetime
import urllib.request
import os

pd.set_option('mode.chained_assignment', None)


def string_to_float(x) -> Union[int, str]:
    try:
        return int(x)
    except ValueError:
        return x


def get_format_timestamp_now() -> str:
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

def tag_duplicated_allele_ids_with_order(df, aid_colname='AlleleID'):
    df = df.copy()
    df['Order'] = 0
    al_dup = df.loc[:, aid_colname].duplicated()
    aid_duped_list = df.loc[al_dup, aid_colname].values
    for aid in aid_duped_list:            
        q = df.loc[df.loc[:, aid_colname].eq(aid), :]
        df.loc[q.index, 'Order'] = np.arange(q.shape[0], dtype=int) + 1
    df['Order'] = df.Order.astype(int)
    
    # ensure a unique_together constraint
    assert df.duplicated(['AlleleID', 'Order']).sum() == 0
    return df

CORRECT_HEADERS = ['', 'AlleleID', 'Type', 'Name', 'GeneID', 'GeneSymbol', 'HGNC_ID', 
                   'ClinicalSignificance', 'ClinSigSimple', 'LastEvaluated', 'rsid', 
                   'nsv/esv (dbVar)', 'RCVaccession', 'PhenotypeIDS', 'PhenotypeList', 
                   'Origin', 'OriginSimple', 'Assembly', 'ChromosomeAccession', 'Chromosome', 
                   'Start', 'Stop', 'ReferenceAllele', 'AlternateAllele', 'Cytogenetic', 
                   'ReviewStatus', 'NumberSubmitters', 'Guidelines', 'TestedInGTR', 
                   'OtherIDs', 'SubmitterCategories', 'VariationID', 'PositionVCF', 
                   'ReferenceAlleleVCF', 'AlternateAlleleVCF', 'Order']


def create_variant_summary_from_summary_df(df:pd.DataFrame) -> pd.DataFrame:        
    df.rename(columns={'#AlleleID':'AlleleID', 'RS# (dbSNP)':'rsid'}, inplace=True)
    df = df.query('Assembly == "GRCh38"')    
    df.loc[:, 'Chromosome'] = df.Chromosome.map(string_to_float)
    df = tag_duplicated_allele_ids_with_order(df, 'AlleleID')
    df.sort_values(['Chromosome', 'Start', 'Order'], inplace=True)
    df.reset_index(inplace=True, drop=True)
    
    # force compliance with my arbitrary SQL model constraints of character length. 
    # see annoquery.models.py for the constraint limits.
    char_limit_dict = {
        'Name':800,
        'Type':25,
        'GeneSymbol':710, 
        'HGNC_ID':10,
        'ClinicalSignificance':70,
        'LastEvaluated':12,
        'nsv/esv (dbVar)':12,
        'RCVaccession':597,
        'PhenotypeIDS':4300,
        'PhenotypeList':1450,
        'Origin':55,
        'OriginSimple':19,
        'Assembly':6,
        'ChromosomeAccession':14,
        'Chromosome':4,
        'ReferenceAllele':12,
        'AlternateAllele':20, 
        'Cytogenetic':24, 
        'ReviewStatus':52,
        'Guidelines':35, 
        'TestedInGTR':1, 
        'OtherIDs':4035,
        'ReferenceAlleleVCF':100,
        'AlternateAlleleVCF':100,
    }

    for k,v in char_limit_dict.items():
        maxlen = df[k].str.len().max()
        if maxlen > v:
            df[k] = df[k].str.slice(stop=v)
            print(f'    - Truncated `{k}` due to maxlen:{maxlen} > db limit: {v}')
    
    # df['ReferenceAlleleVCF'] = df.ReferenceAlleleVCF.str.slice(stop=100)
    # df['AlternateAlleleVCF'] = df.AlternateAlleleVCF.str.slice(stop=100)  
    # df['RCVaccession'] = df.RCVaccession.str.slice(stop=597)
    # df.loc[:, df.dtypes == "object"].apply(lambda x: x.str.slice(stop=100), axis=0)
    
    return df

def save_df(df:pd.DataFrame, output_fn:str):     
    df.to_csv(output_fn, sep='\t', index=True)
    return Path(output_fn)


def process_url_to_df(url:Union[str, Path], output_fn:str=''):  
    print(get_format_timestamp_now(), '>>', 'Reading uri at', url)
    df = pd.read_csv(url, sep='\t', header=0)
    print(get_format_timestamp_now(), '>>', 'Done reading uri at', url)
    print(get_format_timestamp_now(), '>>', 'Processing dataframe into variant_summary format')
    df_processed = create_variant_summary_from_summary_df(df)
    print(get_format_timestamp_now(), '>>', 'Done. Saving to', output_fn or "unspecified, so will use default filename suffix")

    today = datetime.date.today().strftime('%Y-%m-%d')
    if not output_fn:
        output_fn = (os.path.splitext(Path(url).absolute())[0] + f'_filtered_{today}.txt')
    
    actual_path = save_df(df_processed, output_fn)   
    print(get_format_timestamp_now(), '>>', 'Done. Saved to', actual_path) 
    return Path(actual_path)


def from_arguments_decide_what_to_do(args:list):

    def help_msg():
        return 'Usage: python process_variant_summary.py [uri|"download"] [optional:output_fn]. If "download" passed as first argument, the latest clinvar file will be downloaded from the ncbi ftp site. If a URL or filepath is passed as the first argument, load that file into the dataframe for processing. If no `output_fn` is passed, the default is to append the filename with "_filtered_DATE.txt".'
    arglen = len(args)
        
    # if no arguments are passed, display a help message    
    if arglen == 1:
        print(help_msg())
        return
    # if one or two arguments are passed, check if it is a valid url or if it is the command 'download'
    # assume a well-formed 3rd agument as the output filename
    elif arglen >= 2:
        if arglen == 2:
            args.append('')
        if args[1] == 'download':
            # set the url to the latest clinvar file
            uri = 'https://ftp.ncbi.nlm.nih.gov/pub/clinvar/tab_delimited/variant_summary.txt.gz'
            if not args[2]:
                args[2] = Path(uri).stem
            
        else:
            # first arg can be a filename or url
            uri = str(args[1])

        if os.path.isdir(args[2]):
            today = datetime.date.today().strftime('%Y-%m-%d')
            args[2] = Path(args[2]) / f'variant_summary_filtered_{today}.txt'
        
        print(f'Using output filename: "{args[2]}"')

        # turn the uri into a dataframe
        actual_path = process_url_to_df(uri, output_fn=str(args[2]))
        return actual_path

    else:
        raise ValueError('Invalid number of arguments.', help_msg())
    


if __name__ == "__main__":
    from_arguments_decide_what_to_do(sys.argv)
