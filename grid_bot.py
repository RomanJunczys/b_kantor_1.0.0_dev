from colors import Colors
from config_account_reader import ConfigAccountReader
from config_strategy_reader import ConfigStrategyReader
from my_account import MyAccount
import ccxt
import time


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

        print('Testing initialisation')
        self.symbol = config_account_reader.get_market_symbol()

        ticker = self.exchange.fetch_ticker(self.symbol)
        print(f'change: {ticker["change"]} percentage: {ticker["percentage"]}')

        self.config_strategy_reader = ConfigStrategyReader('config_strategy.yaml')

        self.closed_order_status = self.config_strategy_reader.get_filled_order_status()
        self.canceled_order_status = self.config_strategy_reader.get_canceled_order_status()

        self.check_orders_frequency = self.config_strategy_reader.get_check_orders_frequency()
        self.grid_size = self.config_strategy_reader.get_grid_size()
        self.position_size = self.config_strategy_reader.get_position_size()

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

        end_of_life_cycle = False
        type_of_terminate = None
        message = None

        self.buy_or_sell_to_balance()
        self.create_buy_and_sell_orders()

        while not end_of_life_cycle:

            self.checking_for_open_buy_orders()
            self.checking_for_open_sell_orders()

            self.clean_orders_lists()

            end_of_life_cycle, type_of_terminate, message = self.check_bot_termination_condition()

        Colors.print_red(f'End of life cycle {message}')

        self.cancel_all_orders()

        return type_of_terminate

    def checking_for_open_buy_orders(self):

        self.closed_order_ids = []

        for buy_order in self.buy_orders:

            Colors.print_cyan(f"Checking for open buy orders {Colors.BOLD}{buy_order['id']}")

            order = self.try_fetch_order(buy_order['id'], self.symbol)

            order_info = order['info']

            if order_info['status'] == self.closed_order_status:
                self.closed_order_ids.append(order['id'])

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

        for sell_order in self.sell_orders:

            print(f'Checking for open buy orders {sell_order["id"]}')

            order = self.try_fetch_order(sell_order['id'], self.symbol)

            order_info = order['info']
            print(f"status: {order_info['status']}")
            if order_info['status'] == self.closed_order_status:
                self.closed_order_ids.append(order['id'])
                price = float(order_info["price"])
                Colors.print_purple(f'SELL order filled / executed at {order_info["price"]}')
                new_buy_price = price - self.grid_size
                self.create_limit_buy_order(new_buy_price)

            if order_info['status'] == self.canceled_order_status:
                self.closed_order_ids.append(order['id'])

    def create_limit_buy_order(self, new_buy_price):

        Colors.print_blue(f'creating new limit BUY order at {new_buy_price:.4f}')

        new_buy_order = self.exchange.create_limit_sell_order(self.symbol, self.position_size, new_buy_price)
        self.sell_orders.append(new_buy_order)

    def checking_for_open_buy_and_sell_order_old(self):

        while True:

            self.closed_order_ids = []

            for buy_order in self.buy_orders:

                print(f"Checking for open buy orders {buy_order['id']}")

                order = self.try_fetch_order(buy_order['id'], self.symbol)

                order_info = order['info']
                print(f"status: {order_info['status']}")
                if order_info['status'] == self.closed_order_status:
                    self.closed_order_ids.append(order['id'])
                    print(f'BUY order executed at {order_info["price"]}')
                    new_sell_price = float(order_info['price']) + self.grid_size
                    print(f'creating new limit sell order at {new_sell_price:.4f}')
                    new_sell_order = self.exchange.create_limit_sell_order(self.symbol, self.position_size, new_sell_price)
                    self.sell_orders.append(new_sell_order)

                if order_info['status'] == self.canceled_order_status:
                    self.closed_order_ids.append(order['id'])

                # time.sleep(self.check_orders_frequency)

            for sell_order in self.sell_orders:

                print(f'Checking for open buy orders {sell_order["id"]}')

                order = self.try_fetch_order(sell_order['id'], self.symbol)

                order_info = order['info']
                print(f"status: {order_info['status']}")
                if order_info['status'] == self.closed_order_status:
                    self.closed_order_ids.append(order['id'])
                    print(f'SELL order executed at {order_info["price"]}')
                    new_buy_price = float(order_info["price"]) - self.grid_size
                    print(f'creating new limit buy order at {new_buy_price:.4f}')
                    new_buy_order = self.exchange.create_limit_buy_order(self.symbol, self.position_size, new_buy_price)
                    self.buy_orders.append(new_buy_order)

                if order_info['status'] == self.canceled_order_status:
                    self.closed_order_ids.append(order['id'])

                # time.sleep(self.check_orders_frequency)

            self.clean_orders_lists()
            time.sleep(self.check_orders_frequency)

            terminate, type_of_terminate, message = self.check_bot_termination_condition()
            if terminate:
                print(f'{Colors.OKBLUE}End of small loop{Colors.ENDC}')
                return type_of_terminate

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
            print(f'Market: base: {base_name} / counter: {counter_name}')

            my_account = MyAccount(self.exchange_name, self.public_key, self.secret)

            free_base, locked_base = my_account.get_balance_for_asset(base_name)
            total_base = free_base + locked_base
            print(f'Asset: {base_name} balance is {total_base}.'
                  f'       - Details:  free: {free_base} locked: {locked_base}')

            free_counter, locked_counter = my_account.get_balance_for_asset(counter_name)
            total_counter = free_counter + locked_counter
            print(f'Asset: {counter_name} balance is {total_counter}:'
                  f'       - Details: free: {free_counter} locked: {locked_counter}')

            ticker = self.exchange.fetch_ticker(self.symbol)
            last_value = float(ticker['last'])

            print(f'Last value: {last_value}')
            print(f'Asset: {base_name} balance is {total_base * last_value} [{counter_name}].')
            print(f'Asset: {counter_name} balance is {total_counter / last_value}: [{base_name}]')

            total_in_base = total_base + total_counter / last_value
            total_in_counter = total_base * last_value + total_counter
            print(f'Total in base {total_in_base} [{base_name}]')
            print(f'Total in counter {total_in_counter} [{counter_name}]')

            min_amount_in_counter = 10.1  # USDT
            min_amount_in_base = min_amount_in_counter / last_value

            if total_base * last_value < total_counter:
                half = total_in_base / 2.0
                need_buy = half - total_base
                print(f'Need buy {need_buy} {base_name}')
                if need_buy > min_amount_in_base:
                    order = self.exchange.create_market_buy_order(self.symbol, need_buy)
                    print(order)

            elif total_base * last_value >= total_counter:
                half = total_in_base / 2.0
                need_sell = total_base - half
                print(f'Need sell {need_sell} {base_name}')
                if need_sell > min_amount_in_base:
                    order = self.exchange.create_market_sell_order(self.symbol, need_sell)
                    print(order)

    def print_balance(self):

        base_name, counter_name = self.symbol.split('/')
        print(f'Market: base: {base_name} / counter: {counter_name}')

        my_account = MyAccount(self.exchange_name, self.public_key, self.secret)

        free_base, locked_base = my_account.get_balance_for_asset(base_name)
        total_base = free_base + locked_base
        print(f'Asset: {base_name} balance is {total_base}.'
              f'       - Details:  free: {free_base} locked: {locked_base}')

        free_counter, locked_counter = my_account.get_balance_for_asset(counter_name)
        total_counter = free_counter + locked_counter
        print(f'Asset: {counter_name} balance is {total_counter}:'
              f'       - Details: free: {free_counter} locked: {locked_counter}')

        ticker = self.exchange.fetch_ticker(self.symbol)
        last_value = float(ticker['last'])

        print(f'Last value: {last_value}')
        print(f'Asset: {base_name} balance is {total_base*last_value} [{counter_name}].')
        print(f'Asset: {counter_name} balance is {total_counter/last_value}: [{base_name}]')

        total_in_base = total_base + total_counter/last_value
        total_in_counter = total_base*last_value + total_counter
        print(f'Total in base {total_in_base} [{base_name}]')
        print(f'Total in counter {total_in_counter} [{counter_name}]')

        if total_base*last_value < total_counter:
            half = total_in_base / 2.0
            need_buy = half - total_base
            print(f'Need buy {need_buy} {base_name}')
        elif total_base*last_value >= total_counter:
            half = total_in_counter / 2.0
            need_buy = half - total_counter
            print(f'Need buy {need_buy} {counter_name}')

    def create_buy_and_sell_orders(self):

        num_buy_grid_lines = self.config_strategy_reader.get_num_buy_grid_lines()
        num_sell_grid_lines = self.config_strategy_reader.get_num_sell_grid_lines()
        ticker = self.exchange.fetch_ticker(symbol=self.symbol)

        for i in range(num_buy_grid_lines):
            price = float(ticker['bid']) - (self.grid_size * (i + 1))
            print(f'submitting limit BUY order at {price:.4f}')
            order = self.exchange.create_limit_buy_order(self.symbol, self.position_size, price)
            self.buy_orders.append(order)

        for i in range(num_sell_grid_lines):
            price = float(ticker['bid']) + (self.grid_size * (i + 1))
            print(f'submitting limit SELL order at {price:.4f}')
            order = self.exchange.create_limit_sell_order(self.symbol, self.position_size, price)
            self.sell_orders.append(order)

    def cancel_all_orders(self):

        if len(self.sell_orders) > 0:
            print(f'Length of sell orders: {len(self.sell_orders)}')
            for order in self.sell_orders:
                print(f'Order: {order}')
                canceled = self.exchange.cancel_order(order['id'], order['symbol'])
                print(f'{order["id"]} canceled {canceled}')
            self.sell_orders = []

        if len(self.buy_orders) > 0:
            print(f'Length of buy orders: {len(self.buy_orders)}')
            for order in self.buy_orders:
                print(f'Order: {order}')
                canceled = self.exchange.cancel_order(order['id'], order['symbol'])
                print(f'{order["id"]} canceled {canceled}')
            self.buy_orders = []






