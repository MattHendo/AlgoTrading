from datetime import datetime
import pandas as pd
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from config import ALPACA_CONFIG

class SMARsiStrategy(Strategy):
    parameters = {
        "symbol": "AAPL",
        "sma_length": 200,
        "rsi_length": 10,
        "rsi_threshold": 30,  # Overbought/Oversold threshold
        "quantity": 1
    }

    def initialize(self):
        self.symbol = self.parameters["symbol"]
        self.sma_length = self.parameters["sma_length"]
        self.rsi_length = self.parameters["rsi_length"]
        self.rsi_threshold = self.parameters["rsi_threshold"]
        self.quantity = self.parameters["quantity"]
        self.data = pd.DataFrame()  # To store historical data
        self.sleeptime = "1H"  # Frequency of checks (hourly for this example)

    def on_trading_iteration(self):
        # Fetch historical data
        historical_data = self.get_historical_data(self.symbol, "1min", "1d")
        close_prices = historical_data["close"]

        # Calculate indicators
        self.data = historical_data
        self.data["SMA"] = ta.sma(close_prices, length=self.sma_length)
        self.data["RSI"] = ta.rsi(close_prices, length=self.rsi_length)

        # Remove NaN values to avoid errors
        self.data.dropna(inplace=True)

        # Get the latest data point
        latest = self.data.iloc[-1]
        latest_price = latest["close"]
        latest_sma = latest["SMA"]
        latest_rsi = latest["RSI"]

        # Generate buy/sell signals based on RSI and SMA
        if latest_rsi < self.rsi_threshold and latest_price > latest_sma:
            # Buy Signal
            order = self.create_order(self.symbol, self.quantity, "buy")
            self.submit_order(order)
            self.log_message(f"BUY signal triggered at {latest_price}", "INFO")

        elif latest_rsi > 100 - self.rsi_threshold and latest_price < latest_sma:
            # Sell Signal
            order = self.create_order(self.symbol, self.quantity, "sell")
            self.submit_order(order)
            self.log_message(f"SELL signal triggered at {latest_price}", "INFO")

# Set up the trader and backtest
trader = Trader()
broker = Alpaca(ALPACA_CONFIG)
strategy = SMARsiStrategy(
    broker=broker,
    parameters={
        "symbol": "AAPL",
        "sma_length": 200,
        "rsi_length": 10,
        "rsi_threshold": 30,
        "quantity": 1
    }
)

backtesting_start = datetime(2023, 1, 1)
backtesting_end = datetime(2023, 12, 31)

# Run the backtest
strategy.run_backtest(
    YahooDataBacktesting,
    backtesting_start,
    backtesting_end
)

# Add the strategy to the trader for live execution
trader.add_strategy(strategy)
trader.run_all()
