# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 17:23:35 2017

@author: Avanti Financial Services.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from core.libraries.pub_sub import Publisher


class OandaDataFeeder:
    """
    Gets live data from Oanda. Uses a publisher class to feed the data to
    other components.
    """
    def __init__(self):
        self.pub = Publisher()
    


