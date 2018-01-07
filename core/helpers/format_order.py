"""
Created on Thu Nov 30 17:52:00 2017

@author: Avanti Financial Services.
"""
import numpy as np

def round_values(trade, decimals=5):
    trade['Entry Price'] = float(np.around([trade['Entry Price']], decimals=decimals))
    trade['Stop Loss'] = float(np.around([trade['Stop Loss']], decimals=decimals))
    trade['Target Price 1'] = float(np.around([trade['Target Price 1']], decimals=decimals))
    trade['Target Price 2'] = float(np.around([trade['Target Price 2']], decimals=decimals))
    return trade
