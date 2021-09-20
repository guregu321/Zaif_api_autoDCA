#!/usr/bin/env python
# coding: utf-8

# In[1]:


from Zaif_api import Zaif_api
import yaml
import datetime
import time


# In[2]:


path = "../api_config.yaml"
with open(path) as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
budget = config['budget']
api_key = config['api_key']
api_secret = config['api_secret']
print("Buying amount is {}".format(budget))


# In[3]:


api = Zaif_api.zaif(api_key, api_secret)


# In[4]:


print("Job starting at {}".format(datetime.datetime.now()))

##### Cancel all orders #####
api.cancel_all_orders()
print("Initialized")

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
print("    amount = {}, available = {}".format(balance_amount, balance_available))

##### Repeat until my order gets fulfilled #####
while balance_amount != balance_available:
    
    # Keep my bid the highest on the board
    if bid_price != api.get_highest_bid():
        
        print("    amount = {}, available = {}".format(balance_amount, balance_available))
        
        # Get outstanding bid amount
        active_order = api.active_orders()
        try:
            outstanding_amount = list(active_order['return'].values())[0]['amount']
        except:
            outstanding_amount = 0
        
        # Re-bid
        bid_price = api.get_highest_bid() + 100
        api.cancel_all_orders()
        result = api.trade(price=bid_price, amount=outstanding_amount)
        print("Bid placed at {} for {} ETH".format(bid_price, outstanding_amount))
        
    time.sleep(1)
    balance_amount, balance_available = api.my_balance("jpy")
    
    
api.cancel_all_orders()
print("Order fulfilled")


# # テスト用

# api.cancel_all_orders()

# balance_amount, balance_available = api.my_balance("jpy")
# display(balance_amount, balance_available)

# test = {'success': 0, 'error': 'unknown error'}
# print(test['success'])
# 

# In[ ]:




