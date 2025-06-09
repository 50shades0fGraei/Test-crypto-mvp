import math

# Initial Setup
initial_investment = 10  # $10 as requested
starting_price = 100
timeframes = {
    "daily": 0.10,
    "weekly": 0.20,
    "biweekly": 0.36,
    "monthly": 0.50,
    "bimonthly": 0.80,
    "quarterly": 1.20
}
checkpoints = {
    "fs": 5.80,
    "d": 40,
    "cd": 60,
    "b": 80,
    "a": 94.30,
    "fabc": 200
}
daily_compounding_rate = 0.05  # Note: 5% is aggressive; test with 0.005 for realism
profit_boost = 0.05
days_in_quarter = 90
days_per_cycle = 14
cycles_per_quarter = days_in_quarter // days_per_cycle
min_trade_size = 0.0001  # Minimum units to avoid precision issues

class Currency:
    def __init__(self, name, price, volatility_adjustment):
        self.name = name
        self.price = price
        self.volatility_adjustment = volatility_adjustment
        self.positions = []

    def buy(self, price, units, capital):
        cost = price * units
        if capital >= cost and units >= min_trade_size:
            self.positions.append((price, units))
            return cost
        return 0

    def sell(self, price, units_to_sell):
        if not self.positions:
            return 0
        proceeds = 0
        sold_units = 0
        new_positions = []
        for buy_price, units in self.positions:
            if sold_units < units_to_sell:
                sell_units = min(units, units_to_sell - sold_units)
                if sell_units >= min_trade_size:
                    sold_units += sell_units
                    proceeds += sell_units * price
                    remaining_units = units - sell_units
                    if remaining_units >= min_trade_size:
                        new_positions.append((buy_price, remaining_units))
            else:
                new_positions.append((buy_price, units))
        self.positions = new_positions
        return proceeds

    def portfolio_value(self):
        total_units = sum(units for _, units in self.positions)
        return total_units * self.price

    def average_cost(self):
        if not self.positions:
            return 0
        total_cost = sum(price * units for price, units in self.positions)
        total_units = sum(units for _, units in self.positions)
        return total_cost / total_units if total_units > 0 else 0

# Initialize Currencies
currencies = [
    Currency("SHIB", starting_price, 1.0),
    Currency("DOGE", starting_price, 0.9),
    Currency("BABYDOGE", starting_price, 1.1)
]

# Trading State
capital = initial_investment
monthly_pool = 0
month_profits = [0]
week = 0
month = 1
first_purchase_price = starting_price

# Main Trading Loop
for cycle in range(cycles_per_quarter + 1):
    days_in_this_cycle = min(days_per_cycle, days_in_quarter - (cycle * days_per_cycle))
    starting_capital = capital

    # Monthly Boost
    if week % 4 == 0 and month_profits:
        monthly_boost = month_profits[-1] * 0.5
        capital += monthly_boost
        month += 1

    # Week 1: Trading Phase
    for currency in currencies:
        currency.price = starting_price

    # Buy Phase
    for timeframe, drop in timeframes.items():
        for currency in currencies:
            adjusted_drop = drop * currency.volatility_adjustment
            buy_price = currency.price * (1 - adjusted_drop)
            units_to_buy = capital / (len(currencies) * len(timeframes) * buy_price)  # ~$0.55/trade
            cost = currency.buy(buy_price, units_to_buy, capital)
            capital -= cost
            currency.price = buy_price

    # Interloping
    for i, currency in enumerate(currencies):
        for j, other_currency in enumerate(currencies):
            if i != j and currency.price < other_currency.price:
                units_to_exchange = min(0.001, sum(units for _, units in currency.positions))
                proceeds = currency.sell(currency.price, units_to_exchange)
                if proceeds > 0:
                    units_to_buy = proceeds / other_currency.price
                    other_currency.buy(other_currency.price, units_to_buy, capital)
                    capital += proceeds

    # Sell Phase
    for timeframe, rise in timeframes.items():
        for currency in currencies:
            adjusted_rise = rise * currency.volatility_adjustment
            sell_price = currency.price * (1 + adjusted_rise)
            total_units = sum(units for _, units in currency.positions)
            if total_units < min_trade_size:
                continue

            # Checkpoints
            for cp_name, cp_price in checkpoints.items():
                if abs(sell_price - cp_price) / cp_price < 0.05 or (cp_name == "fabc" and sell_price >= 220):  # 5% range
                    sell_price = min(cp_price, 220)
                    units_to_sell = min(0.001, total_units)
                    proceeds = currency.sell(sell_price, units_to_sell)
                    capital += proceeds
                    break

            # Sell on Rise
            if currency.portfolio_value() > currency.average_cost() * total_units:
                units_to_sell = min(0.001, total_units)
                proceeds = currency.sell(sell_price, units_to_sell)
                capital += proceeds

            # Sell First Purchase
            for buy_price, units in currency.positions[:]:
                if buy_price == first_purchase_price and sell_price >= buy_price * 1.20:
                    units_to_sell = min(units, 0.001)
                    proceeds = currency.sell(sell_price, units_to_sell)
                    capital += proceeds
                    break

            currency.price = sell_price

    # Apply Profit Boost
    cycle_profit = (capital - starting_capital) * (1 + profit_boost)

    # Week 2: Compounding
    for day in range(7 if days_in_this_cycle > 7 else max(0, days_in_this_cycle - 7)):
        capital *= (1 + daily_compounding_rate)

    # Profit Allocation
    profit = capital - starting_capital
    cycle_roi = (capital / starting_capital - 1) if starting_capital > 0 else 0
    expected_roi = timeframes["weekly"]
    reinvest_percent = 0.75 if cycle_roi > expected_roi else 0.50
    reinvest_amount = profit * reinvest_percent
    pool_amount = profit * (1 - reinvest_percent)
    capital = starting_capital + reinvest_amount
    monthly_pool += pool_amount

    # Track Monthly Profits
    if week % 4 == 0:
        month_profits.append(profit * 4)
    week += 2

# Final Results
total = capital + monthly_pool
quarterly_roi = (total / initial_investment - 1) * 100
print(f"Final Capital: ${capital:.2f}")
print(f"Monthly Pool: ${monthly_pool:.2f}")
print(f"Total: ${total:.2f}")
print(f"Quarterly ROI: {quarterly_roi:.2f}%")