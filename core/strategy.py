# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 19:31:51 2017

@author: Avanti Financial Services.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from core.libraries.pub_sub import Subscriber
from core.trader import Trader

class Strategy(Subscriber):
    """
    Abstract class that will be inherited by the custom strategy of the user
    in Oanda_Trader/live_trader.py
    Uses an instance of Trader for placing trades.
    """
    def __init__(self, trader=None, *args, **kwargs):
        self.trader = Trader()
    
    def update(self, message):
        pass
    
    def calculate(self):
        """
        Method that will be overriden by the user.
        TODO: input-output interface.
        """
        pass
    
    

