# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 19:50:08 2017

@author: Avanti Financial Services.
"""
"""
Options for the timeframe:
“M2” - 2 minutes
“M3” - 3 minutes
“M4” - 4 minutes
“M5” - 5 minutes
“M10” - 10 minutes
“M15” - 15 minutes
“M30” - 30 minutes
“H1” - 1 hour
“H2” - 2 hours
“H3” - 3 hours
“H4” - 4 hours
“H6” - 6 hours
“H8” - 8 hours
“H12” - 12 hours
"""


Oanda_config = {
            'AccountID': '101-001-1407695-002',
            'Token': 'f9263a6387fee52f94817d6cd8dca978-d097b210677ab84fb58b4655a33eb25c',
            'Environment': 'practice', # 'practice' of 'live'
            'Instrument': 'EUR_USD',
            'ETF': 'M1',
            'ETF1': 'M5',
            }
GDAX_config = {
            'API_KEY' : "",
            'API_SECRET' : "",
            'API_PASS' : "",
            'request':{"type": "subscribe",
                    "channels": [{"name": "full", "product_ids": ["BTC-USD"]}]},
            }

def get_config(platform):
    configuration = {}
    if platform == "oanda":
        configuration = Oanda_config
    elif platform == "gdax":
        configuration = GDAX_config

    return configuration
