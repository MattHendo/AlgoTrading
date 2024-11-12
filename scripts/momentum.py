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
backtesting_end = datetime(2024, 1, 1)
strategy.run_backtest(
    YahooDataBacktesting,
    backtesting_start,
    backtesting_end
)

trader.add_strategy(strategy)
trader.run_all()


'''
Momentum Based Strategy using Lumibot:

The primary aim of this strategy is to invest in stocks
that demonstrate the highest momentum, under the assumption
that these stocks will continue to perform well in the short term.
To achieve this, the strategy ranks stocks based on their momentum 
over a specified lookback period and allocates a portion of available 
capital to the top performing stocks.

The MomentumStrategy class is a subclass of Strategy which includes 
specific parameters for stock selection and momentum calculation.
The parameters dictionary contains configuration items like the 
list of stock symbols to monitor, the number of top stocks to 
invest in, the lookback period for momentum calculations, and 
fraction of cash to invest per stock. The initialize method sets the 
trading interation frequency to 180 minutes, meaning the strategy 
will assess and potentially trade a three-hour intervals. 

Within the on_trading_iteration method, the strategy first calculates 
momentum scores for each stock by comparing the current price to the 
price at the start of the lookback period. These scores are computed by the 
calculate_momentum() method, which retrieves historical prices and calculates the 
percentage change over the specified lookback period. After calculating momentum
for each stock, the strategy sorts them to indentify the top n stocks with 
the highest momentum scores. Once it has identified these top stocks, it 
clears all previous positions by calling self.sell_all() to reset holdings.

The strategy then divides the cash allocation (20% of total cash per stock
as defined in cash_to_invest among the top stocks. For each selected stock, 
it determines the quantity of shares to purchase based on the latest available 
price. The self.create_order method creates a buy order for each stock, and 
self.submit_order executes the purchase if theres is sufficient cash and the 
price is greater than zero. This process repeats every trading iteration to
adjust the portfolio based on updated momentum rankings. 

Finally, the script configures a Trader and an Alpaca broker instance,
linking the strategy to both. A backtesting period is defined, and 
the strategy runs through this timeframe using historical data from Yahoo
Finance. After the backtest is complete, A chart comparing the performance 
of the strategy vs the performance of SPY and a tear sheet with relevant 
indicators is created and displayed in the browser as an html. 
'''
