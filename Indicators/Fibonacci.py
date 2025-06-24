import sys
from decimal import Decimal
from Logging.Logger import Logger

class Fibonacci:
    def __init__(self, crypto, high_data, low_data, lookback=20):
        self.crypto = crypto
        self.high_data = high_data
        self.low_data = low_data
        self.lookback = lookback
        self.levels = None
        self.logger = Logger(crypto)

    def computeFibonacci(self):
        if len(self.high_data) < self.lookback or len(self.low_data) < self.lookback:
            self.logger.info("Not enough data to compute Fibonacci levels")
            sys.exit(0)

        recent_high = max(self.high_data[-self.lookback:])
        recent_low = min(self.low_data[-self.lookback:])

        if recent_high == recent_low:
            self.logger.info("Swing high and low are equal — skipping Fibonacci calculation")
            self.levels = None
            return

        diff = recent_high - recent_low

        self.levels = {
            "0.0": recent_high,
            "0.236": recent_high - Decimal(0.236) * diff,
            "0.382": recent_high - Decimal(0.382) * diff,
            "0.5": recent_high - Decimal(0.5) * diff,
            "0.618": recent_high - Decimal(0.618) * diff,
            "0.786": recent_high - Decimal(0.786) * diff,
            "1.0": recent_low
        }
