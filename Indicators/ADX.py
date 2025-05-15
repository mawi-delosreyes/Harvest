class ATR:
    def __init__(self, high, low, close, period):
        self.high = high
        self.low = low
        self.close = close
        self.period = period


    def computeATR(self):
        if len(self.high) < self.period + 1:
            print("Not enough data to compute ATR")
            return None

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
        self.result = None

    def computeADX(self):
        if len(self.high) < self.period + 1:
            print("Not enough data to compute ADX")
            return None, None, None, None

        atr = ATR(self.high, self.low, self.close, self.period).computeATR()
        if atr is None or atr == 0:
            return None, None, None, None

        plus_dm_list = []
        minus_dm_list = []
        for i in range(1, self.period + 1):
            up_move = self.high[-i] - self.high[-i - 1]
            down_move = self.low[-i - 1] - self.low[-i]

            plus_dm = up_move if up_move > down_move and up_move > 0 else 0
            minus_dm = down_move if down_move > up_move and down_move > 0 else 0

            plus_dm_list.append(plus_dm)
            minus_dm_list.append(minus_dm)

        plus_dm14 = sum(plus_dm_list)
        minus_dm14 = sum(minus_dm_list)

        plus_di = 100 * (plus_dm14 / atr)
        minus_di = 100 * (minus_dm14 / atr)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) != 0 else 0
        adx = dx  

        self.result = (adx, atr, plus_di, minus_di)
