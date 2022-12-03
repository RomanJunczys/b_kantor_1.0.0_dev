import yaml


class ConfigStrategyReader:

    strategy_config: {}
    
    def __init__(self, account_file_name):
        self.account_file_name = account_file_name
        self.__read_strategy_account()
        
    def __read_strategy_account(self):
        with open(self.account_file_name, 'r') as file:
            self.strategy_config = yaml.safe_load(file)
            return self.strategy_config

    def print_config_strategy(self):
        out_str = ''

        out_str += f'Position size: {self.get_position_size()}\n'
        out_str += f'Check orders frequency: {self.get_check_orders_frequency()}\n'
        out_str += f'Close order status: {self.get_filled_order_status()}\n'
        out_str += f'Number of buy grid lines: {self.get_num_buy_grid_lines()}\n'
        out_str += f'Number of sell grid lines: {self.get_num_sell_grid_lines()}\n'
        out_str += f'Grid size: {self.get_grid_size()}\n'

        print(out_str)

    # STRATEGY section

    def get_position_size(self):
        position_size = float(self.strategy_config['STRATEGY']['POSITION_SIZE'])
        return position_size

    def get_check_orders_frequency(self):
        check_orders_frequency = int(self.strategy_config['STRATEGY']['CHECK_ORDERS_FREQUENCY'])
        return check_orders_frequency

    def get_filled_order_status(self):
        closed_order_status = self.strategy_config['STRATEGY']['FILLED_ORDER_STATUS']
        return closed_order_status

    def get_canceled_order_status(self):
        canceled_order_status = self.strategy_config['STRATEGY']['CANCELED_ORDER_STATUS']
        return canceled_order_status

    # grid bot section

    def get_num_buy_grid_lines(self):
        num_buy_grid_lines = int(self.strategy_config['GRID_BOT']['NUM_BUY_GRID_LINES'])
        return num_buy_grid_lines

    def get_num_sell_grid_lines(self):
        num_sell_grid_lines = int(self.strategy_config['GRID_BOT']['NUM_SELL_GRID_LINES'])
        return num_sell_grid_lines

    def get_grid_size(self):
        grid_size = float(self.strategy_config['GRID_BOT']['GRID_SIZE'])
        return grid_size
