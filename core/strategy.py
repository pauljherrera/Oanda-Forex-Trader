# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 19:31:51 2017

@author: Avanti Financial Services.
"""
import sys
import os
import datetime as dt
import pandas as pd

import oandapyV20.endpoints.instruments as instruments
import oandapyV20

from apscheduler.schedulers.background import BackgroundScheduler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from core.helpers.pub_sub import Subscriber
from core.helpers.resampler import resample_ohlcv
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
        self.user_timeframe = kwargs['timeframe']
        self.timeframe_period = kwargs['timeframe period']
        #prepairing the parameters for request
        res = instruments.InstrumentsCandles(instrument=self.instrument, params=self.params)
        self.client = oandapyV20.API(access_token=self.access_token, environment=self.environment)
        self.client.request(res)

        #creating the live dataframe
        self.live_df = pd.DataFrame(columns=['time', 'price', 'liquidity'])
        self.live_df['time'] = pd.to_datetime(self.live_df['time'], format="%Y-%m-%dT%H:%M:%SZ")
        self.live_df.set_index('time', drop=True, inplace = True)

        #creating and setting up the dataframe with the format specified by the client
        self.data = res.response
        self.hist_df = pd.DataFrame(columns=['Date', 'O','H','L','C'])
        self.hist_df['Date'] = [i['time'] for i in self.data['candles']]
        self.hist_df[['O','H','L','C']] = [(i['mid']['o'], i['mid']['h'], i['mid']['l'], i['mid']['c']) for i in self.data['candles']]
        self.hist_df['Date'] = pd.to_datetime(self.hist_df['Date'])
        self.hist_df.set_index('Date', drop=True, inplace=True)
        dataf_base = self.hist_df
        dataf_period = resample_ohlcv(dataf_base,rule = self.user_timeframe, volume=False)
        #dataf_period.dropna(how='any', inplace=True)
        print(" \nM5 DATAFRAME: \n {} \nM15 DATAFRAME: \n {}".format(dataf_base,dataf_period))

        #period of live dataframe
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.show_df, trigger='cron',
                          minute='*/{}'.format(self.timeframe_period))

        scheduler.start()

    def update(self, message):
        print(message)
        self.dataframe_live(message)

    def calculate(self):
        """
        Method that will be overriden by the user.
        TODO: input-output interface.
        """
        pass

    def dataframe_live(self, message):
        #Extracting the data in order to build the dataframe
        bid_data =  message['bids'].pop()
        time = message['time']
        new_element = [time , bid_data['price'], bid_data['liquidity']]
        columns_n=['time','price' ,'liquidity']

        temp_df = pd.DataFrame([new_element], columns=columns_n)
        temp_df['time']= pd.to_datetime(temp_df['time'])
        temp_df['price'] =  temp_df['price'].astype(float)
        temp_df.set_index('time', drop=True, inplace=True)

        self.live_df = pd.concat([self.live_df, temp_df])

    def show_df(self):
        resample_df = self.live_df['price'].resample(self.user_timeframe).ohlc().ffill()
        resample_df.columns = ['O','H','L','C']
        print(resample_df)


if __name__ == "__main__":
    """testing"""
    #parameters set-up
    headers = {'instrument': 'GBP_USD',
                'params': {'granularity':"M5", 'count':201},
                'access_token': 'f9263a6387fee52f94817d6cd8dca978-d097b210677ab84fb58b4655a33eb25c',
                'environment':'practice',
                'timeframe': '15T',
                'timeframe period': 5} #minutes | period of live dataframe
    #'accountID' = '101-001-1407695-002'
    message = {'bids': [{'liquidity': 10000000, 'price': '1.33045'}],
        'instrument': 'GBP_USD', 'tradeable': True,
        'asks': [{'liquidity': 10000000, 'price': '1.33097'}],
        'closeoutAsk': '1.33122', 'status': 'tradeable', 'time': '2017-11-23T20:44:35.635002033Z',
        'type': 'PRICE', 'closeoutBid': '1.33020'}

    strat = Strategy(**headers)
    strat.update(message)
