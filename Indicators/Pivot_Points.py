import sys
from Logging.Logger import Logger

class PivotPoints:
    def __init__(self, crypto, high, low, close):
        self.crypto = crypto
        self.high = high
        self.low = low
        self.close = close
        self.logger = Logger(crypto)
        self.result = None


    def computePivotPoint(self):
        pivot = (self.high + self.low + self.close) / 3
        r1 = (2 * pivot) - self.low
        s1 = (2 * pivot) - self.high
        r2 = pivot + (self.high - self.low)
        s2 = pivot - (self.high - self.low)
        r3 = self.high + (2 * (pivot - self.low))
        s3 = self.low - (2 * (self.high - pivot))

        self.result = (pivot, r1, s1, r2, s2, r3, s3)
