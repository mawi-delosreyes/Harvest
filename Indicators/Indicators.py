import threading
import sys
from .SMA import SMA
from .MACD import MACD
from .ADX import ADX, ATR
from Logging.Logger import Logger
from Database.Database import Database


class Indicators:
    def __init__(self, crypto):
        self.logger = Logger(crypto)
        self.crypto = crypto
        self.sma_fast_period = 9
        self.sma_slow_period = 21
        self.macd_fast_period = 12
        self.macd_slow_period = 26
        self.macd_signal_line_period = 9
        self.adx_period = 14
        self.rows = max(self.sma_fast_period, self.sma_slow_period, 
                        self.macd_fast_period, self.macd_slow_period, self.macd_signal_line_period,
                        self.adx_period) + self.macd_signal_line_period
        self.latest_crypto_data = None


    def retrieveDatabaseData(self):

        col_names = "crypto.id, crypto.open_timestamp, crypto.open, crypto.high, crypto.low, crypto.close, crypto.volume"

        select_crypto_data_query = "SELECT * FROM ("
        select_crypto_data_query += "SELECT %s FROM %s AS crypto " % (col_names, self.crypto) 
        select_crypto_data_query += "ORDER BY crypto.id DESC LIMIT %s" % (self.rows) 
        select_crypto_data_query += ") AS crypto_data ORDER BY crypto_data.open_timestamp ASC"

        return Database(self.crypto).retrieveData(select_crypto_data_query)


    def runIndicators(self):

        min_data =max(self.sma_fast_period, self.sma_slow_period, self.macd_fast_period, self.macd_slow_period, 
                      self.macd_signal_line_period, self.adx_period)

        try:
            self.latest_crypto_data = self.retrieveDatabaseData()
        except Exception as e:
            self.logger.error(e)

        if not self.latest_crypto_data or len(self.latest_crypto_data) < min_data: 
            self.logger.error("Not enough data")
            sys.exit(0)

        (_, _, open, high, low, close, volume
        ) = zip(*self.latest_crypto_data)

        open = list(open)
        high = list(high)
        low = list(low)
        close = list(close)
        volume = list(volume)

        sma = SMA(self.crypto, close, self.sma_fast_period, self.sma_slow_period)
        macd = MACD(self.crypto, close, self.macd_fast_period, self.macd_slow_period, self.macd_signal_line_period)
        adx = ADX(self.crypto, high, low, close, self.adx_period)

        try:
            sma_thread = threading.Thread(target=sma.computeSMA)
            macd_thread = threading.Thread(target=macd.computeMACD)
            adx_thread = threading.Thread(target=adx.computeADX)

            sma_thread.start()
            macd_thread.start()
            adx_thread.start()

            sma_thread.join()
            macd_thread.join()
            adx_thread.join()

            return sma.result, macd.result, adx.result
        
        except Exception as e:
            self.logger.error(e)