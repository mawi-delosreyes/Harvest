import requests
import time
from datetime import datetime
from Database import Database

class DataRetrieval:
    def __init__(self, crypto, cryptoPair):
        self.crypto = crypto
        self.cryptoPair = cryptoPair.lower()
        self.interval = "5m"
        self.url = "https://api.pro.coins.ph/openapi/quote/v1/klines"

    def getPrice(self):

        current_milliseconds = int(datetime.now().timestamp() * 1000)
        params = {
            "symbol": self.cryptoPair,
            "interval": self.interval,
            "limit": 1,
            "startTime": current_milliseconds
        }

        response = requests.get(self.url, params=params)
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

        crypto_columns = "(open_timestamp, open, high, low, close, volume, close_timestamp, quote_asset_volume, num_trades)"
        crypto_data_value = (open_timestamp, open, high, low, close, volume, close_timestamp, quote_asset_volume, num_trades)
        Database().saveDB(self.crypto, crypto_columns, crypto_data_value)



if __name__ == "__main__":
    crypto = "XRP"
    cryptoPair = "XRPPHP"
    retrieval = DataRetrieval(crypto, cryptoPair)
    retrieval.getPrice()
