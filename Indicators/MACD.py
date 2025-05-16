import sys
from decimal import Decimal
from Logging.Logger import Logger

class MACD:
    def __init__(self, crypto, close_data, fast, slow, signalPeriod):
        self.close_data = close_data
        self.fast = fast
        self.slow = slow
        self.signalPeriod = signalPeriod  
        self.macd_values = []
        self.result = None
        self.logger = Logger(crypto)
        self.crypto = crypto


    def computeWilderEMA(self, data, period):
        if len(data) < period:
            self.logger.info("Not enough data to compute EMA")
            sys.exit(0)

        ema_values = []
        sma = sum(Decimal(x) for x in data[:period]) / Decimal(period)
        ema_values.append(sma)

        for price in data[period:]:
            price = Decimal(price)
            ema_prev = ema_values[-1]
            ema = (ema_prev * (Decimal(period) - Decimal('1')) + price) / Decimal(period)
            ema_values.append(ema)
        return ema_values


    def computeSignalLine(self):
        if len(self.macd_values) < self.signalPeriod:
            self.logger.info("Not enough data to compute signal line")
            sys.exit(0)
        return self.computeWilderEMA(self.macd_values, self.signalPeriod)


    def computeMACD(self):
        if len(self.close_data) < self.slow:
            self.logger.error("Not enough data to compute MACD and signal line.")
            sys.exit(0)

        fast_ema = self.computeWilderEMA(self.close_data, self.fast)
        slow_ema = self.computeWilderEMA(self.close_data, self.slow)

        min_len = min(len(fast_ema), len(slow_ema))
        for i in range(min_len):
            macd = fast_ema[-min_len + i] - slow_ema[-min_len + i]
            self.macd_values.append(macd)

        if len(self.macd_values) < self.signalPeriod:
            self.logger.error("Not enough MACD values to compute signal line.")
            sys.exit(0)

        signal_line = self.computeSignalLine()
        self.result = (fast_ema[-1], slow_ema[-1], self.macd_values[-1], signal_line[-1])
