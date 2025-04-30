import requests
import csv
import os
import sys

sys.path.append(os.path.abspath('../../Implementation/indicators'))
from SMA import SMA
from MACD import MACD
from ADX import ADX, ATR

class main:
    def __init__(self):
        self.baseURL = "http://127.0.0.1:8000"
        self.marketDataPath = "/api/getMockData"
        self.database = "../MockDataAPI/sampleData/XRPUSDT.csv"
        self.data = None
        self.numRowsDay = 190

    def retrieveData(self, timestamp):
        params = {"timestamp": timestamp}  

        current_data = requests.get(url=(self.baseURL + self.marketDataPath), params=params)
        
        column_names = ["timestamp", "open", "high", "low", "close", "volume"]
        self.latest_data = current_data.json()
        
        with open(self.database, 'a', newline='') as database:
            dictwriter = csv.DictWriter(database, fieldnames=column_names)
            dictwriter.writerow(self.latest_data)


    def readLastRow(self):
        with open(self.database, 'rb') as database:
            database.seek(-2, 2)  
            while database.read(1) != b'\n':
                database.seek(-2, 1)
            last_data = database.readline().decode().strip().split(',')
        return last_data[0]
    

    def readData(self):
        self.data = []
        with open(self.database, 'r') as f:
            reader = list(csv.DictReader(f))
        self.data = [float(row['close']) for row in reader[-self.numRowsDay:]]



    def getIndicators(self, fast, slow):
        sma = SMA(self.data, fast, slow)
        fast_sma, slow_sma = sma.computeSMA()



if __name__ == '__main__':

    
    sma_fast = 10
    sma_slow = 30

    strategy = main()
    last_timestamp = strategy.readLastRow()
    #strategy.retrieveData(last_timestamp)
    strategy.readData()
    strategy.getIndicators(sma_fast, sma_slow)