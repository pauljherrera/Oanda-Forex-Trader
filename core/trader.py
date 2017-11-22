# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 17:32:50 2017

@author: Avanti Financial Services.
"""
import oandapyV20.endpoints.orders as orders
from oandapyV20.contrib.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopOrderRequest,
    TakeProfitDetails,
    StopLossDetails)

from math import floor


class Trader:
    """
    Makes trades operations using the Oanda API wrapper.
    """
    def __init__(self, accountID, api_client, instrument=None, *args, **kwargs):
        self.accountID = accountID
        self.client = api_client
        self.last_order = None
        self.instrument = instrument
        
    def get_volume(self, percentage):
        """
        TODO: apply money management.
        """
        return 10000
        
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
        units = self.get_volume(trade['Pct of Portfolio'])
        
        pprint(self.place_order(_type='limit', 
                        units=floor(units * trade['TP1 vs TP2 Split']), 
                        side=trade['Type of Trade'],
                        instrument=self.instrument, 
                        price=trade['Entry Price'], 
                        stop_loss=trade['Stop Loss'],
                        take_profit=trade['Target Price 1']))
        
        pprint(self.place_order(_type='limit', 
                        units=floor(units * (1 - trade['TP1 vs TP2 Split'])), 
                        side=trade['Type of Trade'],
                        instrument=self.instrument, 
                        price=trade['Entry Price'], 
                        stop_loss=trade['Stop Loss'],
                        take_profit=trade['Target Price 2']))
        
    
    def place_order(self, _type='market', units=1000, side='LONG',
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
            print()
            limitOrder = LimitOrderRequest(instrument=instrument,
                                          units=units,
                                          price=price,
                                          takeProfitOnFill=take_profit,
                                          stopLossOnFill=stop_loss
                                          ).data
            order = orders.OrderCreate(accountID=self.accountID, data=limitOrder)
                                      
        return self.client.request(order)
      
    
if __name__ == "__main__":
    """
    For testing purposes.
    """
    import oandapyV20
    from pprint import pprint
    
    instrument='USD_JPY'
    accountID = '101-001-1407695-002' 
    access_token = 'f9263a6387fee52f94817d6cd8dca978-d097b210677ab84fb58b4655a33eb25c'
    client = oandapyV20.API(access_token=access_token, environment="practice")
    trader = Trader(accountID, client, instrument=instrument)
    
    units = 10000
    _type = 'limit'
    price = 0.75
    side = 'buy'
    stop_loss = 0.74
    take_profit = 0.76
    
    trade = {'Entry Price': 111.08000000000001,
            'Pct of Portfolio': 0.03,
            'Stop Loss': 110.86500000000001,
            'TP1 vs TP2 Split': 0.5,
            'Target Price 1': 162.93000000000001,
            'Target Price 2': 185.14699999999999,
            'Type of Trade': 'LONG',
            'zone_index': 1193}
    
    trader.new_order(trade)
    
    
    
    