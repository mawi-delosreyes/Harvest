import sys
from Logging.Logger import Logger

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


        obv_values = [0]
        for i in range(1, len(self.close_data)):
            if self.close_data[i] > self.close_data[i - 1]:
                obv_values.append(obv_values[-1] + self.volume_data[i])
            elif self.close_data[i] < self.close_data[i - 1]:
                obv_values.append(obv_values[-1] - self.volume_data[i])
            else:
                obv_values.append(obv_values[-1])
        self.result = (obv_values[-1], obv_values[-2])