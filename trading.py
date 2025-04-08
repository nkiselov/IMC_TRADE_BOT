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
        for product in state.order_depths:
            if(product!="RAINFOREST_RESIN"):
                continue
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []
            buy_price = 9999
            sell_price = 10001
    
            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                if int(best_ask) < buy_price:
                    orders.append(Order(product, best_ask, -best_ask_amount))
    
            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                if int(best_bid) > sell_price:
                    orders.append(Order(product, best_bid, -best_bid_amount))
            
            result[product] = orders
            print(jsonpickle.encode(state.observations))
    
        traderData = "SAMPLE"

        conversions = 1
        return result, conversions, traderData