#!/usr/bin/env python
# coding: utf-8

# In[4]:


import hashlib
import hmac
import json
import time
import datetime
import urllib
import requests


# In[2]:


############### Parameters ############################################################################
# How much to buy (in yen)
budget = 400

# API key
api_key = ""

# API secret
api_secret = ""

#######################################################################################################


# In[3]:


##### Define global_nonce #####
# Zaif only allows 1 trading api calls per second
global_nonce = int(time.time())


# In[4]:


class zaif:
    """API class for Zaif
    Be sure to use your own api_key and api_secret
    Parameters
        pair: specify which trading pair
            "btc_jpy" for btc-jpy pair
            "eth_jpy" for eth-jpy pair
        coin: specify which currency
            "jpy" for jpy
            "btc" for btc
            "ETH" for eth            
        count: number of records to retrieve        
    """

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.get_api_endpoint = "https://api.zaif.jp/api/1/"
        self.trading_api_endpoint = "https://api.zaif.jp/tapi"

    def get_api_call(self, method, path=""):
        """Request public information from Zaif
        Api key not required
        """
        url = self.get_api_endpoint + method
        if path != "":
            url = url + "/" + path
        request_data = requests.get(url)
        return request_data

    def get_pair_info(self, pair="eth_jpy"):
        pair_info = self.get_api_call("currency_pairs/{}".format(pair)).json()
        pair_info = pair_info[0]
        return pair_info
    
    def get_board(self, pair="eth_jpy"):
        board = self.get_api_call("depth", pair).json()
        asks = board["asks"]
        bids = board["bids"]
        return asks, bids
    
    def get_highest_bid(self):
        asks, bids = self.get_board(pair="eth_jpy")
        bids_price = [x[0] for x in bids]
        highest_bid = bids_price[0]
        return highest_bid    

    def trading_api_call(self, method, req={}):
        """Request personal information from Zaif
        Api key required
        """
        global global_nonce
        while global_nonce == int(time.time()):
            time.sleep(0.1)
        global_nonce = int(time.time())
        req["method"] = method
        req["nonce"] = int(time.time())
        post_data = urllib.parse.urlencode(req).encode()
        sign = hmac.new(
            str.encode(self.api_secret), post_data, hashlib.sha512
        ).hexdigest()
        request_data = requests.post(
            self.trading_api_endpoint,
            data=post_data,
            headers={
                "key": self.api_key,
                "sign": sign,
            },
        )
        return request_data

    def my_balance(self, coin="jpy"):
        result = self.trading_api_call("get_info").json()
        #print(result["success"])
        data = {}
        funds = result["return"]["funds"]
        deposit = result["return"]["deposit"]
        amount = round(float(funds[coin]), 8)
        available = round(float(deposit[coin]), 8)
        return amount, available
  
    def trade_history(self, pair="eth_jpy", count=10, req={}):
        req["currency_pair"] = pair
        req["count"] = count
        result = self.trading_api_call("trade_history", req).json()
        return result

    def active_orders(self, pair="eth_jpy", req={}):
        req["currency_pair"] = pair
        result = self.trading_api_call("active_orders", req).json()
        return result
    
    def trade(self, pair="eth_jpy", action="bid", price=0, amount=0, req={}):
        req["currency_pair"] = pair
        req["action"] = action
        req["price"] = price
        req["amount"] = amount
        result = self.trading_api_call("trade", req).json()
        return result    
    
    def cancel_order(self, orders, pair="eth_jpy", req={}):
        for order in orders:
            req["order_id"] = order
            req["currency_pair"] = pair
            result = self.trading_api_call("cancel_order", req).json()
    
    def cancel_all_orders(self):
        orders = self.active_orders()
        order_ids = [k for k, v in orders["return"].items()]
        self.cancel_order(order_ids)
    
api = zaif(api_key, api_secret)


# In[ ]:


print("Job starting at {}".format(datetime.datetime.now()))

##### Cancel all orders #####
api.cancel_all_orders()
print("All orders cancelled")

##### Get decimal limit #####
currency_info = api.get_pair_info()
decimal_length = len(str(currency_info['item_unit_step']))-2

##### Place order at the highest bid price #####
highest_bid = api.get_highest_bid()
bid_price = highest_bid + 100
bid_amount = round(budget/bid_price, decimal_length)
trade_result = api.trade(price=bid_price, amount=bid_amount)
print("Bid placed at {} for {} ETH".format(bid_price, bid_amount))

##### Get my balance ####
balance_amount, balance_available = api.my_balance("jpy")


##### Repeat until my order gets fulfilled #####
while balance_amount != balance_available:
    
    # Keep my bid the highest on the board
    if bid_price != api.get_highest_bid():
        
        # Get outstanding bid amount
        active_order = api.active_orders()
        try:
            outstanding_amount = list(active_order['return'].values())[0]['amount']
        except:
            outstanding_amount = 0
        
        # Re-bid
        bid_price = api.get_highest_bid() + 100
        api.cancel_all_orders()
        api.trade(price=bid_price, amount=outstanding_amount)
        print("Bid placed at {} for {} ETH".format(bid_price, outstanding_amount))
        
    time.sleep(1)
    balance_amount, balance_available = api.my_balance("jpy")
    
api.cancel_all_orders()
print("Order fulfilled")


# # テスト用

# api.cancel_all_orders()

# balance_amount, balance_available = api.my_balance("jpy")
# display(balance_amount, balance_available)
