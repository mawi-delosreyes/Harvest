import sys
from Logging.Logger import Logger

class SMA:
    def __init__(self, crypto, close_data, fast, slow):
        self.close_data = close_data
        self.fast = fast
        self.slow = slow
        self.result = None
        self.logger = Logger(crypto)
        self.crypto = crypto


    def computeSMA(self):

        if len(self.close_data) < self.slow:
            self.logger.info("Not enough data to compute fast and slow SMA")
            sys.exit(0)
        
        fast_sma = sum(self.close_data[-self.fast:]) / self.fast
        slow_sma = sum(self.close_data[-self.slow:]) / self.slow
        self.result = (fast_sma, slow_sma)
