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
        self.ema_fast = None
        self.ema_slow = None
        self.macd = None
        self.signal_line = None
        self.plus_di = None
        self.minus_di = None
        self.adx = None
        self.upper_band = None
        self.bb_sma = None
        self.lower_band = None
        self.kijun = None
        self.obv = None
        self.obv_prev = None
        self.pivot = None
        self.r1 = None
        self.s1 = None
        self.r2 = None
        self.s2 = None
        self.r3 = None
        self.s3 = None
        self.rsi = None
        self.close_price = None
        self.logger = Logger(crypto)


    def checkSignals(self):
        signal = 0

        if all(value is not None for value in [
            self.sma_fast, self.sma_slow, self.ema_fast, self.ema_slow, self.macd, self.signal_line,
            self.plus_di, self.minus_di, self.adx, self.upper_band, self.bb_sma, self.lower_band,
            self.kijun, self.obv, self.obv_prev, self.pivot, self.r1, self.s1, self.r2, self.s2,
            self.r3, self.s3, self.rsi, self.close_price
        ]):

            indicator_signals = Signals(self.sma_fast, self.sma_slow, self.ema_fast, self.ema_slow, self.macd, self.signal_line,
            self.plus_di, self.minus_di, self.adx, self.upper_band, self.bb_sma, self.lower_band,
            self.kijun, self.obv, self.obv_prev, self.pivot, self.r1, self.s1, self.r2, self.s2,
            self.r3, self.s3, self.rsi, self.close_price)

            signal = sum([
                indicator_signals.SMA(), 
                indicator_signals.MACD(), 
                indicator_signals.ADX(), 
                indicator_signals.BollingerBand(), 
                indicator_signals.Kijun(), 
                indicator_signals.OBV(), 
                indicator_signals.RSI(), 
                indicator_signals.PivotPoint(), 
            ])

            self.logger.info(f"SMA Signal: {indicator_signals.SMA()}")
            self.logger.info(f"MACD Signal: {indicator_signals.MACD()}")
            self.logger.info(f"ADX Signal: {indicator_signals.ADX()}")
            self.logger.info(f"Bollinger Band Signal: {indicator_signals.BollingerBand()}")
            self.logger.info(f"Kijun Signal: {indicator_signals.Kijun()}")
            self.logger.info(f"OBV Signal: {indicator_signals.OBV()}")
            self.logger.info(f"RSI Signal: {indicator_signals.RSI()}")
            self.logger.info(f"Pivot Point Signal: {indicator_signals.PivotPoint()}")
            self.logger.info(f"Total Points: {signal}")
        return signal


    def retrieveData(self):

        sma, macd, adx, bb, kijun, obv, pp, rsi, close_price = Indicators(self.crypto).runIndicators()

        self.sma_fast = sma[0]
        self.sma_slow = sma[1]
        self.ema_fast = macd[0]
        self.ema_slow = macd[1]
        self.macd = macd[2]
        self.signal_line = macd[3]
        self.adx = adx[0]
        self.atr = adx[1]
        self.plus_di = adx[2]
        self.minus_di = adx[3]
        self.upper_band = bb[0]
        self.bb_sma = bb[1]
        self.lower_band = bb[2]
        self.kijun = kijun
        self.obv = obv[0]
        self.obv_prev = obv[1]
        self.pivot = pp[0]
        self.r1 = pp[1]
        self.s1 = pp[2]
        self.r2 = pp[3]
        self.s2 = pp[4]
        self.r3 = pp[5]
        self.s3 = pp[6]
        self.rsi = rsi
        self.close_price = close_price


    def executeBuySignal(self, server_timestamp, signal):
        self.logger.info("Buy Signal Detected")

        order_url = "openapi/v1/order"
        wallet_info = DataRetrieval(self.crypto, self.crypto+'PHP').getWalletBalance(server_timestamp)
        crypto_price = Decimal(DataRetrieval(self.crypto, self.crypto + "PHP").getPrice(True)[4])

        params = {
            "symbol": self.crypto + "PHP",
            "side": "buy",
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

        trade = response.json()['fills'][0]
        php_converted_commission = Decimal(trade['commission']) * Decimal(trade['price'])
        take_profit = crypto_price + (php_converted_commission*2) + (self.atr * Decimal(2))
        stop_loss = crypto_price + (php_converted_commission*2) - (self.atr * Decimal(1.5))

        update_statement = "take_profit={}, stop_loss={}, hold=1".format(take_profit, stop_loss)
        condition = "WHERE crypto_name='{}'".format(self.crypto)
        Database(self.crypto).updateDB('Cryptocurrency', update_statement, condition)
        self.logger.info("Updated Take Profit: {}, Stop Loss: {}".format(take_profit, stop_loss))
        self.logger.info("Added hold")


    def executeTPSL(self, server_timestamp):
        retrieve_data_query = "SELECT take_profit, stop_loss FROM Cryptocurrency WHERE crypto_name = '{}'".format(self.crypto)
        profits = Database(self.crypto).retrieveData(retrieve_data_query)
        take_profit = profits[0][0]
        stop_loss = profits[0][1]

        crypto_price = float(DataRetrieval(self.crypto, self.crypto + "PHP").getPrice(True)[4])
        if crypto_price >= take_profit or crypto_price <= stop_loss:    
            self.logger.info("Sell Signal Detected")

            wallet_info = DataRetrieval(self.crypto, self.crypto+'PHP').getWalletBalance(server_timestamp)
            if self.crypto == "XRP":
                quantity = int(Decimal(wallet_info[self.crypto]['free']) * 100) / 100
            elif self.crypto == "BTC":
                quantity = int(Decimal(wallet_info[self.crypto]['free']) * 10000000) / 10000000
            elif self.crypto == "ETH":
                quantity = int(Decimal(wallet_info[self.crypto]['free']) * 1000000) / 1000000
            elif self.crypto == "SOL":
                quantity = int(Decimal(wallet_info[self.crypto]['free']) * 10000) / 10000
            elif self.crypto == "AL":
                quantity = int(Decimal(wallet_info[self.crypto]['free']) * 10) / 10

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

            update_statement = "take_profit=0, stop_loss=0, hold=0"
            condition = "WHERE crypto_name='{}'".format(self.crypto)
            Database(self.crypto).updateDB('Cryptocurrency', update_statement, condition)
            self.logger.info("Updated Take Profit: 0, Stop Loss: 0")
            self.logger.info("Removed hold")
