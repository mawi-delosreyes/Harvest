from decimal import Decimal

class MACD:
    def __init__(self, close_data, fast, slow, signalPeriod, prev_fast_ema, prev_slow_ema, prev_signal):
        self.close_data = close_data
        self.fast = fast
        self.slow = slow
        self.signalPeriod = signalPeriod  
        self.fastSmoothingFactor = Decimal(str(2 / (self.fast + 1)))
        self.slowSmoothingFactor = Decimal(str(2 / (self.slow + 1)))
        self.signalSmoothingFactor = Decimal(str(2 / (self.signalPeriod + 1)))
        self.result = None

    def computeEMA(self):
        if len(self.close_data) < self.slow:
            print("Not enough data to compute fast and slow EMA")
            return None, None

        fast_ema = sum(self.close_data[-self.fast:]) / self.fast
        slow_ema = sum(self.close_data[-self.slow:]) / self.slow

        return fast_ema, slow_ema


    def computeSignalLine(self, macd):
        signal_line = macd
        return signal_line


    def computeMACD(self):
        fast_ema, slow_ema = self.computeEMA()
        if fast_ema is None or slow_ema is None:
            return None, None, None, None

        macd = fast_ema - slow_ema
        signal_line = self.computeSignalLine(macd)

        self.result = (fast_ema, slow_ema, macd, signal_line)
