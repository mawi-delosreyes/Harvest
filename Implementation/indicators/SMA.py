class SMA:
    def __init__(self, data, fast, slow):
        self.data = data
        self.fast = fast
        self.slow = slow


    def computeSMA(self):
        if len(self.data) < self.slow:
            print("Not enough data to compute fast and slow SMA")
            return None, None
        
        fast_sma = sum(self.data[-self.fast:]) / self.fast
        slow_sma = sum(self.data[-self.slow:]) / self.slow

        return fast_sma, slow_sma