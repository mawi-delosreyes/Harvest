class SMA:
    def __init__(self, close_data, fast, slow):
        self.close_data = close_data
        self.fast = fast
        self.slow = slow


    def computeSMA(self):

        if len(self.close_data) < self.slow:
            print("Not enough data to compute fast and slow SMA")
            return None, None
        
        fast_sma = sum(self.close_data[-self.fast:]) / self.fast
        slow_sma = sum(self.close_data[-self.slow:]) / self.slow
        return fast_sma, slow_sma
