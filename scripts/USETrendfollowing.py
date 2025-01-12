from datetime import datetime
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from config import ALPACA_CONFIG
import pandas as pd

class TrendFollowingStrategy(Strategy):
    parameters = {
        "symbol": "SPY",
        "short_window": 50,
        "long_window": 200,
        "quantity": 1
    }

    def initialize(self):
        self.symbol = self.parameters["symbol"]
        self.short_window = self.parameters["short_window"]
        self.long_window = self.parameters["long_window"]
        self.quantity = self.parameters["quantity"]
        self.data = pd.DataFrame()  # To store historical data
        self.last_position = 0  # Tracks the last trading signal (0 = none, 1 = buy, -1 = sell)
        self.sleeptime = "1D"  # Adjust based on backtesting data frequency

    def on_trading_iteration(self):
        # Fetch historical data
        historical_data = self.get_historical_data(self.symbol, "1d", "1y")
        close_prices = historical_data["close"]

        # Update data and calculate moving averages
        self.data = historical_data
        self.data["SMA_short"] = close_prices.rolling(window=self.short_window).mean()
        self.data["SMA_long"] = close_prices.rolling(window=self.long_window).mean()

        # Generate trading signal
        if (
            self.data["SMA_short"].iloc[-1] > self.data["SMA_long"].iloc[-1]
            and self.last_position != 1
        ):
            # Buy Signal
            order = self.create_order(self.symbol, self.quantity, "buy")
            self.submit_order(order)
            self.last_position = 1

        elif (
            self.data["SMA_short"].iloc[-1] < self.data["SMA_long"].iloc[-1]
            and self.last_position != -1
        ):
            # Sell Signal
            order = self.create_order(self.symbol, self.quantity, "sell")
            self.submit_order(order)
            self.last_position = -1

        # If no condition matches, hold the position (do nothing)

# Create a Trader instance and run the backtest
trader = Trader()
broker = Alpaca(ALPACA_CONFIG)
strategy = TrendFollowingStrategy(
    broker=broker,
    parameters={
        "symbol": "SPY",
        "short_window": 50,
        "long_window": 200,
        "quantity": 1
    }
)

backtesting_start = datetime(2015, 1, 1)
backtesting_end = datetime(2024, 11, 5)

# Run the backtest
strategy.run_backtest(
    YahooDataBacktesting,
    backtesting_start,
    backtesting_end
)

# Add the strategy to the trader for live execution
trader.add_strategy(strategy)
trader.run_all()
