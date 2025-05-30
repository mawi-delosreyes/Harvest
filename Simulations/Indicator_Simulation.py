import threading
import sys
from decimal import Decimal
from Indicators.SMA import SMA
from Indicators.MACD import MACD
from Indicators.ADX import ADX
from Indicators.Bollinger_Bands import BoillingerBands
from Indicators.Pivot_Points import PivotPoints
from Indicators.Kijun_Sen import KijunSen
from Indicators.RSI import RSI
from Indicators.OBV import OBV
from Indicators.Forecast import Forecast
from Logging.Logger import Logger
from Database.Database import Database
from Database.DataRetrieval import DataRetrieval


class Indicator_Simulation:
    def __init__(self, crypto, data):
        self.logger = Logger(crypto)
        self.crypto = crypto
        # self.sma_fast_period = 5
        # self.sma_slow_period = 15
        # self.macd_fast_period = 5
        # self.macd_slow_period = 14
        # self.macd_signal_line_period = 6
        # self.adx_period = 10
        # self.bb_period = 14
        # self.bb_std_dev = 2.5
        # self.kijun_sen_period = 20
        # self.rsi_period = 9
        self.sma_short_period = 9
        self.sma_mid_period = 30
        self.sma_long_period = 50
        self.macd_fast_period = 12
        self.macd_slow_period = 26
        self.macd_signal_line_period = 9
        self.adx_period = 20
        self.bb_period = 25
        self.bb_std_dev = 2.5
        self.kijun_sen_period = 34
        self.rsi_period = 20
        self.rows = max(self.sma_short_period, self.sma_mid_period, self.sma_long_period, self.macd_fast_period, self.macd_slow_period, 
                        self.macd_signal_line_period, self.adx_period, self.bb_period, self.kijun_sen_period, self.rsi_period) + self.kijun_sen_period
        self.latest_crypto_data = data


    def runIndicators(self):
        min_data = max(self.sma_short_period, self.sma_mid_period, self.sma_long_period, self.macd_fast_period, self.macd_slow_period, 
                        self.macd_signal_line_period, self.adx_period, self.bb_period, self.kijun_sen_period, self.rsi_period, 50)

        if not self.latest_crypto_data or len(self.latest_crypto_data) < min_data: 
            self.logger.error("Not enough data")
            sys.exit(0)

        (open, high, low, close, volume
        ) = zip(*self.latest_crypto_data)

        open = list(open)
        high = list(high)
        low = list(low)
        close = list(close)
        volume = list(volume)

        sma = SMA(self.crypto, close, self.sma_short_period, self.sma_mid_period, self.sma_long_period)
        macd = MACD(self.crypto, close, self.macd_fast_period, self.macd_slow_period, self.macd_signal_line_period)
        adx = ADX(self.crypto, high, low, close, self.adx_period)
        bb = BoillingerBands(self.crypto, close, self.bb_period, self.bb_std_dev)
        kijun = KijunSen(self.crypto, high, low, self.kijun_sen_period)
        obv = OBV(self.crypto, close, volume)
        pp = PivotPoints(self.crypto, high[-2], low[-2], close[-2])
        rsi = RSI(self.crypto, close, self.rsi_period)
        forecast = Forecast(close)

        try:
            forecast_thread = threading.Thread(target=forecast.computeForecast)
            sma_thread = threading.Thread(target=sma.computeSMA)
            macd_thread = threading.Thread(target=macd.computeMACD)
            adx_thread = threading.Thread(target=adx.computeADX)
            bb_thread = threading.Thread(target=bb.computeBollingerBands)
            kijun_thread = threading.Thread(target=kijun.computeKijunSen)
            obv_thread = threading.Thread(target=obv.computeOBV)
            pp_thread = threading.Thread(target=pp.computePivotPoint)
            rsi_thread = threading.Thread(target=rsi.computeRSI)

            forecast_thread.start()
            sma_thread.start()
            macd_thread.start()
            adx_thread.start()
            bb_thread.start()
            kijun_thread.start()
            obv_thread.start()
            pp_thread.start()
            rsi_thread.start()

            forecast_thread.join()
            sma_thread.join()
            macd_thread.join()
            adx_thread.join()
            bb_thread.join()
            kijun_thread.join()
            obv_thread.join()
            pp_thread.join()
            rsi_thread.join()

            return sma.result, macd.result, adx.result, bb.result, kijun.result, obv.result, pp.result, rsi.result, close[-1], forecast.result

        except Exception as e:
            self.logger.error(e)