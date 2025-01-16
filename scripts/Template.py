from lumibot.brokers import Alpaca
from lumibot.traders import Trader
from lumibot.strategies.strategy import Strategy
from config import ALPACA_CONFIG
import pandas_ta as ta
import pandas as pd
import math

class RSISMAStrategy(Strategy):
    # Define parameters for the strategy
    parameters = {
        "symbol": "AAPL",  # Default symbol
        "initial_investment": 100000,  # Starting investment amount
        "rsi_length": 10,  # RSI calculation length
        "sma_length": 200  # SMA calculation length
    }

    def initialize(self):
        # The amount of time between iterations (e.g., checking every 180 minutes)
        self.sleeptime = "1D"
        self.in_position = False
        self.equity = self.parameters["initial_investment"]
        self.no_of_shares = 0

    def on_trading_iteration(self):
        symbol = self.parameters["symbol"]
        rsi_length = self.parameters["rsi_length"]
        sma_length = self.parameters["sma_length"]

        # Fetch historical data for the symbol
        data = self.get_historical_data(symbol, "1D", 500)  # Fetching 500 days of daily data
        if data.empty:
            self.log_message("No data fetched for symbol, skipping iteration.", "error")
            return

        # Calculate SMA and RSI
        data["sma"] = ta.sma(data["close"], length=sma_length)
        data["rsi"] = ta.rsi(data["close"], length=rsi_length)

        # Drop rows with NaN values
        data = data.dropna()

        # Get the latest data point
        latest_data = data.iloc[-1]
        price = latest_data["close"]
        sma = latest_data["sma"]
        rsi = latest_data["rsi"]
        self.log_message(f"Latest Price: {price}, SMA: {sma}, RSI: {rsi}")

        # Implement buy logic
        if rsi < 30 and price > sma and not self.in_position:
            self.no_of_shares = math.floor(self.equity / price)
            self.equity -= self.no_of_shares * price
            self.in_position = True
            self.log_message(f"BUY: {self.no_of_shares} shares of {symbol} at ${price}")

            # Place buy order
            self.create_order(symbol, self.no_of_shares, "buy")
            self.submit_orders()

        # Implement sell logic
        elif rsi > 70 and price < sma and self.in_position:
            self.equity += self.no_of_shares * price
            self.in_position = False
            self.log_message(f"SELL: {self.no_of_shares} shares of {symbol} at ${price}")

            # Place sell order
            self.create_order(symbol, self.no_of_shares, "sell")
            self.submit_orders()

        # If still in position at the end, log and calculate final stats
        if self.in_position:
            self.equity += self.no_of_shares * price
            self.in_position = False
            self.log_message(f"Closing position: {self.no_of_shares} shares of {symbol} at ${price}")

        # Calculate and log performance
        earning = round(self.equity - self.parameters["initial_investment"], 2)
        roi = round((earning / self.parameters["initial_investment"]) * 100, 2)
        self.log_message(f"EARNING: ${earning}, ROI: {roi}%")

# Set up the Trader, Broker, and Strategy
trader = Trader()
broker = Alpaca(ALPACA_CONFIG)

# Initialize the strategy with Alpaca broker
strategy = RSISMAStrategy(
    broker=broker,
    parameters={
        "symbol": "AAPL",
        "initial_investment": 100000,
        "rsi_length": 10,
        "sma_length": 200
    }
)

# Run backtesting
from datetime import datetime
from lumibot.backtesting import YahooDataBacktesting

backtesting_start = datetime(2020, 1, 1)
backtesting_end = datetime(2020, 12, 31)

strategy.run_backtest(
    YahooDataBacktesting,
    backtesting_start,
    backtesting_end,
    parameters={"symbol": "AAPL"}
)

# Add the strategy to the trader and start live trading (optional)
trader.add_strategy(strategy)
trader.run_all()
