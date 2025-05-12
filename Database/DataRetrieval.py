import requests
from datetime import datetime
from .Database import Database
from Logging.Logger import Logger
from Indicators.Indicators import Indicators
from Coins.GenerateSignature import generateSignature
from Coins.constants import host

class DataRetrieval:
    def __init__(self, crypto, cryptoPair):
        self.crypto = crypto
        self.cryptoPair = cryptoPair.lower()
        self.interval = "5m"
        self.logger = Logger(crypto)


    def getPrice(self):

        prices_url = host + "openapi/quote/v1/klines"

        current_milliseconds = int(datetime.now().timestamp() * 1000)
        params = {
            "symbol": self.cryptoPair,
            "interval": self.interval,
            "limit": 2,
            "startTime": current_milliseconds
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
    
    
    def getWalletBalance(self):
        account_url = "openapi/v1/account"
        current_milliseconds = int(datetime.now().timestamp() * 1000)

        params = {
            "timestamp": current_milliseconds
        }

        account_url, api_key, params['signature'] = generateSignature(account_url, params)

        headers = {
            'X-COINS-APIKEY': api_key
        }

        response = requests.get(account_url, params=params, headers=headers)
        data = response.json()
        
        return data['balances']


    def saveData(self):
        open_timestamp, open, high, low, close, volume, close_timestamp, quote_asset_volume, num_trades = self.getPrice()
        crypto_columns = "(open_timestamp, open, high, low, close, volume, close_timestamp, quote_asset_volume, num_trades)"
        crypto_data_value = (open_timestamp, open, high, low, close, volume, close_timestamp, quote_asset_volume, num_trades)
        
        try:
            last_data_index = Database(self.crypto).saveDB(self.crypto, self.crypto, crypto_columns, crypto_data_value)

            indicators = Indicators(self.crypto)
            sma, macd, adx = indicators.runIndicators()
            
            if all(value is not None for value in sma):
                sma_table = self.crypto + "_SMA"
                sma_columns = "(id, sma_fast, sma_slow)"
                sma_data_values = (last_data_index, sma[0], sma[1])
                Database(self.crypto).saveDB("SMA", sma_table, sma_columns, sma_data_values)

            if all(value is not None for value in macd):
                macd_table = self.crypto + "_MACD"
                macd_columns = "(id, ema_fast, ema_slow, macd, signal_line)"
                macd_data_values = (last_data_index, macd[0], macd[1], macd[2], macd[3])
                Database(self.crypto).saveDB("MACD", macd_table, macd_columns, macd_data_values)

            if all(value is not None for value in adx):
                adx_table = self.crypto + "_ADX"
                adx_columns = "(id, atr, plus_di, minus_di, adx)"
                adx_data_values = (last_data_index, adx[1], adx[2], adx[3], adx[0])
                Database(self.crypto).saveDB("ADX", adx_table, adx_columns, adx_data_values)
            
        
        except Exception as e:
            self.logger.error(e)
            


if __name__ == "__main__":
    crypto = "XRP"
    cryptoPair = "XRPPHP"
    retrieval = DataRetrieval(crypto, cryptoPair)
    retrieval.saveData()
