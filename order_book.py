import ccxt


class OrderBook:

    def __init__(self, exchange, market):

        if exchange == 'binance':
            self.binance = ccxt.binance()
        else:
            print('There is no exchange')

        self.binance.load_markets()

        self.market = self.binance.market(market)

        print(self.market)

    def information(self):
        out_str = ''

        out_str += f'symbol: {self.market["symbol"]}\n'
        out_str += f'precision: {self.market["precision"]}\n'

        print(out_str)





