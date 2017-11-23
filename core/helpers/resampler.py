# -*- coding: utf-8 -*-
"""
Created on Thu Nov 23 11:40:11 2017

@author: paulj
"""

import pandas as pd

def resample_ohlcv(df, rule='1H',volume = False ):
    """
    Resamples a OHLCV DataFrame.
    Returns a OHLCV DataFrame.
    Differs from pandas.resample().ohlc() because it considers all the columns
    of the DataFrame, not just the close.
    """
    resampled_df = pd.DataFrame()
    resampled_df['O'] = df['O'].resample(rule).first()
    resampled_df['H'] = df['H'].resample(rule).max()
    resampled_df['L'] = df['L'].resample(rule).min()
    resampled_df['C'] = df['C'].resample(rule).last()
    if volume:
        resampled_df['volume'] = df['volume'].resample(rule).sum()

    return resampled_df
