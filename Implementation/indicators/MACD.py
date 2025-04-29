class MACD:
    def __init__(self, data, fast, slow, signalPeriod, prev_fast_ema, prev_slow_ema, prev_signal):
        self.data = data
        self.fast = fast
        self.slow = slow
        self.signalPeriod = signalPeriod  
        self.fastSmoothingFactor = 2 / (self.fast + 1)
        self.slowSmoothingFactor = 2 / (self.slow + 1)
        self.signalSmoothingFactor = 2 / (self.signalPeriod + 1)
        self.prev_fast_ema = prev_fast_ema
        self.prev_slow_ema = prev_slow_ema
        self.prev_signal = prev_signal


    def computeEMA(self):
        if len(self.data) < self.slow:
            print("Not enough data to compute fast and slow EMA")
            return None, None

        fast_ema = (self.data[-1] - self.prev_fast_ema) * self.fastSmoothingFactor + self.prev_fast_ema
        slow_ema = (self.data[-1] - self.prev_slow_ema) * self.slowSmoothingFactor + self.prev_slow_ema

        return fast_ema, slow_ema


    def computeSignalLine(self, macd):
        signal_line = (macd - self.prev_signal) * self.signalSmoothingFactor + self.prev_signal

        return signal_line


    def computeMACD(self):
        fast_ema, slow_ema = self.computeEMA()
        if fast_ema is None or slow_ema is None:
            return None, None, None, None

        macd = fast_ema - slow_ema
        signal_line = self.computeSignalLine(macd)

        return fast_ema, slow_ema, macd, signal_line
