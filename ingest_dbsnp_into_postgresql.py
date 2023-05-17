# Purpose: ingest SNP  data into PostgreSQL database
# note that the input tsv must have an index column with 
# a blank header and incremental integer indexes

import psycopg2
import pandas as pd
import os
import pathlib
from getpass import getpass
import sys
import datetime
import gzip

CORRECT_HEADERS = ['rsid', 'chr', 'start', 'stop', 'ref', 'alt', 'af']

def get_format_timestamp_now() -> str:
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

def execute_on_db(fn:str, password:str='', table_name='annoquery_snps'): 
    if not password:
        try:
            password = os.environ['ANNODB_SECRET_PW']
            print('Password found.')
        except KeyError:
            print('Password not found in env.')
            password = getpass()
            
    with psycopg2.connect(f"host=anno-db dbname=annodb user=prism1 password={password}") as conn:
        cursor_obj = conn.cursor()        
        print(get_format_timestamp_now(), ">>", "Truncating begun...")        
        cursor_obj.execute(f'TRUNCATE {table_name}')
        print(get_format_timestamp_now(), ">>", "Truncated.")        
        
        print(get_format_timestamp_now(), ">>", "Ingesting begun...")
        with gzip.open(fn, 'r') as f:
            # cursor_obj.copy_from(f, 'annoquery_clinvars', sep='\\t')
            cursor_obj.copy_expert(f"""COPY {table_name} from STDIN WITH (FORMAT csv, DELIMITER E'\t', HEADER true)""", f)
        print(get_format_timestamp_now(), ">>", "Ingested.")

def check_filename_input(fn:str):
    assert os.path.isfile(fn)
    with open(fn, 'r') as f:
        headers_extracted = [x.strip() for x in f.readlines(1)[0].split('\t')]
        assert headers_extracted == CORRECT_HEADERS
    print(get_format_timestamp_now(), ">>", f"'{fn}' is a valid file with the correct headers")



    

if __name__ == '__main__':
    # check_filename_input(sys.argv[1])
    if input("WARNING! This operation will remove all existing data in the `annoquery_snps` table of the PostgreSQL database!\nThe operation will also take more than a few minutes (but < 30 mins) to ingest the data and rebuild the indexes.\nDo you still want to continue?(y/N)") == 'y':
        execute_on_db(sys.argv[1])
