from typing import Union
import pandas as pd
import numpy as np
import sys
from pathlib import Path
import datetime
import urllib.request
import os
import gzip

pd.set_option('mode.chained_assignment', None)

CORRECT_HEADERS = ['rsid', 'chr', 'start', 'stop', 'ref', 'alt', 'af']
# 1 million rows
CHUNK_SIZE = 10**6 


def string_to_float(x) -> Union[int, str]:
    try:
        return int(x)
    except ValueError:
        return x


def get_format_timestamp_now() -> str:
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')



def save_df(df:pd.DataFrame, output_fn:str):     
    df.to_csv(output_fn, sep='\t', index=True)
    return Path(output_fn)




def from_arguments_decide_what_to_do(args:list):

    def help_msg():
        return 'Usage: python process_snps.py [path/to/file] [optional:output_fn]. If no `output_fn` is passed, the default is to append the filename with "_filtered_DATE.txt".'

    arglen = len(args)
        
    # if no arguments are passed, display a help message    
    if arglen == 1:
        print(help_msg())
        return
    # if one or two arguments are passed, proceed
    # assume a well-formed 3rd agument as the output filename
    elif arglen >= 2:
        if arglen == 2:
            args.append('')
        
        # first arg should be a filename
        uri = str(args[1])

        if not args[2]:
            args[2] = Path('/').absolute()

        if os.path.isdir(args[2]):
            today = datetime.date.today().strftime('%Y-%m-%d')
            args[2] = Path(args[2]) / f'{Path(args[1]).stem}_filtered_{today}.tsv.gz'
        
        print(f'Using output filename: "{args[2]}"')

        # turn the uri into a dataframe
        actual_path = clean_up_snps(uri, output_fn=str(args[2]))
        print('Saved to:', actual_path)
        return actual_path

    else:
        raise ValueError('Invalid number of arguments.', help_msg())
    
def clean_up_snps(fn:str, output_fn:str):

    with gzip.open(fn, 'rt') as f_in:
        last_index = 0
        # iterate over the file in chunks
        for i, chunk in enumerate(pd.read_csv(f_in, sep='\t', chunksize=CHUNK_SIZE, index_col=None, header=None, names=CORRECT_HEADERS)):
            print(f">>> Chunk: {i}, shape={chunk.shape}")

            chunk.index = pd.Index(range(last_index, last_index + chunk.shape[0]), dtype=int)
            last_index = chunk.index.to_list()[-1] + 1
            
            char_limit_dict = {
                'ref':64,
                'alt':64,
                'af':500,
                }
            
            for k,v in char_limit_dict.items():
                maxlen = chunk[k].str.len().max()
                if maxlen > v:
                    chunk[k] = chunk[k].str.slice(stop=v)
                    print(f'    - Truncated `{k}` due to maxlen:{maxlen} > db limit: {v}')
                    
            chunk.to_csv(output_fn, sep='\t', index=True, mode='a', header=False)
    
    return output_fn

if __name__ == "__main__":
    from_arguments_decide_what_to_do(sys.argv)
