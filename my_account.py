import time, datetime
import os
from colors import Colors
import ccxt
import pandas as pd


class MyAccount:

    def __init__(self, exchange_id, public_key, secret):

        self.exchange_id = exchange_id
        self.public_key = public_key
        self.secret = secret

        exchange_id = self.exchange_id
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            'apiKey': self.public_key,
            'secret': self.secret,
        })

        self.file_name = "monitor_your_balance.csv"
        self.sleep_time = 600

    def monitor_your_balance(self):
        self.write_header()
        while True:
            self.write_balance()
            time.sleep(self.sleep_time)

    def write_balance(self):

        timestamp = datetime.datetime.timestamp(datetime.datetime.now())

        if os.path.isfile(self.file_name):
            file = open(self.file_name, 'a')
            out_str = ''

            out_str += f'{timestamp},'
            out_str += f'{self.get_balance_for_all_assets()},'
            out_str += f'{"USDT"},'

            out_str += '\n'

            file.write(out_str)

        else:
            print(f'{Colors.FAIL}There is no file{Colors.ENDC}')

    def write_header(self):

        # create file with header
        if not os.path.isfile(self.file_name):

            file = open(self.file_name, 'w')

            str_header = ''

            str_header += 'timestamp,'
            str_header += 'total,'
            str_header += 'USDT,'

            str_header += '\n'

            file.write(str_header)

    def get_balance_for_asset(self, asset):

        df = self.get_df_balances()
        df = df.loc[df.asset == asset]
        free = df.iloc[0]['free'].astype(float)
        locked = df.iloc[0]['locked'].astype(float)
        return free, locked

    def get_balance_for_all_assets(self):

        df = self.get_df_balances()

        df = df[(df.free > 0.0) | (df.locked > 0.0)]  # filter blank

        df['recent_quotes'] = 0.0  # init values

        for index, row in df.iterrows():

            if row['asset'] != 'USDT':

                pair = row['asset'] + '/' + 'USDT'
                ticker = self.try_fetch_ticker(pair)
                df.at[index, 'recent_quotes'] = float(ticker['last'])

            else:

                df.at[index, 'recent_quotes'] = 1.0  # only for USDT

        # convert all to USDT
        df['free_in_usdt'] = df['free'] * df['recent_quotes']
        df['locked_in_usdt'] = df['locked'] * df['recent_quotes']
        df['balance_in_usdt'] = df['free_in_usdt'] + df['locked_in_usdt']

        # only for view
        columns = ['asset', 'recent_quotes', 'balance_in_usdt']
        print(f"Balances:\n {df[columns]}")

        balance_for_all_assets = df['balance_in_usdt'].sum()
        return balance_for_all_assets

    def get_df_balances(self):

        balances = self.exchange.fetch_balance()

        df = pd.DataFrame(balances['info']['balances'])
        df['free'] = df['free'].astype(float)
        df['locked'] = df['locked'].astype(float)

        return df

    def try_fetch_ticker(self, pair):

        ticker = {'last': 0.0}

        try:
            ticker = self.exchange.fetch_ticker(pair)
        except Exception as ex:
            print(f'{Colors.FAIL}Exception occurred {Colors.BOLD}{ex}{Colors.ENDC}')

        return ticker
