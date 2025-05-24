import sys
import numpy as np
from Logging.Logger import Logger
from decimal import Decimal

class OBV:
    def __init__(self, crypto, close_data, volume_data):
        self. crypto = crypto
        self.logger = Logger(crypto)
        self.close_data = close_data[-5:]
        self.volume_data = volume_data[-5:]
        self.result = None

    
    def computeOBV(self):
        if len(self.close_data) != len(self.volume_data):
            self.logger.info("Close and volume data are not the same length")
            sys.exit(0)    

        obv_values = [float(v) for v in self.close_data]
        x = np.arange(len(obv_values))
        y = np.array(obv_values)

        # Now fit the slope
        slope, _ = np.polyfit(x, y, 1)

        self.result = (obv_values[-1], slope)