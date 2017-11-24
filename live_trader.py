# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 19:39:44 2017

@author: Avanti Financial Services.
"""
import oandapyV20

from core.data_feeder import OandaDataFeeder
from core.trader import Trader
from core.strategy import Strategy
from config import configuration

class CustomStrategy(Strategy):
    def on_ETF_bar(self, ETF_df, ETF1_df):
        """
        Place your code here.
        """
        print('New bar')
        print(ETF_df, ETF1_df)
        
        

        
if __name__ == "__main__":
    # Config variables
    environment = configuration['Environment']
    accountID = configuration['AccountID']
    access_token = configuration['Token']
    instrument = configuration['Instrument']
    headers = {'instrument': instrument,
                'params': {'granularity':"M{}".format(configuration['ETF']), 
                           'count':1000},
                'access_token': access_token,
                'environment':environment,
                'ETF1': configuration['ETF1'],
                'ETF': configuration['ETF']} 
               
    # Instantiate classes.
    client = oandapyV20.API(access_token=access_token, 
                            environment="practice")
    trader = Trader(accountID=accountID, api_client=client, 
                    instrument=instrument)
    data_feeder = OandaDataFeeder(accountID=accountID, 
                            api_client=client)   
    strategy = CustomStrategy(**headers)
    strategy.trader = trader
    data_feeder.pub.register('new_data', strategy)
    
    # Start data feeder.
    data_feeder.get_live_data(instrument=instrument)
    print('Trader succesfully initialized.')
    
