import json
from typing import Dict, List, Tuple
from datamodel import OrderDepth, TradingState, Order


class Trader:
    def run(self, state: TradingState) -> Tuple[Dict[str, List[Order]], int, str]:
        """
        Executes the trading strategy on every tick.
        Uses two SMAs (short term = 7 ticks, long term = 21 ticks) to generate trading signals.
        - BUY when the short SMA crosses above the long SMA.
        - SELL when either (a) the short SMA crosses below the long SMA or (b) the holding period reaches 30 ticks.
        
        Returns:
          - result: A dictionary mapping each product to a list of orders.
          - conversions: An integer conversion (here set to 1).
          - traderData: A persistent JSON string that stores state between ticks.
        """
        result = {}

        # Load persistent state from traderData or initialize state if none exists.
        try:
            data = json.loads(state.traderData) if state.traderData else {}
        except Exception:
            data = {}

        if not data:
            data = {"prices": {}, "positions": {}, "tick": 0}
        else:
            if "prices" not in data:
                data["prices"] = {}
            if "positions" not in data:
                data["positions"] = {}
            if "tick" not in data:
                data["tick"] = 0

        # Increment global tick count.
        data["tick"] += 1
        current_tick = data["tick"]

        # Process each product in the order depths.
        for product in state.order_depths.keys():
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []

            # Compute a mid-price using both sides of the book if available.
            if order_depth.buy_orders and order_depth.sell_orders:
                best_bid = max(order_depth.buy_orders.keys())
                best_ask = min(order_depth.sell_orders.keys())
                mid_price = (best_bid + best_ask) / 2.0
            elif order_depth.buy_orders:
                mid_price = max(order_depth.buy_orders.keys())
            elif order_depth.sell_orders:
                mid_price = min(order_depth.sell_orders.keys())
            else:
                continue  # Skip products with no orders

            # Update price history for the product.
            if product not in data["prices"]:
                data["prices"][product] = []
            data["prices"][product].append(mid_price)

            # Define SMA window sizes.
            short_window = 7   # e.g., last 7 ticks
            long_window = 21   # e.g., last 21 ticks

            # Only evaluate once we have sufficient price history.
            if len(data["prices"][product]) >= long_window + 1:
                # Compute current SMAs.
                sma_short = sum(data["prices"][product][-short_window:]) / short_window
                sma_long = sum(data["prices"][product][-long_window:]) / long_window

                # Compute previous tick's SMAs.
                sma_short_prev = sum(data["prices"][product][-short_window - 1:-1]) / short_window
                sma_long_prev = sum(data["prices"][product][-long_window - 1:-1]) / long_window

                if product not in data["positions"]:
                    # Not in a position: Check for bullish crossover for SELL.
                    if sma_short_prev <= sma_long_prev and sma_short > sma_long:
                        if order_depth.sell_orders:
                            best_ask = min(order_depth.sell_orders.keys())
                            order_quantity = -10  # Adjust your quantity management as needed.
                            orders.append(Order(product, best_ask, order_quantity))
                            # Record the entry tick for this position.
                            data["positions"][product] = {"entry_tick": current_tick}
                            print(f"BUY {order_quantity}x {product} at {best_ask} (Bullish crossover)")
                else:
                    # Already in a position: Check for conditions to exit.
                    time_in_position = current_tick - data["positions"][product]["entry_tick"]
                    # Condition 1: Bearish crossover detected.
                    bearish_crossover = sma_short_prev >= sma_long_prev and sma_short < sma_long
                    # Condition 2: The position has been held for 30 ticks.
                    time_exit = time_in_position >= 30

                    if bearish_crossover or time_exit:
                        if order_depth.buy_orders:
                            best_bid = max(order_depth.buy_orders.keys())
                            order_quantity = 10  # Sell the same quantity (negative indicates a sell).
                            orders.append(Order(product, best_bid, order_quantity))
                            # Remove the open position as it is now closed.
                            del data["positions"][product]
                            reason = "bearish crossover" if bearish_crossover else "30 ticks elapsed"
                            print(f"SELL {abs(order_quantity)}x {product} at {best_bid} (Exit: {reason})")

            result[product] = orders

        # Store updated state in traderData.
        traderData = json.dumps(data)
        conversions = 1

        return result, conversions, traderData
