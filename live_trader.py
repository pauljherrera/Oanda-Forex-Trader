# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 19:39:44 2017

@author: Avanti Financial Services.
"""
import sys
import re
import oandapyV20
from core.GDAX_data_feeder import GDAXDataFeeder
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
        trade = {'Entry Price': 12000,
                'Pct of Portfolio': 0.2,
                'Stop Loss': 10000,
                'TP1 vs TP2 Split': 0.5,
                'Target Price 1': 20000,
                'Target Price 2': 21000,
                'Type of Trade': 'LONG',
                'zone_index': 1193}
        self.trader.new_order(trade)
#        self.trader.cancel_pending_orders()

def get_arg(index, default):
    try:
        return sys.argv[index]
    except IndexError:
        return default

if __name__ == "__main__":

    """
    model input:
        python live_trader.py --USD_EUR Oanda
        python live_trader.py --USD-BTC GDAX
    """
    # Config variables

    pair = get_arg(1, "--BTC-USD")
    platform = get_arg(2, "GDAX")
    configuration = get_config(platform)

    if platform == "Oanda":

        environment = configuration['Environment']
        accountID = configuration['AccountID']
        access_token = configuration['Token']
        instrument = pair.replace("-","")

        headers = {'instrument': instrument,
                    'params': {'granularity':configuration['ETF'],
                               'count':configuration['Data candles']},
                    'access_token': access_token,
                    'environment': environment,
                    'ETF1': configuration['ETF1'],
                    'ETF': configuration['ETF']}

        # Instantiate classes.
        client = oandapyV20.API(access_token=access_token,
                                environment="practice")

        data_feeder = OandaDataFeeder(accountID=accountID,
                                api_client=client)
        trader = OandaTrader(accountID=accountID, api_client=client,
                        instrument=instrument)

        strategy = CustomStrategy(trader=trader,platform="Oanda", **headers)

        data_feeder.pub.register('Oanda_data', strategy)

        # Start data feeder.
        data_feeder.get_live_data(instrument=instrument)
        print('Trader succesfully initialized.')

    elif platform == "GDAX":

        #parameters for the GDAX client and strategy class
        pair = re.sub('--','',pair)
        API_KEY = configuration['API_KEY']
        API_SECRET = configuration['API_SECRET']
        API_PASS = configuration['API_PASS']
        request = configuration['request']
        ETF = configuration['ETF']
        ETF1 = configuration['ETF1']
        data_days = configuration['data_days']

        params = {'instrument': pair,
                    'ETF': ETF,
                    'ETF1': ETF1,
                    'data_days': data_days}

        #Authentication
        auth=Authentication(api_key=API_KEY, secret_key=API_SECRET, passphrase=API_PASS)

        #initialization
        data_feeder = GDAXDataFeeder(request,[pair])


        trader = GDAXTrader(auth=auth)

        strategy = CustomStrategy(trader=trader,sandbox=True, **params)

        data_feeder.pub.register('GDAX_data', strategy)

        data_feeder.start_live_data()
        print("Trader succesfully initialized.")
