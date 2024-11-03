#momentum strategy (70% annual returns)

from config import ALPACA_CONFIG
from datetime import datetime
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader

class MomentumStrategy(Strategy):
    parameters = {
        "symbols": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
        "top_n": 5,
        "lookback_period": 20,
        "cash_to_invest": 0.2
    }

    def initialize(self):
        self.sleeptime = "180M"  # Frequency of trading iterations

    def calculate_momentum(self, symbol):
        # Fetch historical prices using the correct method
        prices = self.get_historical_prices(symbol, length=self.parameters["lookback_period"], timestep='day').df[
            'close']
        return (prices[-1] - prices[0]) / prices[0] if len(prices) > 1 else 0

    def on_trading_iteration(self):
        symbols = self.parameters["symbols"]
        top_n = self.parameters["top_n"]
        cash_to_invest = self.parameters["cash_to_invest"]

        # Calculate momentum scores for all symbols
        momentum_scores = {symbol: self.calculate_momentum(symbol) for symbol in symbols}
        top_symbols = sorted(momentum_scores, key=momentum_scores.get, reverse=True)[:top_n]

        # Clear previous positions
        self.sell_all()

        for symbol in top_symbols:
            # Calculate the cash to invest in the current symbol
            cash = cash_to_invest * self.cash

            # Fetch the latest price for the symbol
            latest_price = self.get_historical_prices(symbol, length=1).df['close'].iloc[-1]

            # Calculate the quantity based on available cash and latest price
            if latest_price > 0:  # Check to avoid division by zero
                quantity = int(cash // latest_price)  # Integer division for shares

                if quantity > 0:  # Ensure quantity is greater than zero
                    order = self.create_order(symbol, quantity=quantity, side="buy")
                    self.submit_order(order)

# Set up the strategy, broker, and trader
trader = Trader()
broker = Alpaca(ALPACA_CONFIG)
strategy = MomentumStrategy(broker=broker)

# Define backtesting parameters
backtesting_start = datetime(2020, 1, 1)
backtesting_end = datetime(2020, 12, 31)
strategy.run_backtest(
    YahooDataBacktesting,
    backtesting_start,
    backtesting_end
)

trader.add_strategy(strategy)
trader.run_all()


#momentum example for youtube series
'''
from lumibot.backtesting import YahooDataBacktesting
from datetime import datetime
from config import ALPACA_CONFIG
from lumibot.brokers import Alpaca
from lumibot.strategies import Strategy
from lumibot.traders import Trader


class SwingHigh(Strategy):
    data = []
    order_number = 0
    entry_price = 0

    def initialize(self):
        self.sleeptime = "30S"

    def on_trading_iteration(self):
        symbol = "TSLA"
        self.data.append(self.get_last_price(symbol))

        self.log_message(f"Position: {self.get_position(symbol)}, Data: {self.data}")

        if len(self.data) > 3:
            temp = self.data[-3:]
            self.log_message(f"Checking for entry condition with prices: {temp}")
            if temp[-1] > temp[1] > temp[0]:
                self.log_message(f"Last 3 prices (momentum detected): {temp}")
                order = self.create_order(symbol, quantity=10, side="buy")
                self.submit_order(order)
                self.order_number += 1
                if self.order_number == 1:
                    self.entry_price = temp[-1]
                    self.log_message(f"Entry price set to: {self.entry_price}")

            if self.get_position(symbol) and self.data[-1] < self.entry_price * 0.995:
                self.log_message(f"Stop-loss triggered at price: {self.data[-1]}")
                self.sell_all()
                self.order_number = 0
            elif self.get_position(symbol) and self.data[-1] >= self.entry_price * 1.015:
                self.log_message(f"Take-profit triggered at price: {self.data[-1]}")
                self.sell_all()
                self.order_number = 0

    def before_market_closes(self):
        self.sell_all()


if __name__ == "__main__":
    trade = False
    if trade:
        broker = Alpaca(ALPACA_CONFIG)
        strategy = SwingHigh(broker=broker)
        trader = Trader()
        trader.add_strategy(strategy)
        trader.run_all()
    else:
        start=datetime(2022,1,1)
        end=datetime(2022,2,1)
        SwingHigh.backtest(
            YahooDataBacktesting,
            start,
            end
        )
'''

