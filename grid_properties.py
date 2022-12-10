import pandas as pd
from datetime import datetime, timedelta
import ccxt

from config_account_reader import ConfigAccountReader


class GridProperties:

    def __init__(self):

        self.config_account_reader = ConfigAccountReader('config_account.yaml')
        exchange_name = self.config_account_reader.get_exchange_name()
        exchange_class = getattr(ccxt, exchange_name)
        self.exchange = exchange_class()

        self.market = self.config_account_reader.get_market_symbol()

    def get_spacing_for_hour(self):

        hours = 1
        unit = '1m'

        now = datetime.now()
        back = now - timedelta(hours=hours)
        back_timestamp = int(back.timestamp() * 1000)

        # print(f'now: {now} minus hours: {hours} is back time: {back}\nback timestamp is {back_timestamp}')

        ohlcv = self.get_all_ohlcv_for_pair(unit, back_timestamp)
        df = self.make_data_frame(ohlcv)

        all_values = []

        all_values.extend(df.Open.values)
        all_values.extend(df.High.values)
        all_values.extend(df.Low.values)
        all_values.extend(df.Close.values)

        df_all_values = pd.DataFrame(data=all_values)

        max_value = float(df_all_values.max())
        min_value = float(df_all_values.min())

        middle_value = min_value + (max_value - min_value) / 2.0

        # print(f'Max: {max_value:.7f} Middle: {middle_value:.7f} Min: {min_value:.7f}')

        spacing = (max_value - min_value) / 6.0

        return spacing

    def get_all_ohlcv_for_pair(self, unit, since):

        all_ohlcv = []

        ohlcv = self.exchange.fetch_ohlcv(symbol=self.market, timeframe=unit, since=since, limit=1000)
        all_ohlcv.extend(ohlcv)

        while len(ohlcv) == 1000:
            since_time_stamp = ohlcv[-1][0]
            ohlcv = self.exchange.fetch_ohlcv(symbol=self.market, timeframe=unit, since=since_time_stamp, limit=1000)
            all_ohlcv.extend(ohlcv)

        return all_ohlcv

    @staticmethod
    def make_data_frame(ohlcv):

        df = pd.DataFrame(ohlcv)
        df.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        df['Time'] = pd.to_datetime(df['Time'], unit='ms')
        df.set_index('Time', inplace=True)
        df = df.astype(float)

        return df
