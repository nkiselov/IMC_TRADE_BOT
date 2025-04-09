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
        theGood = "KELP"

        mrMarginBuy = 1
        mrMarginSell = 1
        msWindow = 30
        #10 351
        #30 323
        
        mid_price = (max(state.order_depths[theGood].buy_orders)+min(state.order_depths[theGood].sell_orders))/2
        price_history = []
        if(state.traderData!=""):
            price_history = jsonpickle.decode(state.traderData)
        price_history+=[mid_price]

        if(len(price_history)>msWindow):
            price_history = price_history[1:]
        avePrice = np.mean(price_history)

        orders: List[Order] = []
        pos = 0
        if theGood in state.position:
            pos = state.position[theGood]
        amtBuy = 50-pos
        amtSell = pos+50

        orders.append(Order(theGood, int(avePrice-mrMarginBuy), amtBuy))
        orders.append(Order(theGood, int(avePrice+mrMarginSell), -amtSell))
        
        result[theGood] = orders

        traderData = jsonpickle.encode(price_history)

        conversions = 1
        return result, conversions, traderData