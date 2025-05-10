import threading

from .SMA import SMA
from .MACD import MACD
from .ADX import ADX, ATR
from Logging.Logger import Logger
from Database.Database import Database


class Indicators:
    def __init__(self, crypto):
        self.logger = Logger(crypto)
        self.crypto = crypto
        self.sma_fast_period = 10
        self.sma_slow_period = 30
        self.macd_fast_period = 12
        self.macd_slow_period = 26
        self.macd_signal_line_period = 9
        self.adx_period = 14
        self.rows = max(self.sma_fast_period, self.sma_slow_period, 
                        self.macd_fast_period, self.macd_slow_period, self.macd_signal_line_period,
                        self.adx_period)
        self.latest_crypto_data = None


    def retrieveDatabaseData(self):

        col_names = "crypto.id, crypto.open_timestamp, crypto.open, crypto.high, crypto.low, crypto.close, crypto.volume, " \
        "sma.sma_fast, sma.sma_slow, macd.ema_fast, macd.ema_slow, macd.macd, macd.signal_line, " \
        "adx.atr, adx.plus_di, adx.minus_di, adx.adx"

        select_crypto_data_query = "SELECT * FROM ("
        select_crypto_data_query += "SELECT %s FROM %s AS crypto " % (col_names, self.crypto) 
        select_crypto_data_query += "LEFT JOIN %s_SMA as sma ON crypto.id=sma.id " % (self.crypto)
        select_crypto_data_query += "LEFT JOIN %s_MACD as macd ON crypto.id=macd.id "  % (self.crypto)
        select_crypto_data_query += "LEFT JOIN %s_ADX as adx ON crypto.id=adx.id "  % (self.crypto)
        select_crypto_data_query +=  "ORDER BY crypto.id DESC LIMIT %s" % (self.rows) 
        select_crypto_data_query += ") AS crypto_data ORDER BY crypto_data.open_timestamp ASC"

        return Database(self.crypto).retrieveData(select_crypto_data_query)


    def runIndicators(self):

        try:
            self.latest_crypto_data = self.retrieveDatabaseData()
        except Exception as e:
            self.logger.error(e)

        if not self.latest_crypto_data or len(self.latest_crypto_data) < 17: 
            self.logger.error("Not enough data")
            return

        (_, _, open, high, low, close, volume,
            sma_fast, sma_slow, ema_fast, ema_slow,
            macd, signal_line, atr, plus_di, minus_di, adx
        ) = zip(*self.latest_crypto_data)

        open = list(open)
        high = list(high)
        low = list(low)
        close = list(close)
        volume = list(volume)
        sma_fast = list(sma_fast)
        sma_slow = list(sma_slow)
        ema_fast = list(ema_fast)
        ema_slow = list(ema_slow)
        macd = list(macd)
        signal_line = list(signal_line)
        atr = list(atr)
        plus_di = list(plus_di)
        minus_di = list(minus_di)
        adx = list(adx)

        sma = SMA(close, self.sma_fast_period, self.sma_slow_period)
        macd = MACD(close, self.macd_fast_period, self.macd_slow_period, self.macd_signal_line_period, ema_fast[-1], ema_slow[-1], signal_line[-1])
        adx = ADX(high, low, close, self.adx_period, atr[-1], plus_di[-1], minus_di[-1], adx[-1])

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