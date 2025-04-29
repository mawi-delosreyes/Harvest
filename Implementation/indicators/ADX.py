class ATR:
    def __init__(self, highs, lows, closes, period, prev_atr):
        self.highs = highs
        self.lows = lows
        self.closes = closes
        self.period = period
        self.prev_atr = prev_atr 


    def calculate(self):
        if len(self.highs) < 2:
            print("Not enough data to compute ATR")
            return None

        # Compute latest True Range for only the last data
        hl = self.highs[-1] - self.lows[-1]
        hc = abs(self.highs[-1] - self.closes[-2])
        lc = abs(self.lows[-1] - self.closes[-2])
        tr = max(hl, hc, lc)

        # Wilder's smoothing
        atr = ((self.prev_atr * (self.period - 1)) + tr) / self.period
        return atr


class ADX:
    def __init__(self, highs, lows, closes, period, prev_atr, prev_plus_dm14, prev_minus_dm14, prev_adx):
        self.highs = highs
        self.lows = lows
        self.closes = closes
        self.period = period
        self.prev_atr = prev_atr
        self.prev_plus_dm14 = prev_plus_dm14
        self.prev_minus_dm14 = prev_minus_dm14
        self.prev_adx = prev_adx


    def calculate(self):
        if len(self.highs) < 2:
            print("Not enough data to compute ADX")
            return None, None, None, None

        # Get latest ATR
        atr = ATR(self.highs, self.lows, self.closes, self.period, self.prev_atr).calculate()
        if atr is None or atr == 0:
            return None, None, None, None

        # Compute latest directional movements
        up_move = self.highs[-1] - self.highs[-2]
        down_move = self.lows[-2] - self.lows[-1]

        plus_dm = up_move if up_move > down_move and up_move > 0 else 0
        minus_dm = down_move if down_move > up_move and down_move > 0 else 0

        # Wilder's smoothing
        plus_dm14 = self.prev_plus_dm14 - (self.prev_plus_dm14 / self.period) + plus_dm
        minus_dm14 = self.prev_minus_dm14 - (self.prev_minus_dm14 / self.period) + minus_dm

        plus_di = 100 * (plus_dm14 / atr)
        minus_di = 100 * (minus_dm14 / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = ((self.prev_adx * (self.period - 1)) + dx) / self.period

        return adx, atr, plus_dm14, minus_dm14
