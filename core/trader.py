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


class Trader:
    """
    Makes trades operations using the Oanda API wrapper.
    """
    def __init__(self, accountID, api_client, *args, **kwargs):
        self.accountID = accountID
        self.client = api_client
        self.last_order = None
    
    def place_order(self, _type='market', units=1000, side='buy',
                    instrument='EUR_USD', price=None, stop_loss=None,
                    take_profit=None):
        if take_profit:
            take_profit = TakeProfitDetails(price=take_profit).data

        if stop_loss:
            stop_loss = StopLossDetails(price=stop_loss).data

        if side == 'sell':
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
                                      
        self.last_order = self.client.request(order)
      
    
if __name__ == "__main__":
    """
    For testing purposes.
    """
    import oandapyV20
    from pprint import pprint
    
    accountID = '101-001-1407695-002' 
    access_token = 'f9263a6387fee52f94817d6cd8dca978-d097b210677ab84fb58b4655a33eb25c'
    client = oandapyV20.API(access_token=access_token, environment="practice")
    trader = Trader(accountID, client)
    
    instrument='AUD_CHF'
    units = 10000
    _type = 'limit'
    price = 0.75
    side = 'buy'
    stop_loss = 0.74
    take_profit = 0.76
    
    trader.place_order(_type=_type, 
                       units=units, 
                       side=side,
                       price=price,
                       instrument=instrument,
                       stop_loss=stop_loss,
                       take_profit=take_profit)
    pprint(trader.last_order)
    
    
    
    