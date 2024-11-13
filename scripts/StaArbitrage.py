from datetime import datetime
from lumibot.backtesting import YahooDataBacktesting
from lumibot.brokers import Alpaca
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
import pandas as pd

API_KEY = "PK2BPY2BJH8UJ9CB3PJB"
SECRET_KEY = "WEiBPpmuS1hT7BtGFc7FQSm5YMcOLPA15KPTbgcq"

ALPACA_CONFIG = {
    "API_KEY": API_KEY,
    "API_SECRET": SECRET_KEY,
    "paper": "True"  
}

class StatArbBot(Strategy):
    parameters = {
        "symbols": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
        "pairs": [("AAPL", "MSFT"), ("GOOGL", "AMZN"), ("MSFT", "TSLA")],
        "z_score_threshold": 2,
        "lookback_window": 20,
    }

    def initialize(self):
        self.sleeptime = "180M"  

    def get_historical_data(self):
        """Fetch historical data for each symbol and ensure consistent date ranges."""
        symbols = self.parameters["symbols"]
        lookback_window = self.parameters["lookback_window"]

       
        historical_data = {}
        for symbol in symbols:
            prices = self.get_historical_prices(symbol, length=lookback_window, timestep='day').df['close']
            historical_data[symbol] = prices

        
        data_df = pd.DataFrame(historical_data)
        data_df.dropna(inplace=True)  
        return data_df

    def calculate_spread(self, stock1, stock2):
        price1 = self.data[stock1]
        price2 = self.data[stock2]
        spread = price1 - price2
        return spread

    def calculate_z_score(self, spread):
        spread_mean = spread.rolling(self.parameters["lookback_window"]).mean()
        spread_std = spread.rolling(self.parameters["lookback_window"]).std()
        z_score = (spread - spread_mean) / spread_std
        return z_score

    def order_target_percent(self, symbol, percent):
        """Custom method to order a target percent of the portfolio for a given symbol."""
        target_cash = percent * self.cash
        latest_price = self.get_historical_prices(symbol, length=1).df['close'].iloc[-1]

        
        if latest_price > 0:  
            quantity = int(target_cash // latest_price) 

            if quantity > 0:
                side = "buy" if percent > 0 else "sell"
                order = self.create_order(symbol, quantity=abs(quantity), side=side)
                self.submit_order(order)

    def on_trading_iteration(self):
        self.data = self.get_historical_data()

        pairs = self.parameters["pairs"]
        z_threshold = self.parameters["z_score_threshold"]

        for stock1, stock2 in pairs:
            spread = self.calculate_spread(stock1, stock2)
            z_score = self.calculate_z_score(spread).iloc[-1]

            if z_score > z_threshold:
                self.order_target_percent(stock1, -0.5)  # Short stock1
                self.order_target_percent(stock2, 0.5)   # Long stock2
                self.log_message(f"Trade: Short {stock1}, Long {stock2} - Z-score: {z_score}")

            elif z_score < -z_threshold:
                self.order_target_percent(stock1, 0.5)   # Long stock1
                self.order_target_percent(stock2, -0.5)  # Short stock2
                self.log_message(f"Trade: Long {stock1}, Short {stock2} - Z-score: {z_score}")

            else:
                self.order_target_percent(stock1, 0)
                self.order_target_percent(stock2, 0)
                self.log_message(f"Exit: {stock1}, {stock2} - Z-score: {z_score}")

# Set up the strategy, broker, and trader
trader = Trader()
broker = Alpaca(ALPACA_CONFIG)
strategy = StatArbBot(broker=broker)

# Define backtesting parameters
backtesting_start = datetime(2021, 1, 1)
backtesting_end = datetime(2021, 12, 31)
strategy.run_backtest(
    YahooDataBacktesting,
    backtesting_start,
    backtesting_end
)

trader.add_strategy(strategy)
trader.run_all()


'''
we are comparing two stocks, then calulating the z-score: (spread − spread mean)/(std) 
In this StatArbBot strategy Z-score threshold is set to +-2 meaning that we only need to take action 
if a pair of stockshave a difference of more than 2 standard deviations from its historical mean. 

When Z-score is grater than 2:
HIGHER stock in the has risen too much compared to the LOWER stock

What should we do:
HIGHER stock (stock1) will likely FALL as returns to its mean (basicaly same idea as mean reversion).
LOWER stock (stock2) will likely RISE as returns to its mean

When Z-score is less than -2:
LOWER stock has fallen too much relative to the HIGHER stock.
HIGHER stock (stock1): will likely RISE as returns to its mean.
LOWER stock (stock2):will likely FALL as returns to its mean

'''

