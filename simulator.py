from resin import Trader
import csv
from datamodel import OrderDepth, UserId, TradingState, Order
import copy
import matplotlib.pyplot as plt
import numpy as np

def getNumber(val):
    try:
        return float(val)
    except:
        return val

def getEntryOrderDepth(ent):
    ret = OrderDepth()
    if(ent['bid_price_1'] != ''):
        ret.buy_orders[ent['bid_price_1']] = ent['bid_volume_1']
    if(ent['bid_price_2'] != ''):
        ret.buy_orders[ent['bid_price_2']] = ent['bid_volume_2']
    if(ent['bid_price_3'] != ''):
        ret.buy_orders[ent['bid_price_3']] = ent['bid_volume_3']
    if(ent['ask_price_1'] != ''):
        ret.sell_orders[ent['ask_price_1']] = -ent['ask_volume_1']
    if(ent['ask_price_2'] != ''):
        ret.sell_orders[ent['ask_price_2']] = -ent['ask_volume_2']
    if(ent['ask_price_3'] != ''):
        ret.sell_orders[ent['ask_price_3']] = -ent['ask_volume_3']
    return ret

def readMarketHistory(inp):
    sample_market = inp
    entries = []
    with open(sample_market, 'r') as file:
        csvreader = csv.reader(file,delimiter=';')
        header = next(csvreader)
        res = []
        for row in csvreader:
            nrow = [getNumber(val) for val in row]
            res+=[dict(zip(header,nrow))]
        entries = res
    products = list(set([e['product'] for e in entries]))
    groupedEntries = dict(zip(products,[[] for _ in range(len(products))]))
    for ent in entries:
        groupedEntries[ent['product']]+=[ent]
    market = dict([(pname,[getEntryOrderDepth(ent) for ent in group]) for (pname,group) in groupedEntries.items()])
    marketByGroup = []
    for i in range(len(market[products[0]])):
        orders = dict()
        for p in products:
            orders[p] = market[p][i]
        marketByGroup+=[orders]
    return marketByGroup, products
        
class Simulator:

    def __init__(self,url):
        market, products = readMarketHistory(url)
        self.market = market
        self.products = products

    def runSimul(self,algo,vis):
        market = self.market
        products = self.products

        traderData = ""
        positionsHistory = dict(zip(products,[[] for _ in products]))
        priceHistory = dict(zip(products,[[] for _ in products]))
        profitHistory = []

        position_limits = dict(zip(products,[50 for _ in products]))
        positions = dict(zip(products,[0 for _ in products]))
        profit = 0

        for itern in range(len(market)):
            cur_orig = market[itern]
            algoOrders, conversions, newTraderData = algo.run(TradingState(traderData=traderData,order_depths=cur_orig,position=positions,timestamp=100*itern,listings=None,own_trades=None,market_trades=None,observations=None))
            traderData = newTraderData
            buy_list = dict([(pname,[list(tup) for tup in orders.buy_orders.items()]) for (pname,orders) in cur_orig.items()])
            sell_list = dict([(pname,[list(tup) for tup in orders.sell_orders.items()]) for (pname,orders) in cur_orig.items()])
            mid_price = dict([(p,(buy_list[p][0][0]+sell_list[p][0][0])/2) for p in products])
            for p in products:
                if(not p in algoOrders):
                    continue
                for order in algoOrders[p]:
                    #price [0]
                    #quantity [1]
                    if(order.quantity<0):
                        if(positions[p]+order.quantity>=-position_limits[p]):
                            while(order.quantity<0 and len(buy_list[p])>0 and buy_list[p][0][0]>=order.price):
                                amt = min(buy_list[p][0][1],-order.quantity)
                                positions[p]-=amt
                                buy_list[p][0][1]-=amt
                                profit+=buy_list[p][0][0]*amt
                                order.quantity+=amt
                                if vis:
                                    print(itern, "SELL",amt,"@",buy_list[p][0][0])
                                if(buy_list[p][0][1]==0):
                                    buy_list[p].pop(0)
                    else:
                        if(positions[p]+order.quantity<=position_limits[p]):
                            while(order.quantity>0 and len(sell_list[p])>0 and sell_list[p][0][0]<=order.price):
                                amt = min(-sell_list[p][0][1],order.quantity)
                                positions[p]+=amt
                                sell_list[p][0][1]+=amt
                                profit-=sell_list[p][0][0]*amt
                                order.quantity-=amt
                                if vis:
                                    print(itern, "BUY",amt,"@",sell_list[p][0][0])
                                if(sell_list[p][0][1]==0):
                                    sell_list[p].pop(0)
            profitHistory += [profit]
            for p in products:
                positionsHistory[p] += [copy.copy(positions[p])]
                priceHistory[p] += [mid_price[p]]

        profitHistory = np.array(profitHistory, dtype=np.float32)
        for p in products:
            priceHistory[p]=np.array(priceHistory[p], dtype=np.float32)
            positionsHistory[p]=np.array(positionsHistory[p], dtype=np.float32)

        netHistory = profitHistory
        for p in products:
            netHistory+=priceHistory[p]*positionsHistory[p]

        if not vis:
            return
        print("Min",np.min(netHistory))
        print("Max",np.max(netHistory))
        print("Last",netHistory[-1])
        plt.plot(netHistory)
        plt.show()
        for p in products:
            print(p)
            plt.plot(priceHistory[p])
            plt.show()