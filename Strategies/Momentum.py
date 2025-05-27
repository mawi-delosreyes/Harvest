import requests
import sys
from decimal import Decimal, ROUND_HALF_UP
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
        self.sma_short = None
        self.sma_mid = None
        self.sma_long = None
        self.ema_fast = None
        self.ema_slow = None
        self.macd = None
        self.signal_line = None
        self.plus_di = None
        self.minus_di = None
        self.atr = None
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
        self.forecast_start = None
        self.forecast_end = None
        self.close_price = None
        self.logger = Logger(crypto)


    def checkSignals(self):
        indicator_signal = 0
        forecast_signal = 0
        if all(value is not None for value in [
            self.sma_short, self.sma_mid, self.sma_long, self.ema_fast, self.ema_slow, self.macd, self.signal_line,
            self.plus_di, self.minus_di, self.adx, self.upper_band, self.bb_sma, self.lower_band,
            self.kijun, self.obv, self.obv_prev, self.pivot, self.r1, self.s1, self.r2, self.s2,
            self.r3, self.s3, self.rsi, self.close_price, self.forecast_start, self.forecast_end
        ]):
            indicator_signals = Signals(self.sma_short, self.sma_mid, self.sma_long, self.ema_fast, self.ema_slow, self.macd, self.signal_line,
            self.plus_di, self.minus_di, self.adx, self.upper_band, self.bb_sma, self.lower_band,
            self.kijun, self.obv, self.obv_prev, self.pivot, self.r1, self.s1, self.r2, self.s2,
            self.r3, self.s3, self.rsi, self.close_price, self.forecast_start, self.forecast_end)

            weights = {
                'SMA': 1,
                'MACD': 2,
                'ADX': 1.5,
                'BollingerBand': 0.3,
                'Kijun': 1,
                'OBV': 0.2,
                'RSI': 1.5,
                'PivotPoint': 1,
                'Forecast': 2.5
            }

            indicator_signal = sum([
                indicator_signals.SMA() * weights['SMA'], 
                indicator_signals.MACD() * weights['MACD'], 
                indicator_signals.ADX() * weights['ADX'], 
                indicator_signals.BollingerBand() * weights['BollingerBand'], 
                indicator_signals.Kijun() * weights['Kijun'], 
                indicator_signals.OBV() * weights['OBV'], 
                indicator_signals.RSI() * weights['RSI'], 
                indicator_signals.PivotPoint() * weights['PivotPoint'], 
                indicator_signals.Forecast() * weights['Forecast']
            ])

            indicator_signal = float(Decimal(indicator_signal).quantize(Decimal('1.' + '0'*2), rounding=ROUND_HALF_UP))

            self.logger.info(f"SMA Signal: {indicator_signals.SMA()}")
            self.logger.info(f"MACD Signal: {indicator_signals.MACD()}")
            self.logger.info(f"ADX Signal: {indicator_signals.ADX()}")
            self.logger.info(f"Bollinger Band Signal: {indicator_signals.BollingerBand()}")
            self.logger.info(f"Kijun Signal: {indicator_signals.Kijun()}")
            self.logger.info(f"OBV Signal: {indicator_signals.OBV()}")
            self.logger.info(f"RSI Signal: {indicator_signals.RSI()}")
            self.logger.info(f"Pivot Point Signal: {indicator_signals.PivotPoint()}")
            self.logger.info(f"Forecast Signal: {indicator_signals.Forecast()}")
            self.logger.info(f"Total Points: {indicator_signal}")

            forecast_signal = indicator_signals.Forecast()
        return (indicator_signal, forecast_signal), (self.sma_mid, self.sma_long) 


    def retrieveData(self):

        sma, macd, adx, bb, kijun, obv, pp, rsi, close_price, forecast  = Indicators(self.crypto).runIndicators()
        self.sma_short = sma[0]
        self.sma_mid = sma[0]
        self.sma_long = sma[1]
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
        self.forecast_start = forecast[0]
        self.forecast_end = forecast[1]


    def executeBuySignal(self, server_timestamp):
        self.logger.info("Buy Signal Detected")

        order_url = "openapi/v1/order"
        wallet_info = DataRetrieval(self.crypto, self.crypto+'PHP').getWalletBalance(server_timestamp)

        params = {
            "symbol": self.crypto + "PHP",
            "side": "buy",
            "type": "MARKET",
            "quoteOrderQty": wallet_info['PHP']['free'],
            "timestamp": server_timestamp,
            "recvWindow": 10000,
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
        crypto_price = Decimal(trade['price'])
        risk_percent = Decimal("0.002")
        reward_percent = Decimal("0.003")
        qty = Decimal(trade['qty'])
        php_converted_commission = Decimal(trade['commission']) * Decimal(trade['price'])
        #total_fee_php = php_converted_commission * Decimal(2) 
        break_even_price = crypto_price + (php_converted_commission / qty)
        take_profit = break_even_price * (1 + reward_percent)
        stop_loss = crypto_price * (1 - risk_percent)

        update_statement = "take_profit={}, stop_loss={}, break_even={}, hold=1, cooldown=10".format(take_profit, stop_loss, break_even_price)
        condition = "WHERE crypto_name='{}'".format(self.crypto)
        Database(self.crypto).updateDB('Cryptocurrency', update_statement, condition)
        self.logger.info("Updated Take Profit: {}, Stop Loss: {}".format(take_profit, stop_loss))
        self.logger.info("Added hold")

        with open('/dev/tty8', 'w') as tty:
            tty.write("\n\nBought {} at price: {:.4f}. TP: {:.4f} SL:{:.4f}\n\n".format(self.crypto, crypto_price, take_profit, stop_loss))


    def executeTPSL(self, server_timestamp):
        self.logger.info("Sell Signal Detected")
        order_url = "openapi/v1/order"

        wallet_info = DataRetrieval(self.crypto, self.crypto+'PHP').getWalletBalance(server_timestamp)
        if self.crypto == "XRP":
            quantity = int(Decimal(wallet_info[self.crypto]['free']) * 100) / 100
        elif self.crypto == "BTC":
            quantity = int(Decimal(wallet_info[self.crypto]['free']) * 10000000) / 10000000
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
            "recvWindow": 10000,
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

        update_statement = "take_profit=0, stop_loss=0, break_even=0, hold=0, cooldown=15"
        condition = "WHERE crypto_name='{}'".format(self.crypto)
        Database(self.crypto).updateDB('Cryptocurrency', update_statement, condition)
        self.logger.info("Updated Take Profit: 0, Stop Loss: 0")
        self.logger.info("Removed hold")