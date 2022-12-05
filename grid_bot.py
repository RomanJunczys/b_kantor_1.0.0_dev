import datetime
import pandas as pd
from colors import Colors
from config_account_reader import ConfigAccountReader
from config_strategy_reader import ConfigStrategyReader
from my_account import MyAccount
import ccxt
import time
import os


class GridBot:
    buy_orders = []
    sell_orders = []
    closed_order_ids = []

    def __init__(self):

        config_account_reader = ConfigAccountReader('config_account.yaml')
        self.exchange_name = config_account_reader.get_exchange_name()
        self.public_key = config_account_reader.get_public_key()
        self.secret = config_account_reader.get_secret_key()
        exchange_class = getattr(ccxt, self.exchange_name)
        self.exchange = exchange_class({
            'apiKey': self.public_key,
            'secret': self.secret,
        })
        self.symbol = config_account_reader.get_market_symbol()

        self.config_strategy_reader = ConfigStrategyReader('config_strategy.yaml')
        self.closed_order_status = self.config_strategy_reader.get_filled_order_status()
        self.canceled_order_status = self.config_strategy_reader.get_canceled_order_status()
        self.check_orders_frequency = self.config_strategy_reader.get_check_orders_frequency()
        self.grid_size = self.config_strategy_reader.get_grid_size()
        self.position_size = self.config_strategy_reader.get_position_size()

        self.file_name = 'bot_life_cycle.csv'

    def manage_bot_life(self):

        while True:

            type_of_terminate = self.bot_life_cycle()

            if type_of_terminate == 'overhead':
                Colors.print_blue('Overhead exit')
                time.sleep(0)

            elif type_of_terminate == 'downstairs':
                Colors.print_blue('Downstairs exit')
                time.sleep(300)

            else:
                print('Leave for other ideas')
                time.sleep(600)

    def bot_life_cycle(self):

        # bot life cycle monitoring
        self.set_file_name(self.file_name)
        self.write_header()

        end_of_life_cycle = False
        type_of_terminate = None
        message = None

        self.cancel_all_orders_on_startup()

        self.buy_or_sell_to_balance()

        self.save_the_initial_state()

        self.create_initial_buy_and_sell_orders()

        while not end_of_life_cycle:
            self.checking_for_open_buy_orders()
            self.checking_for_open_sell_orders()

            self.clean_orders_lists()

            end_of_life_cycle, type_of_terminate, message = self.check_bot_termination_condition()

        Colors.print_red(f'End of life cycle {message}')

        self.cancel_all_orders_at_the_end()

        self.save_the_final_state()

        return type_of_terminate

    def checking_for_open_buy_orders(self):

        # Colors.print_green("BUY")

        for buy_order in self.buy_orders:

            # Colors.print_cyan(f"   Checking for open BUY orders {Colors.BOLD}{buy_order['id']}")

            order = self.try_fetch_order(buy_order['id'], self.symbol)

            order_info = order['info']

            if order_info['status'] == self.closed_order_status:
                self.closed_order_ids.append(order['id'])

                # monitoring of cycle of life
                self.write_filled_order(order)

                price = float(order_info["price"])
                Colors.print_green(f'BUY order filled / executed at {price}')

                new_sell_price = price + self.grid_size
                self.create_limit_sell_order(new_sell_price)

            if order_info['status'] == self.canceled_order_status:
                self.closed_order_ids.append(order['id'])

    def create_limit_sell_order(self, new_sell_price):

        Colors.print_blue(f'creating new limit sell order at {new_sell_price:.4f}')

        new_sell_order = self.exchange.create_limit_sell_order(self.symbol, self.position_size, new_sell_price)
        self.sell_orders.append(new_sell_order)

    def checking_for_open_sell_orders(self):

        # Colors.print_red('SELL')

        for sell_order in self.sell_orders:

            # Colors.print_cyan(f'   Checking for open SELL orders {Colors.BOLD}{sell_order["id"]}')

            order = self.try_fetch_order(sell_order['id'], self.symbol)

            order_info = order['info']

            if order_info['status'] == self.closed_order_status:
                self.closed_order_ids.append(order['id'])

                # monitoring of cycle of life
                self.write_filled_order(order)

                price = float(order_info["price"])

                Colors.print_purple(f'SELL order filled / executed at {order_info["price"]}')
                new_buy_price = price - self.grid_size
                self.create_limit_buy_order(new_buy_price)

            if order_info['status'] == self.canceled_order_status:
                self.closed_order_ids.append(order['id'])

    def write_filled_order(self, order):

        print(f'order: \n\n'
              f'{order}')

        # date = order['datetime']
        date = pd.to_datetime(int(order['info']['updateTime']), unit='ms')
        market = order['symbol']
        type_ = order['info']['side']
        price = order['price']
        amount = order['amount']
        total = order['cost']
        fee = 0.0
        fee_coin = '_BNB_'

        # count
        balance = self.get_balance_of_bot()

        self.write_transaction(date, market, type_, price, amount, total, fee, fee_coin, balance)

    def create_limit_buy_order(self, new_buy_price):

        Colors.print_blue(f'creating new limit BUY order at {new_buy_price:.4f}')

        new_buy_order = self.exchange.create_limit_buy_order(self.symbol, self.position_size, new_buy_price)
        self.buy_orders.append(new_buy_order)

    def clean_orders_lists(self):

        for order_id in self.closed_order_ids:
            self.buy_orders = [buy_order for buy_order in self.buy_orders if buy_order['id'] != order_id]
            self.sell_orders = [sell_order for sell_order in self.sell_orders if sell_order['id'] != order_id]

    def check_bot_termination_condition(self):

        terminate = False
        type_of_terminate = ''
        message = ''

        if len(self.sell_orders) == 0:
            terminate = True
            message = 'Stopping bot, nothing left to sell'
            type_of_terminate = 'overhead'

        if len(self.buy_orders) == 0:
            terminate = True
            message = 'Stopping bot, probably lost money'
            type_of_terminate = 'downstairs'

        return terminate, type_of_terminate, message

    def try_fetch_order(self, id_order, symbol):
        while True:
            try:
                order = self.exchange.fetch_order(id_order, symbol)
                return order
            except Exception as ex:
                print(f'Exception occured {ex}')
                time.sleep(self.check_orders_frequency)
                continue

    def buy_or_sell_to_balance(self):

        base_name, counter_name = self.symbol.split('/')
        Colors.print_blue(f'Market base / counter: {Colors.BOLD}{base_name} / {counter_name}')

        my_account = MyAccount(self.exchange_name, self.public_key, self.secret)

        free_base, locked_base = my_account.get_balance_for_asset(base_name)
        total_base = free_base + locked_base
        Colors.print_blue(f'Asset: {base_name} balance is {total_base}.'
                          f'                   - Details:  free: {free_base} locked: {locked_base}')

        free_counter, locked_counter = my_account.get_balance_for_asset(counter_name)
        total_counter = free_counter + locked_counter
        Colors.print_blue(f'Asset: {counter_name} balance is {total_counter}:'
                          f'              - Details: free: {free_counter} locked: {locked_counter}')

        ticker = self.try_fetch_ticker(self.symbol)
        last_value = float(ticker['last'])

        Colors.print_blue(f'Last value: {Colors.BOLD}{last_value}')
        Colors.print_blue(f'For asset: {base_name} balance is {(total_base * last_value):.2f} in [{counter_name}].')
        Colors.print_blue(f'Fora asset: {counter_name} balance is {(total_counter / last_value):.6f}: in [{base_name}]')

        total_in_base = total_base + total_counter / last_value
        total_in_counter = total_base * last_value + total_counter
        Colors.print_blue(f'{Colors.BOLD}Total:')
        Colors.print_blue(f'Total in base: {Colors.BOLD}{total_in_base:.5f} in [{base_name}]')
        Colors.print_blue(f'Total in counter: {Colors.BOLD}{total_in_counter:.2f} in [{counter_name}]')

        min_amount_in_counter = 10.1  # USDT
        min_amount_in_base = min_amount_in_counter / last_value

        if total_base * last_value < total_counter:
            half = total_in_base / 2.0
            need_buy = half - total_base
            Colors.print_cyan(f'   Need buy {need_buy:.6f} {base_name}')
            if need_buy > min_amount_in_base:
                self.exchange.create_market_buy_order(self.symbol, need_buy)

        elif total_base * last_value >= total_counter:
            half = total_in_base / 2.0
            need_sell = total_base - half
            Colors.print_cyan(f'   Need sell {need_sell:.6f} {base_name}')
            if need_sell > min_amount_in_base:
                self.exchange.create_market_sell_order(self.symbol, need_sell)

    def try_fetch_ticker(self, symbol):
        while True:
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                return ticker
            except Exception as ex:
                Colors.print_red(f'Exception occurred: {Colors.BOLD}{ex}')
                continue

    def get_balance_of_bot(self):

        base_name, counter_name = self.symbol.split('/')

        my_account = MyAccount(self.exchange_name, self.public_key, self.secret)

        free_base, locked_base = my_account.get_balance_for_asset(base_name)
        total_base = free_base + locked_base

        free_counter, locked_counter = my_account.get_balance_for_asset(counter_name)
        total_counter = free_counter + locked_counter

        ticker = self.try_fetch_ticker(self.symbol)
        last_value = float(ticker['last'])

        total_in_counter = total_base * last_value + total_counter
        return total_in_counter

    def create_initial_buy_and_sell_orders(self):

        num_buy_grid_lines = self.config_strategy_reader.get_num_buy_grid_lines()
        num_sell_grid_lines = self.config_strategy_reader.get_num_sell_grid_lines()
        ticker = self.exchange.fetch_ticker(symbol=self.symbol)

        for i in range(num_sell_grid_lines):
            price = float(ticker['bid']) + (self.grid_size * (i + 1))
            Colors.print_purple(f'   Submitting limit SELL order at {price:.4f}')
            order = self.exchange.create_limit_sell_order(self.symbol, self.position_size, price)
            self.sell_orders.append(order)

        for i in range(num_buy_grid_lines):
            price = float(ticker['bid']) - (self.grid_size * (i + 1))
            Colors.print_green(f'   Submitting limit BUY order at {price:.4f}')
            order = self.exchange.create_limit_buy_order(self.symbol, self.position_size, price)
            self.buy_orders.append(order)

    def cancel_all_orders_on_startup(self):

        self.try_fetch_orders_and_fill_buy_sell_orders()
        time.sleep(1)
        self.cancel_all_orders_in_list()

    def cancel_all_orders_at_the_end(self):

        time.sleep(1)
        self.cancel_all_orders_in_list()

    def try_fetch_orders_and_fill_buy_sell_orders(self):

        orders = []

        while True:
            try:
                orders = self.exchange.fetch_orders(self.symbol)
                break
            except Exception as ex:
                Colors.print_red(f'Exception occurred {Colors.BOLD}{ex}')
                continue

        for order in orders:
            if order['info']['status'] == 'NEW':
                if order['info']['side'] == 'BUY':
                    self.buy_orders.append(order)
                elif order['info']['side'] == 'SELL':
                    self.sell_orders.append(order)

    def cancel_all_orders_in_list(self):

        if len(self.sell_orders) > 0:
            for order in self.sell_orders:
                self.try_cancel_order(order['id'], order['symbol'])
            self.sell_orders = []

        if len(self.buy_orders) > 0:
            for order in self.buy_orders:
                self.try_cancel_order(order['id'], order['symbol'])
            self.buy_orders = []

    def try_cancel_order(self, id_order, symbol):
        while True:
            try:
                order = self.exchange.cancel_order(id_order, symbol)
                return order
            except Exception as ex:
                print(f'Exception occured {ex}')
                time.sleep(self.check_orders_frequency)
                continue

    def set_file_name(self, file_name):
        current_time = str(datetime.datetime.now())
        current_time = current_time.replace(':', '-')
        self.file_name = f'{current_time[11:19]}_{file_name}'

    def write_header(self):

        if not os.path.isfile(self.file_name):
            file = open(self.file_name, 'w')

            str_header = ''

            str_header += 'Date(UTC),'
            str_header += 'Market,'
            str_header += 'Type,'
            str_header += 'Price,'
            str_header += 'Amount,'
            str_header += 'Total,'
            str_header += 'Fee,'
            str_header += 'Fee_Coin,'
            str_header += 'Balance,'

            str_header += '\n'

            file.write(str_header)

    def save_the_initial_state(self):

        date = str(datetime.datetime.now())
        market = self.symbol
        type_ = 'INITIAL'

        ticker = self.exchange.fetch_ticker(self.symbol)
        last_value = float(ticker['last'])

        price = last_value
        amount = 0.0
        total = 0.0
        fee = 0.0
        fee_coin = '_BNB_'

        # count
        balance = self.get_balance_of_bot()

        self.write_transaction(date, market, type_, price, amount, total, fee, fee_coin, balance)

    def write_transaction(self, date, market, transaction_type, price, amount, total, fee, fee_coin, balance):

        if os.path.isfile(self.file_name):
            file = open(self.file_name, 'a')

            str_row = ''

            str_row += f'{date},'
            str_row += f'{market},'
            str_row += f'{transaction_type},'
            str_row += f'{price},'
            str_row += f'{amount},'
            str_row += f'{total},'
            str_row += f'{fee},'
            str_row += f'{fee_coin},'
            str_row += f'{balance},'

            str_row += '\n'

            file.write(str_row)

    def save_the_final_state(self):

        date = str(datetime.datetime.now())
        market = self.symbol
        type_ = 'FINAL'

        ticker = self.exchange.fetch_ticker(self.symbol)
        last_value = float(ticker['last'])

        price = last_value
        amount = 0.0
        total = 0.0
        fee = 0.0
        fee_coin = '_BNB_'

        # count
        balance = self.get_balance_of_bot()

        self.write_transaction(date, market, type_, price, amount, total, fee, fee_coin, balance)
