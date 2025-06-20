class Signals:

    def __init__(self, sma_short, sma_mid, sma_long, ema_fast, ema_slow, macd, signal_line,
                 plus_di, minus_di, adx, upper_band, bb_sma, lower_band,
                 kijun, obv, obv_prev, pivot, r1, s1, r2, s2, r3, s3, rsi, close_price):
        self.sma_short = sma_short
        self.sma_mid = sma_mid
        self.sma_long = sma_long
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
        if self.sma_short > self.sma_mid > self.sma_long:
            # Reward greater separation
            strength = min(2, (self.sma_short - self.sma_mid) / self.sma_mid + (self.sma_mid - self.sma_long) / self.sma_long)
            return float(round(1 + strength, 2))
        elif self.sma_short < self.sma_mid < self.sma_long:
            strength = min(2, (self.sma_mid - self.sma_short) / self.sma_short + (self.sma_long - self.sma_mid) / self.sma_mid)
            return float(round(-1 - strength, 2))
        return 0


    def MACD(self):
        macd_hist = self.macd - self.signal_line
        if self.macd > self.signal_line and self.ema_fast > self.ema_slow:
            return float(round(min(3, 1 + abs(macd_hist) * 10), 2))
        elif self.macd < self.signal_line and self.ema_fast < self.ema_slow:
            return float(round(max(-3, -1 - abs(macd_hist) * 10), 2))
        return 0

        
    def ADX(self):
        if self.adx > 20:
            strength = min(2, (self.adx - 20) / 20)
            if self.plus_di > self.minus_di:
                return float(round(1 + strength, 2))
            elif self.minus_di > self.plus_di:
                return float(round(-1 - strength, 2))
        return 0


    def BollingerBand(self):
        if self.close_price < self.lower_band:
            return float(round(min(2, (self.lower_band - self.close_price) / self.lower_band), 2))
        elif self.close_price > self.upper_band:
            return float(round(max(-2, (self.upper_band - self.close_price) / self.upper_band), 2))
        elif self.close_price > self.bb_sma:
            return 0.5
        elif self.close_price < self.bb_sma:
            return -0.5
        return 0

        
    def Kijun(self):
        diff = (self.close_price - self.kijun) / self.kijun
        if diff > 0:
            return float(round(min(2, diff * 5), 2))
        elif diff < 0:
            return float(round(max(-2, diff * 5), 2))
        return 0

        
    def OBV(self):
        _, obv_slope = self.obv, self.obv_prev  # Actually slope now
        if obv_slope > 0:
            return float(round(min(2, obv_slope * 10), 2))  # reward upward trend
        elif obv_slope < 0:
            return float(round(max(-2, obv_slope * 10), 2))  # penalize downward trend
        return 0

        
    def RSI(self):
        if self.rsi > 70:
            return -1.5
        elif self.rsi > 60:
            return 1
        elif self.rsi < 30:
            return 1.5
        elif self.rsi < 40:
            return -1
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