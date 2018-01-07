from binance.client import Client
from binance.enums import *
import time
import pandas as pd
import datetime as dt 

def binance_historic_rates(client,symbol,interval,start_date,end_date):
	c = client.get_klines(symbol=symbol, interval=interval,
							startTime=start_date,endTime=end_date)
	for i in range(len(c)):
		del c[i][5:]
		c[i][0] = str(dt.datetime.fromtimestamp(c[i][0]/1000))
	dfc = pd.DataFrame(c,columns=["Date","O","H","L","C"])
	return dfc

def main():
	api_key = "kL6SRKiga9VurvzKn4wB26dDs1CbND729o1DhpwRXyzR5ADzo8mLfKyBFuDvCZYm"
	api_secret = "GyWN1cELJRgPk7DJ3re3RgB1lUTbiiDgWpoNfEO81R7vYyu0rXIIh4YPqN2WoWgS"
	client = Client(api_key,api_secret)
	today = dt.datetime.today()
	start_date = int(time.mktime((today - dt.timedelta(days=2)).timetuple()))*1000
	end_date = int(time.mktime((today+dt.timedelta(days=1)).timetuple()))*1000
	df = binance_historic_rates(client,'BTCUSDT',KLINE_INTERVAL_15MINUTE,start_date,end_date)
	print(df)

if __name__ == '__main__':
	main()