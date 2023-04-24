import pandas as pd
import numpy as np

def rowloop_index_a_with_b(s:pd.Series, a_label, b_label, subtract_one=False, use_first_in_a_as_default=False):    
    """Usually in the context of `df.apply(thisfunc, axis=1)`, is expecting a pandas row-series and will take the unique nonzero genotype reference numbers (`b_label`) and index the allele list (`a_label`)"""
    nonzeros = list(set(s.loc[b_label][np.flatnonzero(s.loc[b_label])]) - set([-1]))
    if len(nonzeros):        
        ans = s.loc[a_label][np.subtract(nonzeros, 1 if subtract_one else 0)]
    else:
        # if allele, return the first of the list, ie the Wild Type
        # else it is a allele_freq, so return np.nan
        if use_first_in_a_as_default:
            ans =  s.loc[a_label][0]
        else:
            ans = np.nan

    if isinstance(ans, np.ndarray):
        return ans.tolist()
