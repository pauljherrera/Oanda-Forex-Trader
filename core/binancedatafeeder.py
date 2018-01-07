# coding=utf-8
"""
Created 02/01/2018 

"""

import threading
import asyncio
import json
import websockets as ws
import time
from datetime import datetime as dt
from core.helpers.pub_sub import Publisher
from binance.client import Client


class BinanceDataFeeder():
    _stream_url = 'wss://stream.binance.com:9443/'
    _stream_url_multi = 'wss://stream.binance.com:9443/stream?streams='
    def __init__(self, client,channels=['btcusdt'],intervals=['5m']):
        """
        Initialise the Binance socket
        :param client: Binance API client
        :type client: binance.Client
        :param channels: list of binance symbols in lowercase
        :type channels: list
        :param intervals: list of kline intervals in format '1m','5m', etc
        :type intervals: str from enumerate http://python-binance.readthedocs.io/en/latest/enums.html in KLINES section
        """
        #Initializers
        self._conns = {}
        self._loop = asyncio.get_event_loop()
        self._pub = Publisher(channels)
        self._symbols = channels
        self._intervals = intervals
        self._pub=Publisher(['Binance_data'])
        self._stop = False
        self._client = client
        self._last_open = 0
    def _on_message(self,mess):
        #print(mess)
        if mess['k']['t'] != self._last_open:  #candlestick open so it dispatch what it has to
            self._last_open = mess['k']['t']
            self._pub.dispatch('Binance_data',mess)
    def _on_error(self):
        self._stop = True
        print("An error ocurred handling received data.")
        self._on_message(self._last_mess)
    def _start_socket(self, path,multi=False,prefix='ws/'):
        #completes the url
        if path in self._conns:
            return False
        if not multi:
            ws_url = self._stream_url + prefix + path
        else:
            ws_url = self._stream_url_multi + path
        print("Connected to: ",ws_url)
        async def _watch_for_events():
            async with ws.connect(ws_url) as socket:
                    while not self._stop:
                        try:                    
                            if int(time.time())%30==0:
                                print("pinging")
                                socket.ping()
                            event = await socket.recv()
                            dict_event=json.loads(event)
                            self._on_message(dict_event)
                        except:
                            socket.close()
                            self._on_error()
        self._loop.run_until_complete(_watch_for_events())
    def start_live_data(self):
        #builds the path for one or more coins and intervals
        if len(self._symbols) == 1 and len(self._intervals) == 1:
            socket_name = '{}@kline_{}'.format(self._symbols[0], self._intervals[0])
            multi = False
        else:
            first = True
            multi = True
            socket_name = ""
            for sy in self._symbols:
                for itv in self._intervals:
                    if not first:
                        socket_name+="/"
                    socket_name+="{}@kline_{}".format(sy,itv)
                    first = False     
        t = threading.Thread(target=self._start_socket(socket_name,multi))
        t.start()
        

def main():
    api_key = "kL6SRKiga9VurvzKn4wB26dDs1CbND729o1DhpwRXyzR5ADzo8mLfKyBFuDvCZYm"
    api_secret = "GyWN1cELJRgPk7DJ3re3RgB1lUTbiiDgWpoNfEO81R7vYyu0rXIIh4YPqN2WoWgS"
    client = Client(api_key,api_secret)
    dest = {}
    klinesocket = BinanceDataFeeder(client,['btcusdt'],['5m'])
    klinesocket.start_live_data()

if __name__ == '__main__':
    main()