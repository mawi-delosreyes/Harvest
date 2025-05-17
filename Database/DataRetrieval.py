import requests
from datetime import datetime
from .Database import Database
from Logging.Logger import Logger
from Indicators.Indicators import Indicators
from Coins.GenerateSignature import generateTradeSignature
from Coins.constants import host

class DataRetrieval:
    def __init__(self, crypto, cryptoPair):
        self.crypto = crypto
        self.cryptoPair = cryptoPair.lower()
        self.interval = "5m"
        self.logger = Logger(crypto)


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


    def getPrice(self, server_timestamp):
        prices_url = host + "openapi/quote/v1/klines"

        params = {
            "symbol": self.cryptoPair,
            "interval": self.interval,
            "limit": 2,
            "startTime": server_timestamp
        }

        response = requests.get(prices_url, params=params)
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
        xrp_price = response.json()['price']

        return xrp_price
    

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
            'recvWindow': 5000,
        }

        account_url, api_key, params['signature'] = generateTradeSignature(account_url, params)
        headers = {
            'X-COINS-APIKEY': api_key,
        }

        response = requests.get(account_url, params=params, headers=headers)
        data = response.json()
        wallet_balance = {entry['asset']: entry for entry in data['balances']}
        return wallet_balance
    

    def saveWalletBalance(self):
        wallet_balance = self.getWalletBalance()
        crypto_price = self.getCryptoPrice()


        total_php = float(wallet_balance["PHP"]['free'])
        total_php += float(wallet_balance[self.crypto]['free']) * float(crypto_price)

        balance_columns = "(timestamp, user_id, balance)"
        balance_value = (datetime.now(), '1', total_php)
        
        Database(self.crypto).saveDB(self.crypto, "Daily_Balance", balance_columns, balance_value)


    def saveCryptoData(self):
        open_timestamp, open, high, low, close, volume, close_timestamp, quote_asset_volume, num_trades = self.getPrice()
        crypto_columns = "(open_timestamp, open, high, low, close, volume, close_timestamp, quote_asset_volume, num_trades)"
        crypto_data_value = (open_timestamp, open, high, low, close, volume, close_timestamp, quote_asset_volume, num_trades)
        
        try:
            Database(self.crypto).saveDB(self.crypto, self.crypto, crypto_columns, crypto_data_value)
            # last_data_index = Database(self.crypto).saveDB(self.crypto, self.crypto, crypto_columns, crypto_data_value)

            # indicators = Indicators(self.crypto)
            # sma, macd, adx = indicators.runIndicators()
            
            # if all(value is not None for value in sma):
            #     sma_table = self.crypto + "_SMA"
            #     sma_columns = "(id, sma_fast, sma_slow)"
            #     sma_data_values = (last_data_index, sma[0], sma[1])
            #     Database(self.crypto).saveDB("SMA", sma_table, sma_columns, sma_data_values)

            # if all(value is not None for value in macd):
            #     macd_table = self.crypto + "_MACD"
            #     macd_columns = "(id, ema_fast, ema_slow, macd, signal_line)"
            #     macd_data_values = (last_data_index, macd[0], macd[1], macd[2], macd[3])
            #     Database(self.crypto).saveDB("MACD", macd_table, macd_columns, macd_data_values)

            # if all(value is not None for value in adx):
            #     adx_table = self.crypto + "_ADX"
            #     adx_columns = "(id, atr, plus_di, minus_di, adx)"
            #     adx_data_values = (last_data_index, adx[1], adx[2], adx[3], adx[0])
            #     Database(self.crypto).saveDB("ADX", adx_table, adx_columns, adx_data_values)
            
        
        except Exception as e:
            self.logger.error(e)
            