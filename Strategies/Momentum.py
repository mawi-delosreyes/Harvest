import requests
import sys
from decimal import Decimal
from Database.Database import Database
from Database.DataRetrieval import DataRetrieval
from Indicators.Signals import Signals
from Indicators.Indicators import Indicators
from Logging.Logger import Logger
from Coins.GenerateSignature import generateTradeSignature
from Coins.constants import host

class Momentum:
    def __init__(self, crypto):
        self.crypto = crypto
        self.sma_fast = None
        self.sma_slow = None
        # self.ema_fast = None
        # self.ema_slow = None
        # self.macd = None
        # self.signal_line = None
        self.plus_di = None
        self.minus_di = None
        self.adx = None
        self.logger = Logger(crypto)


    # def checkSignals(self):
    #     if all(value is not None for value in [self.sma_fast, self.sma_slow, self.ema_fast, self.ema_slow, self.macd, self.signal_line,
    #                                     self.plus_di, self.minus_di, self.adx]):

    #         indicator_signals = Signals(self.sma_fast, self.sma_slow, self.ema_fast, self.ema_slow, self.macd, self.signal_line,
    #                                     self.plus_di, self.minus_di, self.adx)
            
    #         self.logger.info(f"SMA Signal: {indicator_signals.SMA()}")
    #         self.logger.info(f"MACD Signal: {indicator_signals.MACD()}")
    #         self.logger.info(f"ADX Signal: {indicator_signals.ADX()}")
    #         self.signal = -1
    #         if indicator_signals.SMA() == 1 and indicator_signals.MACD() == 1 and indicator_signals.ADX() == 1:
    #             self.signal = 1

    def checkSignals(self):
        if all(value is not None for value in [self.sma_fast, self.sma_slow, self.plus_di, self.minus_di, self.adx]):

            indicator_signals = Signals(self.sma_fast, self.sma_slow, self.plus_di, self.minus_di, self.adx)
            
            self.logger.info(f"SMA Signal: {indicator_signals.SMA()}")
            self.logger.info(f"ADX Signal: {indicator_signals.ADX()}")
            self.signal = -1
            if indicator_signals.SMA() == 1 and indicator_signals.ADX() == 1:
                self.signal = 1


    def retrieveData(self):

        # col_names = "crypto.id, sma.sma_fast, sma.sma_slow, macd.ema_fast, macd.ema_slow, macd.macd, macd.signal_line, " \
        # "adx.atr, adx.plus_di, adx.minus_di, adx.adx"

        # select_crypto_data_query = "SELECT %s FROM %s AS crypto " % (col_names, self.crypto) 
        # select_crypto_data_query += "LEFT JOIN %s_SMA as sma ON crypto.id=sma.id " % (self.crypto)
        # select_crypto_data_query += "LEFT JOIN %s_MACD as macd ON crypto.id=macd.id "  % (self.crypto)
        # select_crypto_data_query += "LEFT JOIN %s_ADX as adx ON crypto.id=adx.id "  % (self.crypto)
        # select_crypto_data_query +=  "ORDER BY crypto.id DESC LIMIT 1"

        # latest_data = Database(self.crypto).retrieveData(select_crypto_data_query)[0]

        # sma, macd, adx = Indicators(self.crypto).runIndicators()
        sma, adx = Indicators(self.crypto).runIndicators()

        self.sma_fast = sma[0]
        self.sma_slow = sma[1]
        # self.ema_fast = macd[0]
        # self.ema_slow = macd[1]
        # self.macd = macd[2]
        # self.signal_line = macd[3]
        self.adx = adx[0]
        self.atr = adx[1]
        self.plus_di = adx[2]
        self.minus_di = adx[3]


    def tradeExecution(self):

        purchase_signal = None
        order_url = "openapi/v1/order"
        time_url = host + "openapi/v1/time"

        check_hold_query = "SELECT hold FROM User WHERE user_id = 1"
        hold = Database(self.crypto).retrieveData(check_hold_query)
        server_timestamp = requests.get(time_url).json()["serverTime"]
        wallet_info = DataRetrieval(self.crypto, self.crypto+'PHP').getWalletBalance(server_timestamp)
        trade_fee = DataRetrieval(self.crypto, self.crypto+'PHP').getTradeFees(server_timestamp)

        self.logger.info("Trade Signal: " + str(self.signal))

        # Emergency stop
        # if float(wallet_info["PHP"]['free']) < 150.00 and float(wallet_info[self.crypto]['free']) < 0.01 and self.signal == 1:
        #     self.logger.info("Emergency Stop Triggered: Low Funds")
        #     sys.exit(0)


        # No Position
        if hold[0][0] == 0 and self.signal == 1:

            crypto_price = Decimal(DataRetrieval(self.crypto, self.crypto + "PHP").getPrice(server_timestamp)[4])
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
                self.logger.info("Buy Signal Detected")
                purchase_signal = "buy"
                estimated_crypto_amount = Decimal(wallet_info['PHP']['free']) / crypto_price
                take_profit = crypto_price + ((estimated_crypto_amount * Decimal(trade_fee[self.crypto+"PHP"]['takerCommission'])) * crypto_price) + (self.atr * 2)
                stop_loss = crypto_price + ((estimated_crypto_amount * Decimal(trade_fee[self.crypto+"PHP"]['takerCommission'])) * crypto_price) - (self.atr * Decimal(1.5))

                params = {
                    "symbol": self.crypto + "PHP",
                    "side": purchase_signal,
                    "type": "MARKET",
                    "quoteOrderQty": wallet_info['PHP']['free'],
                    "timestamp": server_timestamp,
                }

                order_url, api_key, params['signature'] = generateTradeSignature(order_url, params)

                headers = {
                    'X-COINS-APIKEY': api_key
                }
                
                try:
                    response = requests.post(order_url, params=params, headers=headers)
                    self.logger.info("Order Response: {}".format(response.json()))
                except Exception as e:
                    self.logger.error("Error executing order: {}".format(e))
                    sys.exit(0)

                update_statement = "take_profit={}, stop_loss={}".format(take_profit, stop_loss)
                condition = "WHERE crypto_name='{self.crypto}'"
                Database(self.crypto).updateDB('Cryptocurrency', update_statement, condition)
                self.logger.info("Updated Take Profit: {}, Stop Loss: {}".format(take_profit, stop_loss))

                condition = "WHERE user_id=1"
                Database(self.crypto).updateDB('User', "hold=1", condition)
                self.logger.info("Added hold")

        # With Position
        else: 
            retrieve_data_query = "SELECT take_profit, stop_loss FROM Cryptocurrency WHERE crypto_name = '{}'".format(self.crypto)
            profits = Database(self.crypto).retrieveData(retrieve_data_query)
            take_profit = profits[0][0]
            stop_loss = profits[0][1]

            crypto_price = float(DataRetrieval(self.crypto, self.crypto + "PHP").getPrice(server_timestamp)[4])
            if ((crypto_price >= take_profit or crypto_price <= stop_loss) or (self.signal == 0 or self.signal == -1)) and hold[0][0] == 1:    
                self.logger.info("Sell Signal Detected")

                if self.crypto == "XRP":
                    quantity = int(Decimal(wallet_info[self.crypto]['free']) * 100) / 100
                elif self.crypto == "ETH":
                    quantity = int(Decimal(wallet_info[self.crypto]['free']) * 1000000) / 1000000
                elif self.crypto == "SOL":
                    quantity = int(Decimal(wallet_info[self.crypto]['free']) * 10000) / 10000

                params = {
                    "symbol": self.crypto + "PHP",
                    "side": "SELL",
                    "type": "MARKET",
                    "quantity": quantity,
                    "timestamp": server_timestamp,
                }

                order_url, api_key, params['signature'] = generateTradeSignature(order_url, params)

                headers = {
                    'X-COINS-APIKEY': api_key
                }
                
                try:
                    response = requests.post(order_url, params=params, headers=headers)
                    self.logger.info("Order Response: {}".format(response.json()))
                except Exception as e:
                    self.logger.error("Error executing order: {}".format(e))
                    sys.exit(0)

                update_statement = "take_profit=0, stop_loss=0"
                condition = "WHERE crypto_name='{self.crypto}'"
                Database(self.crypto).updateDB('Cryptocurrency', update_statement, condition)
                self.logger.info("Updated Take Profit: 0, Stop Loss: 0")

                condition = "WHERE user_id=1"
                Database(self.crypto).updateDB('User', "hold=0", condition)
                self.logger.info("Removed hold")
