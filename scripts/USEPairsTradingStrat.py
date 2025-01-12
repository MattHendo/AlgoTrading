from datetime import datetime
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from config import ALPACA_CONFIG
import pandas as pd

API_KEY="PKK0JP0AA7PS0M1PS437"
SECRET_KEY ="y8XKrt8IazYOyGjMPWY6tZmXkWZyfZUnG2JAxwPI"

ALPACA_CONFIG = {
    "API_KEY": API_KEY,
    "API_SECRET": SECRET_KEY,
    "paper": "True" }
    
class PairsTrading(Strategy):
    parameters = {
        "symbol": "SPY",
        "short_window": 50,
        "long_window": 200,
        "quantity": 1,
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


# Create a Trader instance
trader = Trader()

# Configure the broker
broker = Alpaca(ALPACA_CONFIG)

# Set up the strategy with parameters
strategy = PairsTrading(
    broker=broker,
    parameters={
        "symbol": "SPY",
        "short_window": 50,
        "long_window": 200,
        "quantity": 1,
    },
)

# Define backtesting period
backtesting_start = datetime(2015, 1, 1)
backtesting_end = datetime(2024, 11, 5)

# Run backtest
strategy.run_backtest(
    YahooDataBacktesting,
    backtesting_start,
    backtesting_end,
)

# Add strategy to the trader for live execution
trader.add_strategy(strategy)

# Execute the strategy
trader.run_all()
