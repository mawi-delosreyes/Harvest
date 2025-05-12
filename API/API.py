import requests

class RetrieveAPIData:
    def __init__(self):
        self.baseURL = "http://127.0.0.1:8000"
        self.marketDataPath = "/api/getMockData"
        self.executeTradePath = "/api/postMockTradeExecution/"
        self.mockTradeInfoPath = "/api/getMockTradeInfo"

    def retrieveAPIData(self, timestamp):
        params = {"timestamp": timestamp}  

        current_data = requests.get(url=(self.baseURL + self.marketDataPath), params=params)
        latest_data = current_data.json()
        return latest_data

    def executeTrade(self, signal, trade_amount, entry_price):
        payload = {
            "signal": signal,
            "trade_amount": trade_amount,
            "entry_price": entry_price,
        }

        response = requests.post(url=(self.baseURL + self.executeTradePath), json=payload)
        trade_data = response.json()
        return trade_data
    
    def tradeInfo(self, signal, trade_amount, entry_price, current_price):
        params = {
            "signal": signal,
            "trade_amount": trade_amount,
            "entry_price": entry_price,
            "current_price": current_price
        }

        print(params)
        response = requests.get(url=(self.baseURL + self.mockTradeInfoPath), params=params)
        trade_info = response.json()
        return trade_info



