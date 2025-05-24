import sys
from Logging.Logger import Logger

class SMA:
    def __init__(self, crypto, close_data, short, mid, long):
        self.close_data = close_data
        self.short = short
        self.mid = mid
        self.long = long
        self.result = None
        self.logger = Logger(crypto)
        self.crypto = crypto


    def computeSMA(self):

        if len(self.close_data) < self.long:
            self.logger.info("Not enough data to compute fast and slow SMA")
            sys.exit(0)
        
        short_sma = sum(self.close_data[-self.short:]) / self.short
        mid_sma = sum(self.close_data[-self.mid:]) / self.mid
        long_sma = sum(self.close_data[-self.long:]) / self.long
        self.result = (short_sma, mid_sma, long_sma)
