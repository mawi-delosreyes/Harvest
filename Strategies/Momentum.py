import requests
from decimal import Decimal
from Database.Database import Database
from Database.DataRetrieval import DataRetrieval
from Indicators.Signals import Signals
from Coins.GenerateSignature import generateTradeSignature
from datetime import datetime

class Momentum:
    def __init__(self, crypto):
        self.crypto = crypto
        self.sma_fast = None
        self.sma_slow = None
        self.ema_fast = None
        self.ema_slow = None
        self.macd = None
        self.signal_line = None
        self.plus_di = None
        self.minus_di = None
        self.adx = None


    def checkSignals(self):
        if all(value is not None for value in [self.sma_fast, self.sma_slow, self.ema_fast, self.ema_slow, self.macd, self.signal_line,
                                        self.plus_di, self.minus_di, self.adx]):

            indicator_signals = Signals(self.sma_fast, self.sma_slow, self.ema_fast, self.ema_slow, self.macd, self.signal_line,
                                        self.plus_di, self.minus_di, self.adx)
            
            self.signal = indicator_signals.SMA() * indicator_signals.MACD() * indicator_signals.ADX()


    def retrieveData(self):

        col_names = "crypto.id, sma.sma_fast, sma.sma_slow, macd.ema_fast, macd.ema_slow, macd.macd, macd.signal_line, " \
        "adx.atr, adx.plus_di, adx.minus_di, adx.adx"

        select_crypto_data_query = "SELECT %s FROM %s AS crypto " % (col_names, self.crypto) 
        select_crypto_data_query += "LEFT JOIN %s_SMA as sma ON crypto.id=sma.id " % (self.crypto)
        select_crypto_data_query += "LEFT JOIN %s_MACD as macd ON crypto.id=macd.id "  % (self.crypto)
        select_crypto_data_query += "LEFT JOIN %s_ADX as adx ON crypto.id=adx.id "  % (self.crypto)
        select_crypto_data_query +=  "ORDER BY crypto.id DESC LIMIT 1"

        latest_data = Database(self.crypto).retrieveData(select_crypto_data_query)[0]
        self.sma_fast = latest_data[1]
        self.sma_slow = latest_data[2]
        self.ema_fast = latest_data[3]
        self.ema_slow = latest_data[4]
        self.macd = latest_data[5]
        self.signal_line = latest_data[6]
        self.atr = latest_data[7]
        self.plus_di = latest_data[8]
        self.minus_di = latest_data[9]
        self.adx = latest_data[10]


    def tradeExecution(self):

        purchase_signal = None
        order_url = "openapi/v1/order"
        current_milliseconds = int(datetime.now().timestamp() * 1000)

        wallet_info = DataRetrieval(self.crypto, self.crypto+'PHP').getWalletBalance()
        wallet = {entry['asset']: entry for entry in wallet_info}

        # No Position
        if float(wallet[self.crypto]['free']) < 0.01 and self.signal == 1:

            crypto_price = float(DataRetrieval(self.crypto, self.crypto + "PHP").getPrice()[4])
            # if self.signal == 1 or self.signal == -1:
            #     if self.signal == 1:
            #         purchase_signal = "buy"
            #         take_profit = Decimal(crypto_price) + (2 * self.atr)
            #         stop_loss = Decimal(crypto_price) - self.atr

                # elif self.signal == -1:
                #     purchase_signal = "sell"
                #     take_profit = Decimal(crypto_price) - (2 * self.atr)
                #     stop_loss = Decimal(crypto_price) + self.atr

                # else:
                #     purchase_signal = None  

            if self.signal == 1:
                purchase_signal = "buy"
                take_profit = Decimal(crypto_price) + (2 * self.atr)
                stop_loss = Decimal(crypto_price) - self.atr

                params = {
                    "symbol": self.crypto + "PHP",
                    "side": purchase_signal,
                    "type": "MARKET",
                    "quoteOrderQty": wallet['PHP']['free'],
                    "timestamp": current_milliseconds,
                }

                print(params)
                order_url, api_key, params['signature'] = generateTradeSignature(order_url, params)

                headers = {
                    'X-COINS-APIKEY': api_key
                }
                
                response = requests.post(order_url, params=params, headers=headers)

                print(response.json())

                update_statement = "take_profit={}, stop_loss={}".format(take_profit, stop_loss)
                Database(self.crypto).updateDB('Cryptocurrency', update_statement)

        # With Position
        else: 
            retrieve_data_query = "SELECT take_profit, stop_loss FROM Cryptocurrency WHERE crypto_name = '{}'".format(self.crypto)
            profits = Database(self.crypto).retrieveData(retrieve_data_query)
            take_profit = profits[0][0]
            stop_loss = profits[0][1]
            crypto_price = float(DataRetrieval(self.crypto, self.crypto + "PHP").getPrice()[4])

            if (crypto_price >= take_profit or crypto_price <= stop_loss) or ((self.signal == 0 or self.signal == -1) and float(wallet[self.crypto]['free']) > 0.01):
                params = {
                    "symbol": self.crypto + "PHP",
                    "side": "SELL",
                    "type": "MARKET",
                    "quantity": int(float(wallet[self.crypto]['free']) * 100) / 100,
                    "timestamp": current_milliseconds,
                }

                order_url, api_key, params['signature'] = generateTradeSignature(order_url, params)

                headers = {
                    'X-COINS-APIKEY': api_key
                }
                
                response = requests.post(order_url, params=params, headers=headers)

                print(response.json())

                update_statement = "take_profit=0, stop_loss=0"
                Database(self.crypto).updateDB('Cryptocurrency', update_statement)


if __name__ == '__main__':
    crypto = "XRP"

    strategy = Momentum(crypto)
    strategy.retrieveData()
    strategy.checkSignals()
    strategy.tradeExecution()