import sys
from Logging.Logger import Logger

class RSI:
    def __init__(self, crypto, close_data, period):
        self.close_data = close_data
        self.period = period
        self.result = None
        self.logger = Logger(crypto)

    
    def computeRSI(self):
        if len(self.close_data) < self.period:
            self.logger.error("Not enough data to calculate RSI")
            sys.exit(0)

        gains = []
        losses = []

        for i in range(-self.period, 0):
            delta = self.close_data[i] - self.close_data[i - 1]
            if delta > 0:
                gains.append(delta)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(-delta)

        avg_gain = sum(gains) / self.period
        avg_loss = sum(losses) / self.period

        if avg_loss == 0:
            self.result = 100
        else:
            rs = avg_gain / avg_loss
            self.result = 100 - (100 / (1 + rs))
