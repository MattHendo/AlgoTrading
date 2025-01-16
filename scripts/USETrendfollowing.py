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
    "paper": "True"  
}

class TrendFollowingStrategy(Strategy):
    parameters = {
        "symbol": "AAPL",          # The symbol to trade
        "lookback_window": 200,   # Number of days to fetch historical prices
        "short_window": 50,       # Short SMA window
        "long_window": 200,       # Long SMA window
        "quantity": 1000             # Number of shares to trade
    }

    def initialize(self):
        self.symbol = self.parameters["symbol"]
        self.lookback_window = self.parameters["lookback_window"]
        self.short_window = self.parameters["short_window"]
        self.long_window = self.parameters["long_window"]
        self.quantity = self.parameters["quantity"]
        self.data = pd.DataFrame()  # To store historical data
        self.last_position = 0      # Tracks the last trading signal (0 = none, 1 = buy, -1 = sell)
        self.sleeptime = "1D"       # Adjust based on backtesting data frequency

    def get_historical_data(self):
        """Fetch historical data for the symbol and ensure consistent date ranges."""
        prices = self.get_historical_prices(
            self.symbol, length=self.lookback_window, timestep="day"
        ).df["close"]

        # Convert to DataFrame to align with strategy's expectations
        data_df = pd.DataFrame({self.symbol: prices})
        data_df.dropna(inplace=True)  # Drop rows with missing values
        return data_df

    def on_trading_iteration(self):
        # Fetch historical data
        historical_data = self.get_historical_data()
        close_prices = historical_data[self.symbol]  # Extract close prices for the symbol

        # Update data and calculate moving averages
        self.data = historical_data
        self.data["SMA_short"] = close_prices.rolling(window=self.short_window).mean()
        self.data["SMA_long"] = close_prices.rolling(window=self.long_window).mean()

        # Generate trading signals
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
        "lookback_window": 200,  # Ensure sufficient data for SMA calculations
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

