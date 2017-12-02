# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 19:39:44 2017

@author: Avanti Financial Services.
"""
import sys
import re
import oandapyV20
from core.GDAX_data_feeder import GDAXClient
from core.data_feeder import OandaDataFeeder
from core.trader import OandaTrader, GDAXTrader
from core.strategy import Strategy
from core.helpers.gdax_auth import Authentication
from config import get_config

class CustomStrategy(Strategy):
    def on_ETF_bar(self, ETF_df, ETF1_df):
        """
        Place your code here.
        """
        print('New bar')
        print(ETF_df, ETF1_df)
        trade = {'Entry Price': 111.08000000000001,
                'Pct of Portfolio': 0.01,
                'Stop Loss': 110.86554000000001,
                'TP1 vs TP2 Split': 0.3,
                'Target Price 1': 162.93000000000001,
                'Target Price 2': 185.14699999999999,
                'Type of Trade': 'LONG',
                'zone_index': 1193}
        self.trader.new_order(trade)
        self.trader.cancel_pending_orders()


def get_arg(index, default):
    try:
        return sys.argv[index]
    except IndexError:
        return default

if __name__ == "__main__":

    """
    model input:
        python live_trader.py --USD_EUR oanda
        python live_trader.py --USD-BTC gdax
    """
    # Config variables

    pair = get_arg(1,"--USD_EUR")
    platform = get_arg(2,"oanda")
    configuration = get_config(platform)

    if platform == "oanda":

        environment = configuration['Environment']
        accountID = configuration['AccountID']
        access_token = configuration['Token']
        instrument = pair.replace("-","")

        headers = {'instrument': instrument,
                    'params': {'granularity':configuration['ETF'],
                               'count':1000},
                    'access_token': access_token,
                    'environment':environment,
                    'ETF1': configuration['ETF1'],
                    'ETF': configuration['ETF']}

        # Instantiate classes.
        client = oandapyV20.API(access_token=access_token,
                                environment="practice")

        data_feeder = OandaDataFeeder(accountID=accountID,
                                api_client=client)
        trader = OandaTrader(accountID=accountID, api_client=client,
                        instrument=instrument)
        strategy = CustomStrategy(trader=trader, **headers)

        data_feeder.pub.register('Oanda_data', strategy)

        # Start data feeder.
        data_feeder.get_live_data(instrument=instrument)
        print('Trader succesfully initialized.')

    elif platform == "gdax":

        #parameters for the GDAX client and strategy class
        pair = re.sub('--','',pair)
        API_KEY = configuration['API_KEY']
        API_SECRET = configuration['API_SECRET']
        API_PASS = configuration['API_PASS']
        request = configuration['request']

        params = {'pair': pair}

        #Authentication
        auth=Authentication(API_KEY, API_SECRET, API_PASS)

        #for authenticated mode
        request.update(auth.get_dict())

        #Initializing client
        ws = GDAXClient(request,pair)
        ws.connect()
