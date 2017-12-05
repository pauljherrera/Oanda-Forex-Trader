# -*- coding: utf-8 -*-
"""
Created on Wed Nov  1 19:23:23 2017

@author: Paul Herrera
"""

import requests
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
from core.helpers.gdax_auth import Authentication


class GDAX_Handler:
    def __init__(self, auth=None, sandbox=False, *args, **kwargs):
        if sandbox:
            self.url = 'https://api-public.sandbox.gdax.com'
        else:
            self.url = 'https://api.gdax.com'
        self.order_dict = {
            "type": "limit",
            "size": "0.01",
            "price": "0.100",
            "side": "buy",
            "product_id": "BTC-USD"
        }

        self.auth = auth

    def get_ticker(self, product_id):
        r = requests.get(self.url + '/products/{}/ticker'.format(product_id))
        if r.status_code == 200:
            return json.loads(r.text)
        else:
            print("Error in response.")

    def list_accounts(self):
        r = requests.get(self.url + '/accounts', auth=self.auth)
        if r.status_code == 200:
            return json.loads(r.text)
        else:
            print("Error in response.")

    def place_order(self, _type='limit', size='0.01', side='buy',
                    product_id='BTC-USD', price=None, verbose=True):
        # Creating trade JSON.
        order_dict = {}
        order_dict['type'] = _type
        order_dict['size'] = size
        order_dict['side'] = side
        order_dict['product_id'] = product_id

        if _type == 'limit':
            order_dict['price'] = price
            assert(order_dict['price'] != None)
        elif _type == 'stop':
            order_dict = {'type':order_dict['type'],
                        'size':order_dict['size'],'price':order_dict}

        self.order_dict = order_dict

        # Placing trade.
        r = requests.post(self.url + '/orders', data=json.dumps(order_dict),
                          auth=self.auth)
        if r.status_code == 200:
            if verbose:
                print('\nNew order: {}, {}, {}'.format(product_id, side, size))
            return json.loads(r.text)
        else:
            print("Error in response.")
            return r

    def list_orders(self, product_id='', status=[]):
        """
        Return a list of orders of the specified product and
        status.
            status = ['open']
            product_id = 'BTC-USD'
        """
        r = self.url + '/orders/'
        result = []
        params = {}

        if product_id:
            params["product_id"] = product_id
        if status:
            params["status"] = status
        r = requests.get(url, auth=self.auth, params=params, timeout=30)

        result.append(r.json())
        if 'cb-after' in r.headers:
            self.paginate_orders(product_id, status, result, r.headers['cb-after'])
        return result

    def paginate_orders(self, product_id, status, result, after):
        r = self.url + '/orders'

        params = {
            "after": str(after),
        }
        if product_id:
            params["product_id"] = product_id
        if status:
            params["status"] = status
        r = requests.get(url, auth=self.auth, params=params, timeout=30)
        if r.json():
            result.append(r.json())
        if 'cb-after' in r.headers:
            self.paginate_orders(product_id, result, r.headers['cb-after'])
        return result

    def cancel_pending_orders(self, date=None):
        """
        Cancels the pending limit orders. If a date specified,
        cancels the orders before that date.
        Returns the IDs of the canceled orders.
        """
        orders = self.list_orders(status=['open'])

        limit_orders = [order for order in orders if order['type'] == 'limit']

        if date:
            canceled_orders = [order['id'] for order in limit_orders
                        if order['created_at'] <= date]
        else:
            canceled_orders = [order['id'] for order in limit_orders]

        for ord_id in canceled_orders:
            res = requests.delete(self.url + '/orders/' + ord_id, auth=self.auth, timeout=30)

        return len(canceled_orders)

    def margin_available(self):
        r = requests.get(self.url + '/accounts', auth=self.auth)
        available = float(r.json()['available'])
        return available

if __name__ == '__main__':
    # API keys.
    API_key = 'c2c736241299f78327809504d2ffb0e7'
    passphrase = 'si3b5hm7609'
    secret = 'xzYSvcKvfP8Nx1uS+FxK7yWtoSfJplenN0vv9zGywfQcjTqEfqTmvGWsGixSQHCtkh9JdNoncEU1rEL1MXDWkA=='

    # Instantianting the objects needed.
    auth = Authentication(api_key=API_key, secret_key=secret, passphrase=passphrase)
    gdax = GDAX_Handler(auth=auth)
