import threading
import sys
from decimal import Decimal
from Indicators.SMA import SMA
from Indicators.MACD import MACD
from Indicators.ADX import ADX
from Indicators.Kijun_Sen import KijunSen
from Indicators.RSI import RSI
from Indicators.OBV import OBV
from Indicators.RSI import RSI
from Indicators.Fibonacci import Fibonacci
from Logging.Logger import Logger
from Database.Database import Database
from Database.DataRetrieval import DataRetrieval


class Indicators:
    def __init__(self, crypto):
        self.logger = Logger(crypto)
        self.crypto = crypto
        self.sma_short_period = 20
        self.sma_long_period = 50
        self.macd_fast_period = 3
        self.macd_slow_period = 10
        self.macd_signal_line_period = 3
        self.adx_period = 9
        self.bb_period = 14
        self.bb_std_dev = 2.0
        self.kijun_sen_period = 13
        self.rsi_period = 14
        self.rows = max(self.sma_short_period, self.sma_long_period, self.macd_fast_period, self.macd_slow_period, 
                        self.macd_signal_line_period, self.adx_period, self.bb_period, self.kijun_sen_period, self.rsi_period) + self.kijun_sen_period
        self.latest_crypto_data = None


    def retrieveDatabaseData(self, interval):

        col_names = "crypto.id, crypto.open_timestamp, crypto.open, crypto.high, crypto.low, crypto.close, crypto.volume"

        select_crypto_data_query = "SELECT * FROM ("
        if interval == "1m":
            select_crypto_data_query += "SELECT %s FROM %s AS crypto " % (col_names, self.crypto + "_1") 
        elif interval == "5m":
            select_crypto_data_query += "SELECT %s FROM %s AS crypto " % (col_names, self.crypto + "_5") 
        select_crypto_data_query += "ORDER BY crypto.id DESC LIMIT %s" % (self.rows) 
        select_crypto_data_query += ") AS crypto_data ORDER BY crypto_data.open_timestamp ASC"

        return Database(self.crypto).retrieveData(select_crypto_data_query)


    def runIndicators(self, interval='1m'):
        num_data = max(self.sma_short_period, self.sma_long_period, self.macd_fast_period, self.macd_slow_period, 
                        self.macd_signal_line_period, self.rsi_period)

        try:
            self.latest_crypto_data = self.retrieveDatabaseData(interval)
        except Exception as e:
            self.logger.error(e)

        if not self.latest_crypto_data or len(self.latest_crypto_data) < num_data: 
            self.logger.error("Not enough data")
            sys.exit(0)

        (_, _, open, high, low, close, volume
        ) = zip(*self.latest_crypto_data)

        open = list(open)
        high = list(high)
        low = list(low)
        close = list(close)
        volume = list(volume)

        latest_data = DataRetrieval(self.crypto, self.crypto + "PHP").getPrice(True, "1m")
        open.append(Decimal(latest_data[1]))
        high.append(Decimal(latest_data[2]))
        low.append(Decimal(latest_data[3]))
        close.append(Decimal(latest_data[4]))
        volume.append(Decimal(latest_data[5]))

        sma = SMA(self.crypto, close, self.sma_short_period, None, self.sma_long_period)
        macd = MACD(self.crypto, close, self.macd_fast_period, self.macd_slow_period, self.macd_signal_line_period)
        adx = ADX(self.crypto, high, low, close, self.adx_period)
        kijun = KijunSen(self.crypto, high, low, self.kijun_sen_period)
        obv = OBV(self.crypto, close, volume)
        rsi = RSI(self.crypto, close, self.rsi_period)
        fib = Fibonacci(self.crypto, high, low, 20)

        try:
            sma_thread = threading.Thread(target=sma.computeSMA)
            macd_thread = threading.Thread(target=macd.computeMACD)
            adx_thread = threading.Thread(target=adx.computeADX)
            kijun_thread = threading.Thread(target=kijun.computeKijunSen)
            obv_thread = threading.Thread(target=obv.computeOBV)
            rsi_thread = threading.Thread(target=rsi.computeRSI)
            fib_thread = threading.Thread(target=fib.computeFibonacci)

            sma_thread.start()
            macd_thread.start()
            adx_thread.start()
            kijun_thread.start()
            obv_thread.start()
            rsi_thread.start()
            fib_thread.start()

            sma_thread.join()
            macd_thread.join()
            adx_thread.join()
            kijun_thread.join()
            obv_thread.join()
            rsi_thread.join()
            fib_thread.join()

            sma_trend = sum([c[3] for c in self.latest_crypto_data[-30:]]) / 30
            candle_body = close[-1] - open[-1]

            return sma.result, macd.result, adx.result, kijun.result, obv.result, rsi.result, fib.levels, close[-1], sma_trend, candle_body

        except Exception as e:
            self.logger.error(e)