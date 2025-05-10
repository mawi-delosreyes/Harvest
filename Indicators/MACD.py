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
        self.prev_fast_ema = prev_fast_ema
        self.prev_slow_ema = prev_slow_ema
        self.prev_signal = prev_signal
        self.result = None

    def computeEMA(self):
        if len(self.close_data) < self.slow:
            print("Not enough data to compute fast and slow EMA")
            return None, None

        if self.prev_fast_ema != None:
            fast_ema = (self.close_data[-1] - self.prev_fast_ema) * self.fastSmoothingFactor + self.prev_fast_ema
        else: 
            fast_ema = sum(self.close_data[-self.fast:]) / self.fast

        if self.prev_slow_ema != None:
            slow_ema = (self.close_data[-1] - self.prev_slow_ema) * self.slowSmoothingFactor + self.prev_slow_ema
        else:
            slow_ema = sum(self.close_data[-self.slow:]) / self.slow

        return fast_ema, slow_ema


    def computeSignalLine(self, macd):

        if self.prev_signal != None:
            signal_line = (macd - self.prev_signal) * self.signalSmoothingFactor + self.prev_signal
        else: signal_line = macd

        return signal_line


    def computeMACD(self):
        fast_ema, slow_ema = self.computeEMA()
        if fast_ema is None or slow_ema is None:
            return None, None, None, None

        macd = fast_ema - slow_ema
        signal_line = self.computeSignalLine(macd)

        self.result = (fast_ema, slow_ema, macd, signal_line)
