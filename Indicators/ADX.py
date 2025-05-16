import sys
from Logging.Logger import Logger

class ATR:
    def __init__(self, crypto, high, low, close, period):
        self.high = high
        self.low = low
        self.close = close
        self.period = period
        self.logger = Logger(crypto)


    def computeATR(self):
        if len(self.high) < self.period + 1:
            self.logger.info("Not enough data to compute ATR")
            sys.exit(0)

        tr_values = []
        for i in range(1, len(self.high)):
            hl = self.high[i] - self.low[i]
            hc = abs(self.high[i] - self.close[i - 1])
            lc = abs(self.low[i] - self.close[i - 1])
            tr_values.append(max(hl, hc, lc))

        first_atr = sum(tr_values[:self.period]) / self.period
        atr_values = [first_atr]
        for tr in tr_values[self.period:]:
            prev_atr = atr_values[-1]
            atr = ((prev_atr * (self.period - 1)) + tr) / self.period
            atr_values.append(atr)

        return atr_values


class ADX:
    def __init__(self, crypto, high, low, close, period):
        self.high = high
        self.low = low
        self.close = close
        self.period = period
        self.result = None
        self.logger = Logger(crypto)
        self.crypto = crypto
        

    def smooth(self, values, period):
        first_avg = sum(values[:period]) / period
        smoothed = [first_avg]
        for val in values[period:]:
            prev = smoothed[-1]
            new_val = ((prev * (period - 1)) + val) / period
            smoothed.append(new_val)
        return smoothed


    def computeADX(self):
        if len(self.high) < self.period * 2:
            self.logger.info("Not enough data to compute ADX")
            sys.exit(0)

        atr = ATR(self.crypto, self.high, self.low, self.close, self.period).computeATR()
        if atr is None or atr == 0:
            self.logger.info("No ATR value")
            sys.exit(0)

        plus_dm_list = []
        minus_dm_list = []

        for i in range(1, len(self.high)):
            up_move = self.high[i] - self.high[i - 1]
            down_move = self.low[i - 1] - self.low[i]

            plus_dm = up_move if (up_move > down_move and up_move > 0) else 0
            minus_dm = down_move if (down_move > up_move and down_move > 0) else 0

            plus_dm_list.append(plus_dm)
            minus_dm_list.append(minus_dm)


        smoothed_plus_dm = self.smooth(plus_dm_list, self.period)
        smoothed_minus_dm = self.smooth(minus_dm_list, self.period)
        aligned_atr = atr[-len(smoothed_plus_dm):]

        plus_di = [100 * (p / t) if t != 0 else 0 for p, t in zip(smoothed_plus_dm, aligned_atr)]
        minus_di = [100 * (m / t) if t != 0 else 0 for m, t in zip(smoothed_minus_dm, aligned_atr)]

        dx_list = []
        for pdi, mdi in zip(plus_di, minus_di):
            denom = pdi + mdi
            dx = 100 * abs(pdi - mdi) / denom if denom != 0 else 0
            dx_list.append(dx)

        first_adx = sum(dx_list[:self.period]) / self.period
        adx_values = [first_adx]
        for dx in dx_list[self.period:]:
            prev_adx = adx_values[-1]
            adx = ((prev_adx * (self.period - 1)) + dx) / self.period
            adx_values.append(adx)

        self.result = (adx_values[-1], atr[-1], plus_di[-1], minus_di[-1])
