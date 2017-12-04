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
from core.helpers.resampler import concat_ohlc
from core.trader import GDAXTrader as GDT
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
        self.ETF1 = kwargs['ETF1']
        self.ETF = kwargs['ETF']
        self.columns=['Date','O','H','L','C']

        self.timeframes = {'M1': '1T', 'M2': '2T', 'M3': '3T', 'M4': '4T',
                           'M5': '5T', 'M10': '10T', 'M15': '15T', 'M30': '30T',
                           'H1': '60T', 'H2': '2H', 'H3': '3H', 'H4': '4H',
                           'H6': '6H', 'H8': '8H', 'H12': '12H'}


        #creating the live dataframe
        self.live_df = pd.DataFrame(columns=['time', 'price', 'liquidity'])
        self.live_df['time'] = pd.to_datetime(self.live_df['time'], format="%Y-%m-%dT%H:%M:%SZ")
        self.live_df.set_index('time', drop=True, inplace = True)

        #request responses and dataframe laod
        data = self.request_data(self.ETF)
        self.ETF_df = self.load_df(data)

        data1 = self.request_data(self.ETF1)
        self.ETF1_df = self.load_df(data1)

#        print(" \nM5 DATAFRAME: \n {} \nM15 DATAFRAME: \n {}".format(self.ETF_df,
#                                                                   self.ETF1_df))

        #format required by the user
        self.TEMP_df = self.format_df(self.ETF_df)
        self.TEMP1_df = self.format_df(self.ETF1_df)

        #period of live dataframe
        scheduler = BackgroundScheduler()
        if self.ETF[0] == 'M':
            scheduler.add_job(self.update_dfs, trigger='cron',
                              minute='*/{}'.format(self.ETF[1]))
        elif self.ETF[0] == 'H':
            scheduler.add_job(self.update_dfs, trigger='cron',
                              hour='*/{}'.format(self.ETF[1]))
        scheduler.start()

        # Saving csv and calling on bar
        self.TEMP_df.to_csv('ETF.csv', index=False)
        self.TEMP1_df.to_csv('ETF1.csv', index=False)
        self.on_ETF_bar(self.TEMP_df,self.TEMP1_df)

    def request_data(self, timeframe):
        self.params['granularity'] = timeframe
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

        #Check for price in order to send stop loss or take profit orders
        GTD.check_position(message)

        time = message['time']
        new_element = [time , bid_data['price'], bid_data['liquidity']]
        columns_n=['time','price' ,'liquidity']

        temp_df = pd.DataFrame([new_element], columns=columns_n)
        temp_df['time'] = pd.to_datetime(temp_df['time'])
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
        rule = self.timeframes[self.ETF]
        resample_df = self.live_df['price'].resample(rule).ohlc().ffill()
        resample_df.columns = ['O','H','L','C']
        #print(resample_df)
        self.ETF_df = concat_ohlc(self.ETF_df, resample_df)
        ETF_df = self.format_df(self.ETF_df)

        # Updating ETF dataframe.
        rule = self.timeframes[self.ETF1]
        resample_df = self.live_df['price'].resample(rule).ohlc().ffill()
        resample_df.columns = ['O','H','L','C']

        self.ETF1_df = concat_ohlc(self.ETF1_df, resample_df)
        ETF1_df = self.format_df(self.ETF1_df)

        # Saving csv and calling on_bar.
        ETF_df.to_csv('ETF.csv', index=False)
        ETF1_df.to_csv('ETF1.csv', index=False)
        self.on_ETF_bar(ETF_df, ETF1_df)


if __name__ == "__main__":
    """For testing purposes"""
    from core.data_feeder import OandaDataFeeder

    #parameters set-up
    accountID = '101-001-1407695-002'
    access_token = 'f9263a6387fee52f94817d6cd8dca978-d097b210677ab84fb58b4655a33eb25c'

    headers = {'instrument': 'EUR_USD',
                'params': {'granularity':"M",
                           'count':5000},
                'access_token': access_token,
                'environment':'practice',
                'ETF1': 'M15',
                'ETF': 'M5'}

    message = {'bids': [{'liquidity': 10000000, 'price': '1.33045'}],
        'instrument': 'GBP_USD', 'tradeable': True,
        'asks': [{'liquidity': 10000000, 'price': '1.33097'}],
        'closeoutAsk': '1.33122', 'status': 'tradeable', 'time': '2017-11-23T20:44:35.635002033Z',
        'type': 'PRICE', 'closeoutBid': '1.33020'}


    client = oandapyV20.API(access_token=access_token, environment="practice")
    instrument='GBP_USD'

    dataf = OandaDataFeeder(accountID, client)
    dataf.get_live_data(instrument)

    strat = Strategy(**headers)
    #strat.update(message)
    dataf.pub.register('Oanda_data', strat)
