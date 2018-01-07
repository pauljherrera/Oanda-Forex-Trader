import pandas as pd
import datetime as dt
import time
from binance.client import Client
from binance.enums import *
from datetime import datetime as dtime
from core.helpers.pub_sub import Subscriber
from core.helpers.binance_helper import binance_historic_rates

class Strategy_Binance(Subscriber):
	def __init__(self,plataform='Binance_data',*args,**kwargs):
		self.timeframes = { 'M1': KLINE_INTERVAL_1MINUTE,
							'M3': KLINE_INTERVAL_3MINUTE,
							'M5': KLINE_INTERVAL_5MINUTE,
							'M15': KLINE_INTERVAL_15MINUTE,
							'M30': KLINE_INTERVAL_30MINUTE,
							'H1': KLINE_INTERVAL_1HOUR,
							'H2': KLINE_INTERVAL_2HOUR,
							'H4': KLINE_INTERVAL_4HOUR,
							'H6': KLINE_INTERVAL_6HOUR,
							'H8': KLINE_INTERVAL_8HOUR,
							'H12': KLINE_INTERVAL_12HOUR }
		#Initializers
		self.plataform = plataform
		self.client = Client(kwargs['API_KEY'],kwargs['API_SECRET'])
		self.ETF = kwargs['ETF']
		self.ETF1 = kwargs['ETF1']
		self.live_ETF = pd.DataFrame(columns=["Date","O","H","L","C"])
		self.live_ETF1 = pd.DataFrame(columns=["Date","O","H","L","C"])
		#calculate the start of the historics
		today = dt.datetime.today()
		start_date = int(time.mktime((today - dt.timedelta(days=kwargs['data_days'])).timetuple()))*1000
		end_date = int(time.mktime((today+dt.timedelta(days=1)).timetuple()))*1000
		self.ETF_df = binance_historic_rates(self.client,kwargs['symbol'],self.timeframes[self.ETF],start_date,end_date)
		self.ETF1_df = binance_historic_rates(self.client,kwargs['symbol'],self.timeframes[self.ETF1],start_date,end_date)
		"""
		Scheduler
		"""
		self.ETF_df.to_csv("ETF.csv", index=False)
		self.ETF1_df.to_csv("ETF1.csv",index=False)
		self.on_ETF_bar(self.ETF_df,self.ETF1_df)
	def update(self,mess):
		#get the open time of the candlestick and the  ohlc and adds it to the right dataframe
		lmess = [str(dt.datetime.fromtimestamp(mess['k']['t']/1000)),mess['k']['o'],mess['k']['h'],mess['k']['l'],mess['k']['c']]
		if mess['k']['i'] == self.timeframes[self.ETF]:
			self.ETF_df.loc[len(self.ETF_df.index+1)]=lmess
			self.ETF_df.to_csv("ETF.csv", index=False)
		else:
			self.ETF1_df.loc[len(self.ETF_df.index+1)]=lmess
			self.ETF1_df.to_csv("ETF1.csv",index=False)
		self.on_ETF_bar(self.ETF_df,self.ETF1_df)
	def on_ETF_bar(self, ETF_df, ETF1_df):
		"""
		Method that will be overriden by the user.
		"""
		#print(ETF_df,"\n\n\n")
		#print(ETF1_df)

def main():
	binance = {'API_KEY':"kL6SRKiga9VurvzKn4wB26dDs1CbND729o1DhpwRXyzR5ADzo8mLfKyBFuDvCZYm",
				'API_SECRET':"GyWN1cELJRgPk7DJ3re3RgB1lUTbiiDgWpoNfEO81R7vYyu0rXIIh4YPqN2WoWgS",
				'data_days':1, 'ETF' : 'M5', 'ETF1' : 'M15', 'symbol': 'BTCUSDT'}
	mess = {'e': 'kline', 'E': 1515293744333, 's': 'BTCUSDT', 'k': {'t': 1515293700000, 
			'T': 1515293999999, 's': 'BTCUSDT', 'i': '5m', 'f': 5246352, 'L': 5246410, 
			'o': '16746.59000000', 'c': '16771.98000000', 'h': '16772.00000000', 'l': '16732.00000000',
			'v': '10.38784000', 'n': 59, 'x': False, 'q': '174107.48574958',
			'V': '8.16052300', 'Q': '136765.29006706', 'B': '0'}}
	s = Strategy_Binance(**binance)
	s.update(mess)


if __name__ == '__main__':
	main()