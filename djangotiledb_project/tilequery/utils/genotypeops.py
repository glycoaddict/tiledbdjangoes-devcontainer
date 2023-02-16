import pandas as pd
import numpy as np

def rowloop_index_a_with_b(s:pd.Series, a_label, b_label):    
    """Usually in the context of `df.apply(thisfunc, axis=1)`, is expecting a pandas row-series and will take the unique nonzero genotype reference numbers (`b_label`) and index the allele list (`a_label`)"""
    nonzeros = list(set(s.loc[b_label][np.flatnonzero(s.loc[b_label])]))
    if len(nonzeros):        
        return s.loc[a_label][np.subtract(nonzeros,1)]
    else:
        return np.nan

