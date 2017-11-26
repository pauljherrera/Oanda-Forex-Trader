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

from apscheduler.schedulers.background import BackgroundScheduler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from core.helpers.pub_sub import Subscriber
from core.helpers.resampler import resample_ohlcv, concat_ohlc

class Strategy(Subscriber):
    """
    Abstract class that will be inherited by the custom strategy of the user
    in Oanda_Trader/live_trader.py
    Uses an instance of Trader for placing trades.
    """
    def __init__(self, trader=None, *args, **kwargs):
        self.trader = trader
        self.params = kwargs['params']
        self.instrument = kwargs['instrument']
        self.access_token = kwargs['access_token']
        self.environment = kwargs['environment']
        self.ETF1 = '{}T'.format(kwargs['ETF1'])
        self.ETF = kwargs['ETF']
        self.columns=['Date','O','H','L','C']

        #creating the live dataframe
        self.live_df = pd.DataFrame(columns=['time', 'price', 'liquidity'])
        self.live_df['time'] = pd.to_datetime(self.live_df['time'], format="%Y-%m-%dT%H:%M:%SZ")
        self.live_df.set_index('time', drop=True, inplace = True)

        #request responses and dataframe laod
        data = self.request_data()
        self.ETF_df = self.load_df(data)

        data1 = self.request_data()
        self.ETF1_df = self.load_df(data1)

#        print(" \nM5 DATAFRAME: \n {} \nM15 DATAFRAME: \n {}".format(self.ETF_df,
#                                                                   self.ETF1_df))

        #format required by the user
        self.TEMP_df = self.format_df(self.ETF_df)
        self.TEMP1_df = self.format_df(self.ETF1_df)

        #period of live dataframe
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.update_dfs, trigger='cron',
                          minute='*/{}'.format(self.ETF))
        scheduler.start()

        # Calling on bar.
        self.on_ETF_bar(self.TEMP_df,self.TEMP1_df)

    def request_data(self):
        res = instruments.InstrumentsCandles(instrument=self.instrument, params=self.params)
        client = oandapyV20.API(access_token=self.access_token, environment=self.environment)
        client.request(res)

        return res.response

    def load_df(self, data):
        ETF = pd.DataFrame(columns=self.columns)
        ETF['Date'] = [i['time'] for i in data['candles']]
        ETF[['O','H','L','C']] = [(float(i['mid']['o']), float(i['mid']['h']),
                                           float(i['mid']['l']), float(i['mid']['c'])) \
                                           for i in data['candles']]
        ETF['Date'] = pd.to_datetime(ETF['Date'])
        ETF.set_index('Date', drop=True, inplace=True)

        return ETF

    def format_df(self, df):
        TEMP_df = df
        TEMP_df = TEMP_df.sort_index()
        TEMP_df['Date'] = TEMP_df.index
        TEMP_df.reset_index(drop=True, inplace=True)
        TEMP_df = TEMP_df[self.columns]

        return TEMP_df

    def update(self, message):
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
        #print(self.live_df)

    def on_ETF_bar(self, ETF_df, ETF1_df):
        """
        Method that will be overriden by the user.
        """
        print(ETF_df)
        print(ETF1_df)

    def update_dfs(self):
        # Updating ETF dataframe.
        rule = '{}T'.format(self.ETF)
        resample_df = self.live_df['price'].resample(rule).ohlc().ffill()
        resample_df.columns = ['O','H','L','C']
        #print(resample_df)
        self.ETF_df = concat_ohlc(self.ETF_df, resample_df)
        ETF_df = self.format_df(self.ETF_df)

        # Updating ETF dataframe.
        resample_df = self.live_df['price'].resample(self.ETF1).ohlc().ffill()
        resample_df.columns = ['O','H','L','C']

        self.ETF1_df = concat_ohlc(self.ETF1_df, resample_df)
        ETF1_df = self.format_df(self.ETF1_df)

        self.on_ETF_bar(ETF_df, ETF1_df)


if __name__ == "__main__":
    """testing"""
    from core.data_feeder import OandaDataFeeder

    #parameters set-up
    headers = {'instrument': 'GBP_USD',
                'params': {'granularity':"D", 'count': 200}, #number of days in the dataframe
                'access_token': 'f9263a6387fee52f94817d6cd8dca978-d097b210677ab84fb58b4655a33eb25c',
                'environment':'practice',
                'ETF1': 15,
                'ETF': 5} #minutes | period of live dataframe
    #'accountID' = '101-001-1407695-002'
    message = {'bids': [{'liquidity': 10000000, 'price': '1.33045'}],
        'instrument': 'GBP_USD', 'tradeable': True,
        'asks': [{'liquidity': 10000000, 'price': '1.33097'}],
        'closeoutAsk': '1.33122', 'status': 'tradeable', 'time': '2017-11-23T20:44:35.635002033Z',
        'type': 'PRICE', 'closeoutBid': '1.33020'}


    accountID = '101-001-1407695-002'
    access_token = 'f9263a6387fee52f94817d6cd8dca978-d097b210677ab84fb58b4655a33eb25c'
    client = oandapyV20.API(access_token=access_token, environment="practice")
    instrument='GBP_USD'

    dataf = OandaDataFeeder(accountID, client)
    dataf.get_live_data(instrument)

    strat = Strategy(**headers)
    #strat.update(message)
    dataf.pub.register('new_data', strat)
