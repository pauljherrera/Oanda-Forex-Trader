# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 17:32:50 2017

@author: paulj
"""



class Trader:
    """
    Makes trades operations using the Oanda API wrapper.
    """
    def place_order(self, _type='market', volume=1000, side='buy',
                    pair='EUR_USD', price=None, stop_loss=None,
                    take_profit=None):
        pass
    
    def close_order(self):
        pass
    