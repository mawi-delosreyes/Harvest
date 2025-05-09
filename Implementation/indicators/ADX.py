class ATR:
    def __init__(self, high, low, close, period, prev_atr):
        self.high = high
        self.low = low
        self.close = close
        self.period = period
        self.prev_atr = prev_atr 


    def computeATR(self):
        if len(self.high) < 2:
            print("Not enough data to compute ATR")
            return None

        # Compute latest True Range for only the last data
        if self.prev_atr is not None:
            hl = self.high[-1] - self.low[-1]
            hc = abs(self.high[-1] - self.close[-2])
            lc = abs(self.low[-1] - self.close[-2])
            tr = max(hl, hc, lc)
            atr = ((self.prev_atr * (self.period - 1)) + tr) / self.period
        else:
            tr_values = []
            for i in range(self.period):
                hl = self.high[-(self.period-i)] - self.low[-(self.period-i)]
                hc = abs(self.high[-(self.period-i)] - self.close[-(self.period-i)])
                lc = abs(self.low[-(self.period-i)] - self.close[-(self.period-i)])
                tr_values.append(max(hl, hc, lc))

            atr = sum(tr_values) / self.period

        return atr


class ADX:
    def __init__(self, high, low, close, period, prev_atr, prev_plus_dm14, prev_minus_dm14, prev_adx):
        self.high = high
        self.low = low
        self.close = close
        self.period = period
        self.prev_atr = prev_atr
        self.prev_plus_dm14 = prev_plus_dm14
        self.prev_minus_dm14 = prev_minus_dm14
        self.prev_adx = prev_adx

    def computeADX(self):
        if len(self.high) < self.period + 1:
            print("Not enough data to compute ADX")
            return None, None, None, None

        atr = ATR(self.high, self.low, self.close, self.period, self.prev_atr).computeATR()
        if atr is None or atr == 0:
            return None, None, None, None

        # Compute current +DM and -DM
        up_move = self.high[-1] - self.high[-2]
        down_move = self.low[-2] - self.low[-1]

        plus_dm = up_move if up_move > down_move and up_move > 0 else 0
        minus_dm = down_move if down_move > up_move and down_move > 0 else 0

        # Check if we're calculating for the first time (no previous smoothed DM values)
        if self.prev_plus_dm14 is None or self.prev_minus_dm14 is None:
            plus_dm_list = []
            minus_dm_list = []
            for i in range(1, self.period + 1):
                up_move_i = self.high[-i] - self.high[-i - 1]
                down_move_i = self.low[-i - 1] - self.low[-i]

                plus_dm_list.append(up_move_i if up_move_i > down_move_i and up_move_i > 0 else 0)
                minus_dm_list.append(down_move_i if down_move_i > up_move_i and down_move_i > 0 else 0)

            plus_dm14 = sum(plus_dm_list)
            minus_dm14 = sum(minus_dm_list)

            plus_di = 100 * (plus_dm14 / atr)
            minus_di = 100 * (minus_dm14 / atr)
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) != 0 else 0
            adx = dx  
        else:
            # Use Wilder's smoothing for +DM14 and -DM14
            plus_dm14 = self.prev_plus_dm14 - (self.prev_plus_dm14 / self.period) + plus_dm
            minus_dm14 = self.prev_minus_dm14 - (self.prev_minus_dm14 / self.period) + minus_dm
        
            plus_di = 100 * (plus_dm14 / atr)
            minus_di = 100 * (minus_dm14 / atr)
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = ((self.prev_adx * (self.period - 1)) + dx) / self.period

        return adx, atr, plus_dm14, minus_dm14




'''
class ADX:
    def __init__(self, high, low, close, period, prev_atr, prev_plus_dm14, prev_minus_dm14, prev_adx):
        self.high = high
        self.low = low
        self.close = close
        self.period = period
        self.prev_atr = prev_atr
        self.prev_plus_dm14 = prev_plus_dm14
        self.prev_minus_dm14 = prev_minus_dm14
        self.prev_adx = prev_adx


    def computeADX(self):
        if len(self.high) < self.period:
            print("Not enough data to compute ADX")
            return None, None, None, None

        # Get latest ATR
        atr = ATR(self.high, self.low, self.close, self.period, self.prev_atr).computeATR()
        if atr is None or atr == 0:
            return None, None, None, None

        # Compute latest directional movements
        up_move = self.high[-1] - self.high[-2]
        down_move = self.low[-2] - self.low[-1]

        plus_dm = up_move if up_move > down_move and up_move > 0 else 0
        minus_dm = down_move if down_move > up_move and down_move > 0 else 0

        # Wilder's smoothing
        if self.prev_plus_dm14 is not None and self.prev_minus_dm14 is not None:
            plus_dm14 = self.prev_plus_dm14 - (self.prev_plus_dm14 / self.period) + plus_dm
            minus_dm14 = self.prev_minus_dm14 - (self.prev_minus_dm14 / self.period) + minus_dm
        else:
            plus_dm = []
            minus_dm = []

            for i in range(1, len(self.high)):
                # +DM is the difference between the current high and the previous high if greater than the current low and previous low difference
                plus_dm.append(max(0, self.high[i] - self.high[i-1]) if self.high[i] - self.high[i-1] > self.low[i-1] - self.low[i] else 0)
                # -DM is the difference between the current low and the previous low if greater than the current high and previous high difference
                minus_dm.append(max(0, self.low[i-1] - self.low[i]) if self.low[i-1] - self.low[i] > self.high[i] - self.high[i-1] else 0)



        plus_di = 100 * (plus_dm14 / atr)
        minus_di = 100 * (minus_dm14 / atr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = ((self.prev_adx * (self.period - 1)) + dx) / self.period

        return adx, atr, plus_dm14, minus_dm14
'''