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

def concat_ohlc(df1, df2):
    """
    Concatenates two OHLCV dataframes. If some of the index members of
    the two dataframes are equal, it deals with it maintaining the
    OHLCV integrity.
    """
    # Getting similar index.
    equals = set(df1.index).intersection(set(df2.index))

    # Concatenating.
    concat_df = pd.concat([df1, df2])
    concat_df = concat_df.groupby(concat_df.index).first()

    # Dealing with colliding indexes.
    for e in equals:
        concat_df.at[e,'H'] = max(df1.loc[e,'H'], df2.loc[e,'H'])
        concat_df.at[e,'L'] = min(df1.loc[e,'L'], df2.loc[e,'L'])
        concat_df.at[e,'C'] = df2.loc[e,'C']

    return concat_df
