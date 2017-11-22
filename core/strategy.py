# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 19:31:51 2017

@author: Avanti Financial Services.
"""
import sys
import os
import pandas as pd

import oandapyV20.endpoints.instruments as instruments
import oandapyV20

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from core.helpers.pub_sub import Subscriber
from core.trader import Trader

class Strategy(Subscriber):
    """
    Abstract class that will be inherited by the custom strategy of the user
    in Oanda_Trader/live_trader.py
    Uses an instance of Trader for placing trades.
    """
    def __init__(self, trader=None, *args, **kwargs):
        #self.trader = Trader()
        self.params = kwargs['params']
        self.instrument = kwargs['instrument']
        self.access_token = kwargs['access_token']
        self.environment = kwargs['environment']
        self.timeframe = kwargs['timeframe']

        #prepairing the parameters for request
        res = instruments.InstrumentsCandles(instrument=self.instrument, params=self.params)
        self.client = oandapyV20.API(access_token=self.access_token, environment=self.environment)
        self.client.request(res)

        #creating and setting up the dataframe with the format specified by the client
        self.data = res.response
        self.hist_df = pd.DataFrame(columns=['Date', 'O','H','L','C'])
        self.hist_df['Date'] = [i['time'] for i in self.data['candles']]
        self.hist_df[['O','H','L','C']] = [(i['mid']['o'], i['mid']['h'], i['mid']['l'], i['mid']['c']) for i in self.data['candles']]
        self.hist_df['Date'] = pd.to_datetime(self.hist_df['Date'])
        self.hist_df.set_index('Date', drop=True, inplace=True)
        print(self.hist_df)
        print(self.hist_df.resample(self.timeframe).asfreq()[::-1].ffill())

    def update(self, message):
        pass

    def calculate(self):
        """
        Method that will be overriden by the user.
        TODO: input-output interface.
        """
        pass

if __name__ == "__main__":

    #parameters set-up
    headers = {'instrument': 'GBP_USD',
                'params': {'granularity':"M5", 'count':201},
                'access_token': 'f9263a6387fee52f94817d6cd8dca978-d097b210677ab84fb58b4655a33eb25c',
                'environment':'practice',
                'timeframe': '15T'} #or M15 by request way

    #'accountID' = '101-001-1407695-002'
    strat = Strategy(**headers)
