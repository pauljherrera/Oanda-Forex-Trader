# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 17:23:35 2017

@author: Avanti Financial Services.
"""
import sys
import os

import oandapyV20.endpoints.pricing as pricing
from oandapyV20.exceptions import V20Error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
print(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from core.helpers.pub_sub import Publisher


class OandaDataFeeder:
    """
    Gets live data from Oanda. Uses a publisher class to feed the data to
    other components.
    """
    def __init__(self, accountID, api_client, *args, **kwargs):
        self.accountID = accountID
        self.client = api_client
        self.pub = Publisher(['new_data'])
        
    def filter_data(self, data):
        """
        Filters the necessary data and publishes it.
        """
        if data['type'] == 'PRICE':
            self.pub.dispatch('new_data', data)
        
    def get_live_data(self, instrument='EUR_USD'):
        """
        Subscribes to the stream of data of an instrument.
        """
        s = pricing.PricingStream(accountID=self.accountID, 
                                  params={"instruments": instrument})
        try:
            for resp in self.client.request(s):
                self.filter_data(resp)
        
        except V20Error as e:
            print("Error: {}".format(e))
            
if __name__ == "__main__":
    """
    For testing purposes.
    """
    import oandapyV20
    from core.helpers.pub_sub import Subscriber
    
    accountID = '101-001-1407695-002' 
    access_token = 'f9263a6387fee52f94817d6cd8dca978-d097b210677ab84fb58b4655a33eb25c'
    client = oandapyV20.API(access_token=access_token, environment="practice")
    instrument='GBP_USD'
    dataf = OandaDataFeeder(accountID, client)
    
    sub = Subscriber('sub')
    dataf.pub.register('new_data', sub)
    
    dataf.get_live_data(instrument)

        
    


