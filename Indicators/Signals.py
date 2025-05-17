class Signals:

    def __init__(self, sma_fast, sma_slow, ema_fast, ema_slow, macd, signal_line,
                 plus_di, minus_di, adx, upper_band, bb_sma, lower_band,
                 kijun, obv, obv_prev, pivot, r1, s1, r2, s2, r3, s3, rsi, close_price):
        self.sma_fast = sma_fast
        self.sma_slow = sma_slow
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.macd = macd
        self.signal_line = signal_line
        self.plus_di = plus_di
        self.minus_di = minus_di
        self.adx = adx
        self.upper_band = upper_band
        self.bb_sma = bb_sma
        self.lower_band = lower_band
        self.kijun = kijun
        self.obv = obv
        self.obv_prev = obv_prev
        self.pivot = pivot
        self.r1 = r1
        self.s1 = s1
        self.r2 = r2
        self.s2 = s2
        self.r3 = r3
        self.s3 = s3
        self.rsi = rsi
        self.close_price = close_price

    
    def SMA(self):
        if self.sma_fast > self.sma_slow:
            return 1  # Buy signal
        else:
            return -1  # Sell signal
        
    def MACD(self):
        if self.ema_fast > self.ema_slow and self.macd > self.signal_line:
            return 1  # Buy signal
        else:
            return -1 # Sell signal
        
    def ADX(self):
        if self.adx > 20 and self.plus_di > self.minus_di:
            return 1  # Buy signal
        elif self.adx > 20 and self.minus_di > self.plus_di:
            return -1  # Sell signal
        else:       
            return 0

    def BollingerBand(self):
        if self.close_price < self.lower_band:
            return 1  # Oversold
        elif self.close_price > self.upper_band:
            return -1  # Overbought
        elif self.close_price > self.bb_sma:
            return 0.5  # Mild bullish trend
        elif self.close_price < self.bb_sma:
            return -0.5  # Mild bearish trend
        else:
            return 0
        
    def Kijun(self):
        if self.close_price > self.kijun:
            return 1
        elif self.close_price < self.kijun:
            return -1
        else:
            return 0
        
    def OBV(self):
        if self.obv > self.obv_prev:
            return 1
        else:
            return -1
        
    def RSI(self):
        if self.rsi > 60:
            return 1
        elif self.rsi < 40:
            return -1
        else:
            return 0
    
    def PivotPoint(self):
        if self.close_price > self.r3:
            return 2
        elif self.r2 < self.close_price <= self.r3:
            return 1.5
        elif self.r1 < self.close_price <= self.r2:
            return 1
        elif self.pivot < self.close_price <= self.r1:
            return 0.5
        
        elif self.s1 <= self.close_price < self.pivot:
            return -0.5
        elif self.s2 <= self.close_price < self.s1:
            return -1
        elif self.s3 <= self.close_price < self.s2:
            return -1.5
        elif self.close_price < self.s3:
            return -2 
        return 0 

