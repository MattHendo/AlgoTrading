from config import ALPACA_CONFIG
from lumibot.brokers import Alpaca
from lumibot.strategies import Strategy
from lumibot.traders import Trader


class ArbitrageStrategy(Strategy):
    def initialize(self):
        self.symbol1 = 'AAPL'
        self.symbol2 = 'MSFT'
        self.capital = 100000
        self.position_size = 100

    def run(self):
        data1 = self.get_historical_data(self.symbol1, '1D', '2020-01-01', '2023-01-01')
        data2 = self.get_historical_data(self.symbol2, '1D', '2020-01-01', '2023-01-01')

        data = pd.merge(data1['close'], data2['close'], left_index=True, right_index=True, suffixes=('_AAPL', '_MSFT'))
        data.dropna(inplace=True)

        # Calculate the spread and Z-score
        data['Spread'] = data['close_AAPL'] - data['close_MSFT']
        data['Z-score'] = (data['Spread'] - data['Spread'].mean()) / data['Spread'].std()

        for index, row in data.iterrows():
            if row['Z-score'] < -1:
                # Long AAPL, Short MSFT
                self.alpaca_api.submit_order(symbol=self.symbol1, qty=self.position_size, side='buy', type='market', time_in_force='gtc')
                self.alpaca_api.submit_order(symbol=self.symbol2, qty=self.position_size, side='sell', type='market', time_in_force='gtc')
            elif row['Z-score'] > 1:
                # Short AAPL, Long MSFT
                self.alpaca_api.submit_order(symbol=self.symbol1, qty=self.position_size, side='sell', type='market', time_in_force='gtc')
                self.alpaca_api.submit_order(symbol=self.symbol2, qty=self.position_size, side='buy', type='market', time_in_force='gtc')
            elif -0.5 < row['Z-score'] < 0.5:
                # Exit positions
                self.alpaca_api.submit_order(symbol=self.symbol1, qty=self.position_size, side='sell', type='market', time_in_force='gtc')
                self.alpaca_api.submit_order(symbol=self.symbol2, qty=self.position_size, side='buy', type='market', time_in_force='gtc')

if __name__ == "__main__":
    broker = Alpaca(ALPACA_CONFIG)
    strategy = ArbitrageStrategy(broker=broker)
    trader = Trader()
    trader.add_strategy(strategy)
    trader.run_all()