# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 14:22:47 2017

@author: Avanti Financial Services.
"""

import json
import oandapyV20
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.orders as orders
import oandapyV20.endpoints.pricing as pricing
from oandapyV20.contrib.requests import (
    MarketOrderRequest,
    TakeProfitDetails,
    StopLossDetails)
from oandapyV20.exceptions import V20Error


accountID = '101-001-1407695-002' 
access_token = 'f9263a6387fee52f94817d6cd8dca978-d097b210677ab84fb58b4655a33eb25c'


client = oandapyV20.API(access_token=access_token, environment="practice")

mktOrder = MarketOrderRequest(instrument="EUR_USD",
                              units=10000,
                              takeProfitOnFill=TakeProfitDetails(price=1.10).data,
                              stopLossOnFill=StopLossDetails(price=1.07).data
                              ).data
r = orders.OrderCreate(accountID=accountID, data=mktOrder)
client.request(r)

instruments = ["EUR_USD", "EUR_JPY"]
s = pricing.PricingStream(accountID=accountID, params={"instruments": ",".join(instruments)})
try:
    n = 0
    for R in client.request(s):
        print(json.dumps(R, indent=2))
        n += 1
        if n > 10:
            s.terminate("maxrecs received: {}".format(10))

except V20Error as e:
    print("Error: {}".format(e))
    
