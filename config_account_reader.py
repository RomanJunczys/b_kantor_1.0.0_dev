import yaml


class ConfigAccountReader:
    
    account_config: {}
    
    def __init__(self, account_file_name):
        self.account_file_name = account_file_name
        self.__read_config_account()
    
    def __read_config_account(self):
        with open(self.account_file_name, 'r') as file:
            self.account_config = yaml.safe_load(file)
            return self.account_config

    def print_config_account(self):
        out_str = ''

        out_str += f'Exchange: {self.get_exchange_name()}\n'
        out_str += f'Market symbol: {self.get_market_symbol()}\n'
        out_str += f'Public Key: {self.get_public_key()}\n'
        out_str += f'Secret Key: {self.get_secret_key()}\n'

        print(out_str)

    def get_exchange_name(self):
        exchange = self.account_config['GENERAL']['EXCHANGE']
        return exchange
    
    def get_market_symbol(self):
        market_symbol = self.account_config['MARKET']['SYMBOL']
        return market_symbol
    
    def get_public_key(self):
        public_key = self.account_config['ACCOUNT']['PUBLIC_KEY']
        return public_key

    def get_secret_key(self):
        secret_key = self.account_config['ACCOUNT']['SECRET_KEY']
        return secret_key
