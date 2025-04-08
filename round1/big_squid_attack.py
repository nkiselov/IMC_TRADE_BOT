import json
from typing import Dict, List, Tuple
from datamodel import OrderDepth, TradingState, Order


class Trader:
    def run(self, state: TradingState) -> Tuple[Dict[str, List[Order]], int, str]:
        result: Dict[str, List[Order]] = {}

        # Load persistent state or initialize if empty
        try:
            data = json.loads(state.traderData) if state.traderData else {}
        except Exception:
            data = {}

        data.setdefault("prices", {})
        data.setdefault("positions", {})
        data["tick"] = data.get("tick", 0) + 1
        current_tick = data["tick"]

        for product in state.order_depths:
            if product != "SQUID_INK":
                continue

            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []

            # Compute mid-price
            if order_depth.buy_orders and order_depth.sell_orders:
                best_bid = max(order_depth.buy_orders.keys())
                best_ask = min(order_depth.sell_orders.keys())
                mid_price = (best_bid + best_ask) / 2
            elif order_depth.buy_orders:
                mid_price = max(order_depth.buy_orders.keys())
            elif order_depth.sell_orders:
                mid_price = min(order_depth.sell_orders.keys())
            else:
                continue  # No data to compute price

            # Update price history
            data["prices"].setdefault(product, []).append(mid_price)

            # Define SMA windows
            short_window = 7
            long_window = 21
            price_history = data["prices"][product]

            if len(price_history) >= long_window + 1:
                sma_short = sum(price_history[-short_window:]) / short_window
                sma_long = sum(price_history[-long_window:]) / long_window

                sma_short_prev = sum(price_history[-short_window - 1:-1]) / short_window
                sma_long_prev = sum(price_history[-long_window - 1:-1]) / long_window

                # BUY condition (bullish crossover)
                if product not in data["positions"]:
                    if sma_short_prev <= sma_long_prev and sma_short > sma_long:
                        if order_depth.sell_orders:
                            best_ask = min(order_depth.sell_orders.keys())
                            quantity = min(10, order_depth.sell_orders[best_ask])  # Limit size
                            orders.append(Order(product, best_ask, quantity))
                            data["positions"][product] = {"entry_tick": current_tick}

                # SELL condition (bearish crossover or timeout)
                else:
                    time_held = current_tick - data["positions"][product]["entry_tick"]
                    bearish_crossover = sma_short_prev >= sma_long_prev and sma_short < sma_long
                    timed_exit = time_held >= 30

                    if bearish_crossover or timed_exit:
                        if order_depth.buy_orders:
                            best_bid = max(order_depth.buy_orders.keys())
                            quantity = min(10, abs(order_depth.buy_orders[best_bid]))
                            orders.append(Order(product, best_bid, -quantity))
                            del data["positions"][product]

            result[product] = orders

        traderData = json.dumps(data)
        conversions = 1
        return result, conversions, traderData
