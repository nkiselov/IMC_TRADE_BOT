from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import jsonpickle
import numpy as np

# Trading State has
#   position
#   order_depths
# other components i didnt make

class Trader:
    def run(self, state: TradingState):
        result = {}
        theGood = "SQUID_INK"

        
        bigWindow = 100
        smallWindow = 50
        mid_price = (max(state.order_depths[theGood].buy_orders)+min(state.order_depths[theGood].sell_orders))/2
        price_history = []
        if(state.traderData!=""):
            price_history = jsonpickle.decode(state.traderData)
        price_history+=[mid_price]

        if(len(price_history)>bigWindow):
            price_history = price_history[1:]
        smlAve = np.mean(price_history[max(0,len(price_history)-smallWindow):])
        bigAve = np.mean(price_history[max(0,len(price_history)-bigWindow):])
        conf = int(0.5*abs(smlAve-bigAve))
        orders: List[Order] = []
        pos = 0
        if theGood in state.position:
            pos = state.position[theGood]
        amtBuy = min((50-pos),conf)
        amtSell = min((pos+50),conf)

        if smlAve<bigAve:
            orders.append(Order(theGood, int(smlAve), amtBuy))
        else:
            orders.append(Order(theGood, int(smlAve), -amtSell))
        
        result[theGood] = orders

        traderData = jsonpickle.encode(price_history)

        conversions = 1
        return result, conversions, traderData