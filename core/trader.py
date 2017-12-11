# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 17:32:50 2017

@author: Avanti Financial Services.
"""

import sys
import os
import requests
import json

from apscheduler.schedulers.background import BackgroundScheduler
from math import floor
from dateutil import parser
import numpy as np
import pandas as pd

import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.accounts as accounts
from oandapyV20.contrib.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopOrderRequest,
    TakeProfitDetails,
    StopLossDetails)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from core.helpers.format_order import round_values
from core.helpers.gdax_api import GDAX_Handler
from core.helpers.gdax_auth import Authentication
from core.helpers.order_book import get_dataframe

class OandaTrader:
    """
    Makes trades operations using the Oanda API wrapper.
    """
    def __init__(self, accountID, api_client, instrument=None,
                 leverage=100, *args, **kwargs):
        self.accountID = accountID
        self.client = api_client
        self.last_order = None
        self.instrument = instrument
        self.leverage = leverage
        self.get_margin_available()
        self.round_value = 5 if not 'JPY' in self.instrument else 3

        # Initializing daemon for getting account balance
        scheduler = BackgroundScheduler()
        scheduler.add_job(self.get_margin_available , 'interval', minutes=1)
        scheduler.start()

    def get_margin_available(self):
        a = accounts.AccountDetails(self.accountID)
        r = self.client.request(a)
        self.margin_available = float(r['account']['marginAvailable'])

    def cancel_pending_orders(self, date=None):
        """
        Cancels the pending limit orders. If a date specified,
        cancels the orders before that date.
        Returns the IDs of the canceled orders.
        """
        # Retrieving orders.
        r = orders.OrdersPending(self.accountID)
        pending_orders = self.client.request(r)
        limit_orders = [order for order in pending_orders['orders']
                        if order['type'] == 'LIMIT']

        if date:
            orders_id = [x['id'] for x in limit_orders
                         if parser.parse(x['createTime']).replace(tzinfo=None) <= date]
        else:
            orders_id = [x['id'] for x in limit_orders]

        # Canceling orders.
        for _id in orders_id:
            r = orders.OrderCancel(self.accountID, orderID=_id)
            self.client.request(r)
        print('{} order(s) canceled.'.format(len(orders_id)))

        return orders_id


    def new_order(self, trade):
        """
        This class will be called by the strategy to place new orders.
        The input is a dictionary like:
            {'Entry Price': float,
            'Pct of Portfolio': float,
            'Stop Loss': float,
            'TP1 vs TP2 Split': float,
            'Target Price 1': float,
            'Target Price 2': float,
            'Type of Trade': <'LONG'/'SHORT'>}
        """
        trade = round_values(trade,self.round_value)
        units = self.margin_available * trade['Pct of Portfolio'] * self.leverage

        r1 = self._place_order(_type='limit',
                        units=floor(units * trade['TP1 vs TP2 Split']),
                        side=trade['Type of Trade'],
                        instrument=self.instrument,
                        price=trade['Entry Price'],
                        stop_loss=trade['Stop Loss'],
                        take_profit=trade['Target Price 1'])

        r2 = self._place_order(_type='limit',
                        units=floor(units * (1 - trade['TP1 vs TP2 Split'])),
                        side=trade['Type of Trade'],
                        instrument=self.instrument,
                        price=trade['Entry Price'],
                        stop_loss=trade['Stop Loss'],
                        take_profit=trade['Target Price 2'])
#        print(r1, r2)

        print('\nNew orders opened.')
        print('Entry price: {}'.format(trade['Entry Price']))
        print('Stop Loss: {}'.format(trade['Stop Loss']))
        print('Take profits: {} , {}'.format(trade['Target Price 1'],
                                             trade['Target Price 2']))

    def _place_order(self, _type='market', units=1000, side='LONG',
                    instrument='EUR_USD', price=None, stop_loss=None,
                    take_profit=None):
        if take_profit:
            take_profit = TakeProfitDetails(price=take_profit).data

        if stop_loss:
            stop_loss = StopLossDetails(price=stop_loss).data

        if side == 'SHORT':
            units = -units

        if _type == 'market':
            mktOrder = MarketOrderRequest(instrument=instrument,
                                          units=units,
                                          takeProfitOnFill=take_profit,
                                          stopLossOnFill=stop_loss
                                          ).data
            order = orders.OrderCreate(accountID=self.accountID, data=mktOrder)
        elif _type == 'stop':
            stopOrder = StopOrderRequest(instrument=instrument,
                                          units=units,
                                          price=price,
                                          takeProfitOnFill=take_profit,
                                          stopLossOnFill=stop_loss
                                          ).data
            order = orders.OrderCreate(accountID=self.accountID, data=stopOrder)
        elif _type == 'limit':
            limitOrder = LimitOrderRequest(instrument=instrument,
                                          units=units,
                                          price=price,
                                          takeProfitOnFill=take_profit,
                                          stopLossOnFill=stop_loss
                                          ).data
            order = orders.OrderCreate(accountID=self.accountID, data=limitOrder)

        return self.client.request(order)

class GDAXTrader(GDAX_Handler):

    def __init__(self,auth=None, sandbox=False, *args,**kwargs):
        super().__init__(auth=auth, sandbox=sandbox, *args, **kwargs)
        self.url = super().get_url()
        self.columns = ['created_at', 'id', 'Price', 'Stop Loss',
                        'Target Price', 'size', 'status']
        self.order_df = pd.DataFrame(columns=self.columns)

    def new_order(self, trade):

        """
        {'Entry Price': float,
        'Pct of Portfolio': float,
        'Stop Loss': float,
        'TP1 vs TP2 Split': float,
        'Target Price 1': float,
        'Target Price 2': float,
        'Type of Trade': <'LONG'/'SHORT'>}
        """

        size = round(self.margin_available() / trade['Entry Price'] * trade['Pct of Portfolio'], 5)
        self.stop_l = trade['Stop Loss']
        self.target_1 = trade['Target Price 1']
        self.target_2 = trade['Target Price 2']

        print(size)

        r1 = self.place_order(
                            _type = 'limit',
                            size = size * trade['TP1 vs TP2 Split'],
                            side = 'buy',
                            product_id = self.order_dict['product_id'] ,
                            price = trade['Entry Price'],
                            verbose=True)
        
        r2 = self.place_order(
                            _type = 'limit',
                            size = size * (1 - trade['TP1 vs TP2 Split']),
                            side = 'buy',
                            product_id = self.order_dict['product_id'],
                            price = trade['Entry Price'],
                            verbose=True)
        
        if (r1.status_code == 200) and (r2.status_code == 200):
            print('\nNew orders opened.')
            print('Entry price: {}'.format(trade['Entry Price']))
            print('Stop Loss: {}'.format(trade['Stop Loss']))
            print('Take profits: {} , {}'.format(trade['Target Price 1'],
                                                 trade['Target Price 2']))
    
            """
            creating dataframe to get a record of the orders
            And the values of stop loss and target price to execute
            them precisely
            """
            self.load_orders(r1,r2)
        
        else:
            print("Trade 1 status: {}".format(r1.text))
            print("Trade 2 status: {}".format(r2.text))
            

    def load_orders(self, order1, order2):
        #load the new orders into a dataframe
        r1 = json.loads(order1.text)
        r2 = json.loads(order2.text)


        r1['Stop Loss'] = self.stop_l
        r1['Target Price'] = self.target_1

        r2['Stop Loss'] = self.stop_l
        r2['Target Price'] = self.target_2

        new_ords = get_dataframe(r1,r2,self.columns)

        self.order_df = pd.concat([self.order_df, new_ords])


    def place_order(self, _type='limit', size='0.01', side='buy',
                    product_id='BTC-USD', price=None, verbose=True):
        order = super().place_order(_type=_type, size=size, side=side,
                                    product_id=product_id, price=price,
                                    verbose=verbose)
        self.last_order = order
        
        return order

    def close_last_order(self):
        # Setting parameters.
        if self.order_dict['side'] == 'buy':
            side = 'sell'
        elif self.order_dict['side'] == 'sell':
            side = 'buy'
        size = self.order_dict['size']
        product_id = self.order_dict['product_id']

        # Placing trade.
        order = self.place_order(size=size, side=side, product_id=product_id,
                                 verbose=False)
        self.last_order = order

        super().close_last_order()

    def list_orders(self,product_id = 'BTC-USD', status = ['open']):

        orders = super().list_orders(product_id = product_id, status = status)

        return orders

    def cancel_pending_orders(self, date=None):
        res = super().cancel_pending_orders(date)
        print('{} order(s) canceled.'.format(res))

    def check_position(self, tick):
        """
            check which orders comply with their corresponding...
            Stop Loss and Target price values and real time data

            if there's is stop loss values that match with the specified in the trade parameters:
                search in the df the orders with the correspondent stop loss value and
                the status "done" in order to place a stop order with
                the size of the 'filled_size' in the original limit order

            same with target price, in this one the order will be of type limit

        """
        data = self.order_df
        price = tick['price']

        if len(data.index) != 0:
            self.stop_orders = data.loc[price <= data['Stop Loss']]\
                                        [['id','Stop Loss','size']]
            self.target_orders = data.loc[price >= data['Target Price']]\
                                        [['id','Target Price']]

            if len(self.stop_orders.index) != 0:
                for index,row in self.stop_orders.iterrows():
                    #getting the actual status of each order
                    r = requests.get(self.url + '/orders/{}'.format(row['id']))
                    r = json.loads(r.text)
                    if r['status'] == 'done':
                        self.place_order(_type='stop', side='sell',
                                            price=row['Stop Loss'],
                                            size=r['filled_size'])
                        #deletes the orders with status done and processed
                        self.order_df = self.order_df[self.order_df['id'] != row['id']]

            if  len(self.target_orders.index) != 0:
                for index,row in self.target_orders.iterrows():
                    r = requests.get(self.url + '/orders/{}'.format(row['id']))
                    r = json.loads(r.text)
                    if r['status'] == 'done':
                        self.place_order(_type='limit', side='sell',
                                            price=row['Target Price'],
                                            size=r['filled_size'])
                        self.order_df = self.order_df[self.order_df['id'] != row['id']]


if __name__ == "__main__":
    """
    For testing purposes.
    """
    import oandapyV20

    instrument='USD_JPY'
    accountID = '101-001-1407695-002'
    access_token = 'f9263a6387fee52f94817d6cd8dca978-d097b210677ab84fb58b4655a33eb25c'
    client = oandapyV20.API(access_token=access_token, environment="practice")
    trader = OandaTrader(accountID, client, instrument=instrument)

    units = 10000
    _type = 'limit'
    price = 0.75
    side = 'buy'
    stop_loss = 0.74
    take_profit = 0.76

    trade = {'Entry Price': 111.08000000000001,
            'Pct of Portfolio': 0.01,
            'Stop Loss': 110.86554000000001,
            'TP1 vs TP2 Split': 0.3,
            'Target Price 1': 162.93000000000001,
            'Target Price 2': 185.14699999999999,
            'Type of Trade': 'LONG',
            'zone_index': 1193}

    trader.new_order(trade)


    API_key = ''
    passphrase = ''
    secret = ''

    # Instantianting the objects needed.
    auth = Authentication(api_key=API_key, secret_key=secret, passphrase=passphrase)
    GDAX_trader = GDAXTrader()
