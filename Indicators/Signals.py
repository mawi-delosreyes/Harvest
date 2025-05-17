class Signals:
    def __init__(self, sma_fast, sma_slow, plus_di, minus_di, adx):
    # def __init__(self, sma_fast, sma_slow, ema_fast, ema_slow, macd, signal_line, plus_di, minus_di, adx):
        self.sma_fast = sma_fast
        self.sma_slow = sma_slow
        # self.ema_fast = ema_fast
        # self.ema_slow = ema_slow
        # self.macd = macd
        # self.signal_line = signal_line
        self.plus_di = plus_di
        self.minus_di = minus_di
        self.adx = adx
    
    def SMA(self):
        if self.sma_fast > self.sma_slow:
            return 1  # Buy signal
        elif self.sma_fast < self.sma_slow:
            return -1  # Sell signal
        else:
            return 0  # No signal
        
    def MACD(self):
        if self.ema_fast > self.ema_slow and self.macd > self.signal_line:
            return 1  # Buy signal
        elif self.ema_fast < self.ema_slow and self.macd < self.signal_line:
            return -1  # Sell signal
        else:
            return 0  # No signal
        
    def ADX(self):
        if self.adx > 20 and self.plus_di > self.minus_di:
            return 1  # Buy signal
        elif self.adx > 20 and self.minus_di > self.plus_di:
            return -1  # Sell signal
        else:
            return 0  # No signal
