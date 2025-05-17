import sys
from Logging.Logger import Logger

class KijunSen:
    def __init__(self, crypto, high_data, low_data, period):
        self.crypto = crypto
        self.high_data = high_data
        self.low_data = low_data
        self.period = period
        self.result = None
        self.logger = Logger(crypto)


    def computeKijunSen(self):

        if len(self.high_data) != len(self.low_data):
            self.logger.error("Number of high and low data points are not the same")
            sys.exit(0)
            
        if len(self.high_data) < self.period or len(self.low_data) < self.period:
            self.logger.error("Not enough data points to calculate Kijun Sen")
            sys.exit(0)

        highest = max(self.high_data[-self.period:])
        lowest = min(self.low_data[-self.period:])
        self.result = (highest + lowest) / 2
