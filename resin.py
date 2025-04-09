from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import string
import jsonpickle

# Trading State has
#   position
#   order_depths
# other components i didnt make

class Trader:
    def run(self, state: TradingState):
        result = {}
        theGood = "RAINFOREST_RESIN"

        buy_price = 9998
        sell_price = 10002
        thres = 5
        
        print(state.position)
        orders: List[Order] = []
        pos = 0
        if theGood in state.position:
            pos = state.position[theGood]
        amtBuy = 50-pos
        amtSell = pos+50

        if amtBuy<thres:
            sell_price-=1
        if amtSell<thres:
            buy_price+=1
        orders.append(Order(theGood, buy_price, amtBuy))
        orders.append(Order(theGood, sell_price, -amtSell))
        
        result[theGood] = orders

        traderData = ""

        conversions = 1
        return result, conversions, traderData