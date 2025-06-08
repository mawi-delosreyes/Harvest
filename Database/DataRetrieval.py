import requests
from datetime import datetime
from .Database import Database
from Logging.Logger import Logger
from Coins.GenerateSignature import generateTradeSignature
from Coins.constants import host

class DataRetrieval:
    def __init__(self, crypto, cryptoPair):
        self.crypto = crypto
        self.interval = "5m"
        if crypto is not None:
            self.logger = Logger(crypto)
            self.cryptoPair = cryptoPair.lower()
        else:
            self.logger = Logger("Harvest")
            self.cryptoPair = None

    def saveDelayedData(self, last_timestamp):
        
        prices_url = host + "openapi/quote/v1/klines"
        time_url = host + "openapi/v1/time"

        start_milliseconds = int(last_timestamp.timestamp() * 1000)
        server_timestamp = requests.get(time_url).json()["serverTime"] - (5 * 60 * 1000)
        params = {
            "symbol": self.cryptoPair,
            "interval": self.interval,
            "startTime": start_milliseconds,
            "endTime": server_timestamp
        }

        response = requests.get(prices_url, params=params)
        data = response.json()
        for i in data:
            open_timestamp = datetime.fromtimestamp(i[0]/1000.0)
            open = i[1]
            high = i[2]
            low = i[3]
            close = i[4]
            volume = i[5]
            close_timestamp = datetime.fromtimestamp(i[6]/1000.0)
            quote_asset_volume = i[7]
            num_trades = i[8]

            crypto_columns = "(open_timestamp, open, high, low, close, volume, close_timestamp, quote_asset_volume, num_trades)"
            crypto_data_value = (open_timestamp, open, high, low, close, volume, close_timestamp, quote_asset_volume, num_trades)

            Database(self.crypto).saveDB(self.crypto, self.crypto, crypto_columns, crypto_data_value)


    def getPrice(self, not_db_price=False):
        prices_url = host + "openapi/quote/v1/klines"
        time_url = host + "openapi/v1/time"
        server_timestamp = requests.get(time_url).json()["serverTime"]

        params = {
            "symbol": self.cryptoPair,
            "interval": self.interval,
            "limit": 2,
            "startTime": server_timestamp
        }

        response = requests.get(prices_url, params=params)
        if not_db_price:
            data = response.json()[-1]
        else:
            data = response.json()[0]
        
        open_timestamp = datetime.fromtimestamp(data[0]/1000.0)
        open = data[1]
        high = data[2]
        low = data[3]
        close = data[4]
        volume = data[5]
        close_timestamp = datetime.fromtimestamp(data[6]/1000.0)
        quote_asset_volume = data[7]
        num_trades = data[8]

        return open_timestamp, open, high, low, close, volume, close_timestamp, quote_asset_volume, num_trades
    

    def getCryptoPrice(self):
        prices_url = host + "openapi/quote/v1/ticker/price"
        
        params = {
            "symbol": self.cryptoPair
        }

        response = requests.get(prices_url, params=params)
        price = response.json()[0]['price']

        return price
    

    def getTradeFees(self, server_timestamp):
        tradeFee_url = "openapi/v1/asset/tradeFee"

        params = {
            "symbol": self.cryptoPair.upper(),
            "timestamp": server_timestamp,
            "recvWindow": 10000,
        }

        tradeFee_url, api_key, params['signature'] = generateTradeSignature(tradeFee_url, params)
        headers = {
            'X-COINS-APIKEY': api_key,
        }

        response = requests.get(tradeFee_url, params=params, headers=headers)
        data = response.json()
        crypto_balance = {entry['symbol']: entry for entry in data}
        return crypto_balance
    

    def getWalletBalance(self, server_timestamp):
        account_url = "openapi/v1/account"

        params = {
            "timestamp": server_timestamp,
            'recvWindow': 10000,
        }

        account_url, api_key, params['signature'] = generateTradeSignature(account_url, params)
        headers = {
            'X-COINS-APIKEY': api_key,
        }

        response = requests.get(account_url, params=params, headers=headers)
        try:
            data = response.json()
            wallet_balance = {entry['asset']: entry for entry in data['balances']}
        except Exception as e:
            print(response.json())
        return wallet_balance
    

    def saveWalletBalance(self):
        time_url = host + "openapi/v1/time"
        server_timestamp = requests.get(time_url).json()["serverTime"]

        wallet_balance = self.getWalletBalance(server_timestamp)
        crypto_price = self.getCryptoPrice()


        total_php = float(wallet_balance["PHP"]['free'])
        total_php += float(wallet_balance[self.crypto]['free']) * float(crypto_price)

        balance_columns = "(timestamp, user_id, balance)"
        balance_value = (datetime.now(), '1', total_php)
        
        Database(self.crypto).saveDB(self.crypto, "Daily_Balance", balance_columns, balance_value)


    def saveCryptoData(self):
        open_timestamp, open, high, low, close, volume, close_timestamp, quote_asset_volume, num_trades = self.getPrice(False)
        crypto_columns = "(open_timestamp, open, high, low, close, volume, close_timestamp, quote_asset_volume, num_trades)"
        crypto_data_value = (open_timestamp, open, high, low, close, volume, close_timestamp, quote_asset_volume, num_trades)
        
        try:
            Database(self.crypto).saveDB(self.crypto, self.crypto, crypto_columns, crypto_data_value)
        except Exception as e:
            self.logger.error(e)
            