import requests
from decimal import Decimal
from Database.Database import Database
from Database.DataRetrieval import DataRetrieval
from Indicators.Signals import Signals
from Coins.GenerateSignature import generateSignature
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
        self.take_profit = 10
        self.stop_loss = 5


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
        order_url = "openapi/v1/order/test"
        current_milliseconds = int(datetime.now().timestamp() * 1000)

        #trade_info = DataRetrieval(self.crypto, self.crypto+'PHP').getWalletBalance()[0]['balances']['asset']
        trade_info = {
            "accountType":"SPOT",
            "canDeposit":True,
            "canTrade":True,
            "canWithdraw":True,
            "balances":[
                {
                    "asset":"PHP",
                    "free":"100",
                    "locked":"0"
                }
            ],
            "token":"PHP",
            "daily":{
                "cashInLimit":"500000",
                "cashInRemaining":"499994",
                "cashOutLimit":"500000",
                "cashOutRemaining":"500000",
                "totalWithdrawLimit":"500000",
                "totalWithdrawRemaining":"500000"
            },
            "monthly":{
                "cashInLimit":"10000000",
                "cashInRemaining":"9999157",
                "cashOutLimit":"10000000",
                "cashOutRemaining":"10000000",
                "totalWithdrawLimit":"10000000",
                "totalWithdrawRemaining":"10000000"
            },
            "annually":{
                "cashInLimit":"120000000",
                "cashInRemaining":"119998577",
                "cashOutLimit":"120000000",
                "cashOutRemaining":"119999488",
                "totalWithdrawLimit":"120000000",
                "totalWithdrawRemaining":"119998487.97"
            },
            "updateTime":1707273549694
        }

        asset = trade_info['balances'][0]['asset']
        quantity = trade_info['balances'][0]['free']

        # No Position
        if asset == "PHP":

            crypto_price = float(DataRetrieval(self.crypto, self.crypto + "PHP").getPrice()[4])

            if self.signal == 1 or self.signal == -1:
                if self.signal == 1:
                    purchase_signal = "buy"
                    take_profit = Decimal(crypto_price) + (2 * self.atr)
                    stop_loss = Decimal(crypto_price) - self.atr

                elif self.signal == -1:
                    purchase_signal = "sell"
                    take_profit = Decimal(crypto_price) - (2 * self.atr)
                    stop_loss = Decimal(crypto_price) + self.atr

                else:
                    purchase_signal = None  


                params = {
                    "symbol": self.crypto + "PHP",
                    "side": purchase_signal,
                    "type": "LIMIT",
                    "price": quantity,
                    "timestamp": current_milliseconds,
                }
                order_url, api_key, params['signature'] = generateSignature(order_url, params)

                headers = {
                    'X-COINS-APIKEY': api_key
                }
                
                response = requests.post(order_url, params=params, headers=headers)

                update_statement = "take_profit={}, stop_loss={}".format(take_profit, stop_loss)
                Database(self.crypto).updateDB('Cryptocurrency', update_statement)

        # With Position
        else:

            retrieve_data_query = "SELECT take_profit, stop_loss FROM Cryptocurrency WHERE crypto_name = '{}'".format(self.crypto)
            profits = Database(self.crypto).retrieveData(retrieve_data_query)
            take_profit = profits[0][0]
            stop_loss = profits[0][1]
            crypto_price = float(DataRetrieval(self.crypto, self.crypto + "PHP").getPrice()[4])

            if (crypto_price >= take_profit or crypto_price <= stop_loss) or self.signal == 0:
                params = {
                    "symbol": asset + "PHP",
                    "side": "SELL",
                    "type": "MARKET",
                    "quantity": quantity,
                    "timestamp": current_milliseconds,
                }

                order_url, api_key, params['signature'] = generateSignature(order_url, params)

                headers = {
                    'X-COINS-APIKEY': api_key
                }
                
                response = requests.post(order_url, params=params, headers=headers)

                update_statement = "take_profit=0, stop_loss=0"
                Database(self.crypto).updateDB('Cryptocurrency', update_statement)


if __name__ == '__main__':
    crypto = "XRP"

    strategy = Momentum(crypto)
    strategy.retrieveData()
    strategy.checkSignals()
    strategy.tradeExecution()