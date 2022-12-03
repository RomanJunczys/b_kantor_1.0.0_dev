import threading
from config_account_reader import ConfigAccountReader
from config_strategy_reader import ConfigStrategyReader
from my_account import MyAccount
from grid_bot import GridBot

config_account_reader = ConfigAccountReader('config_account.yaml')
public_key = config_account_reader.get_public_key()
secret = config_account_reader.get_secret_key()
exchange_id = config_account_reader.get_exchange_name()

my_account = MyAccount(exchange_id, public_key, secret)
grid_bot = GridBot()


if __name__ == "__main__":

    thread_1 = threading.Thread(target=my_account.monitor_your_balance)
    thread_2 = threading.Thread(target=grid_bot.manage_bot_life)

    thread_1.start()
    thread_2.start()

    thread_1.join()
    thread_2.join()





