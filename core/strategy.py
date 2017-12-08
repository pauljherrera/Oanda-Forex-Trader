# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 19:31:51 2017

@author: Avanti Financial Services.
"""
import sys
import os
import gdax
import pandas as pd
import datetime as dt
import oandapyV20.endpoints.instruments as instruments
import oandapyV20

from apscheduler.schedulers.background import BackgroundScheduler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from core.helpers.pub_sub import Subscriber
from core.helpers.resampler import concat_ohlc
from core.trader import GDAXTrader as GDT
from core.helpers.gdax_data_downloader import get_historic_rates

class Strategy(Subscriber):
    """
    Abstract class that will be inherited by the custom strategy of the user
    in Oanda_Trader/live_trader.py
    Uses an instance of Trader for placing trades.
    """
    def __init__(self, platform="GDAX", trader=None, *args, **kwargs):
        self.trader = trader
        self.columns=['Date','O','H','L','C']
        self.instrument = kwargs['instrument']
        self.data_days = kwargs['data days']
        m = 60
        h = 3600
        #self.timeframes = {'M1': '1T', 'M2': '2T', 'M3': '3T', 'M4': '4T',
        #                   'M5': '5T', 'M10': '10T', 'M15': '15T', 'M30': '30T',
        #                   'H1': '60T', 'H2': '2H', 'H3': '3H', 'H4': '4H',
        #                   'H6': '6H', 'H8': '8H', 'H12': '12H'}

        self.timeframes = {'M1':1*m, 'M2':2*m , 'M3':3*m, 'M4':4*m,
                           'M5':5*m, 'M10':10*m, 'M15':15*m, 'M30':30*m,
                           'H1':1*h, 'H2':2*h, 'H3':3*h, 'H4':4*h,
                           'H6':6*h , 'H8':8*h , 'H12':12*h}

        self.ETF1 = kwargs['ETF1']
        self.ETF = kwargs['ETF']

        if platform == "Oanda":
            measure = 'liquidity'
            self.params = kwargs['params']
            self.access_token = kwargs['access_token']
            self.environment = kwargs['environment']

            #request responses and dataframe load
            data = self.request_data(self.ETF)
            self.ETF_df = self.load_df(data)

            data1 = self.request_data(self.ETF1)
            self.ETF1_df = self.load_df(data1)

            #format required by the user
            self.TEMP_df = self.format_df(self.ETF_df)
            self.TEMP1_df = self.format_df(self.ETF1_df)

            self.TEMP_df = self.ETF_df
            self.TEMP1_df = self.ETF1_df

        elif platform == "GDAX":
            measure = 'size'
            timeframe_1 = self.timeframes[self.ETF]
            timeframe_2 = self.timeframes[self.ETF1]
            self.client = gdax.PublicClient()

            self.ETF_df = self.load_gdax_df(timeframe_1, self.instrument)
            self.ETF1_df = self.load_gdax_df(timeframe_2, self.instrument)

            self.TEMP_df = self.ETF_df
            self.TEMP1_df = self.ETF1_df


        #creating the live dataframe
        self.live_df = pd.DataFrame(columns=['time', 'price', measure])
        self.live_df['time'] = pd.to_datetime(self.live_df['time'], format="%Y-%m-%dT%H:%M:%SZ")
        self.live_df.set_index('time', drop=True, inplace = True)

        print(self.ETF_df)
        print(self.ETF1_df)
        #format required by the user


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


    def load_gdax_df(self, granularity, product):
        today = dt.date.today()
        start_date_str = (today - dt.timedelta(days=self.data_days)).isoformat()
        end_date_str = (today + dt.timedelta(days=1)).isoformat()
        print('\nGetting historical data')
        hist_df = get_historic_rates(self.client, product=self.instrument,
                         start_date=start_date_str, end_date=end_date_str,
                         granularity=granularity, beautify=False)
        hist_df = hist_df[['time','open', 'high', 'low', 'close', 'volume']]
        del hist_df['volume']

        hist_df.columns = ['Date', 'O', 'H', 'L', 'C']
        hist_df['Date'] = pd.to_datetime(hist_df['Date'], unit='s')
        hist_df.set_index('Date', inplace=True)
        hist_df.sort_index(inplace=True)
        hist_df = hist_df.groupby(hist_df.index).first()

        return hist_df


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
        if message['Channel'] == "GDAX_data":
            GTD.check_position(message)

        time = message['time']
        new_element = [time , bid_data['price'], bid_data['liquidity']]
        columns_n=['time', 'price' , 'liquidity']

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

    headers = {'instrument': 'BTC-USD',
                'params': {'granularity':"M",
                           'count':5000},
                'access_token': access_token,
                'environment':'practice',
                'ETF1': 'M15',
                'ETF': 'M5',
                'data days':2}

    message = {'bids': [{'liquidity': 10000000, 'price': '1.33045'}],
        'instrument': 'GBP_USD', 'tradeable': True,
        'asks': [{'liquidity': 10000000, 'price': '1.33097'}],
        'closeoutAsk': '1.33122', 'status': 'tradeable', 'time': '2017-11-23T20:44:35.635002033Z',
        'type': 'PRICE', 'closeoutBid': '1.33020'}


    #client = oandapyV20.API(access_token=access_token, environment="practice")
    #instrument='GBP_USD'
    platform = "GDAX"
    #dataf = OandaDataFeeder(accountID, client)
    #dataf.get_live_data(instrument)

    strat = Strategy(platform,**headers)
    #strat.update(message)
    #dataf.pub.register('Oanda_data', strat)
