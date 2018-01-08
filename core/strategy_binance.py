import pandas as pd
import datetime as dt
import time
from binance.client import Client
from binance.enums import *
from datetime import datetime as dtime
from apscheduler.schedulers.background import BackgroundScheduler
from core.helpers.pub_sub import Subscriber
from core.helpers.binance_helper import binance_historic_rates
from core.binancedatafeeder import BinanceDataFeeder

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
		"""Scheduler"""
		scheduler = BackgroundScheduler()
		if self.ETF[0] == 'M':
			scheduler.add_job(self.update_dfs, trigger='cron',
								minute='*/{}'.format(self.ETF[1:]))
		elif self.ETF[0] == 'H':
			scheduler.add_job(self.update_dfs, trigger='cron',
								hour='*/{}'.format(self.ETF[1:]))
		scheduler.start()
		"""Scheduler"""
		self.ETF_df.to_csv("ETF.csv", index=False)
		self.ETF1_df.to_csv("ETF1.csv",index=False)
		self.on_ETF_bar(self.ETF_df,self.ETF1_df)
	def update(self,message):
		#get the open time of the candlestick and the  ohlc and adds it to the right dataframe
		lmess = [str(dt.datetime.fromtimestamp(message['k']['t']/1000)),message['k']['o'],message['k']['h'],
												message['k']['l'],message['k']['c']]
		if message['k']['i'] == self.timeframes[self.ETF]:
			if str(dt.datetime.fromtimestamp(message['k']['t']/1000)) != self.ETF_df.iloc[-1]['Date']:
				self.live_ETF.loc[len(self.ETF_df.index+1)]=lmess
		else:
			if str(dt.datetime.fromtimestamp(message['k']['t']/1000)) != self.ETF1_df.iloc[-1]['Date']:
				self.live_ETF1.loc[len(self.ETF_df.index+1)]=lmess
	def update_dfs(self):
		print("saving")
		self.ETF_df = pd.concat([self.ETF_df,self.live_ETF])
		self.ETF1_df = pd.concat([self.ETF1_df,self.live_ETF1])
		self.live_ETF = pd.DataFrame(columns=["Date","O","H","L","C"])
		self.live_ETF1 = pd.DataFrame(columns=["Date","O","H","L","C"])
		self.ETF_df.to_csv("ETF.csv", index=False)
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
	client = Client(binance['API_KEY'],binance['API_SECRET'])
	dfeeder = BinanceDataFeeder(client,['btcusdt'],['5m','15m'])
	s = Strategy_Binance(**binance)
	dfeeder.pub.register('Binance_data', s)
	dfeeder.start_live_data()


if __name__ == '__main__':
	main()