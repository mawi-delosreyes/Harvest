import math
from decimal import Decimal
from Logging.Logger import Logger

class BoillingerBands:
    def __init__(self, crypto, close_data, period, std_dev):
        self.close_data = close_data
        self.period = period
        self.std_dev = std_dev
        self.result = None
        self.logger = Logger(crypto)


    def computeBollingerBands(self):
        if len(self.close_data) < self.period:
            self.logger.error("Not enough data points to calculate Bollinger Bands")

        data = self.close_data[-self.period:]
        sma = sum(data) / self.period
        variance = sum((p - sma) ** 2 for p in data) / self.period
        std_dev = math.sqrt(variance)

        upper_band = sma + Decimal(self.std_dev * std_dev)
        lower_band = sma - Decimal(self.std_dev * std_dev)

        self.result = (upper_band, sma, lower_band)



