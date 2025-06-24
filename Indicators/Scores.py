import joblib

class Scores:
    def __init__(self, crypto, sma, macd,
                 adx, kijun, obv, rsi, fib, close_price, candle_body):
        self.crypto = crypto
        self.sma_short = sma[0]
        self.sma_long = sma[1]
        self.macd = macd[2]
        self.signal_line = macd[3]
        self.adx = adx
        self.kijun = kijun
        self.obv = obv
        self.rsi = rsi
        self.fib = fib
        self.close_price = close_price
        self.candle_body = candle_body
        self.model_prob = None
        self.score = 0
        self.indicators = []
        self.weights = {
            'sma': 1.5,
            'rsi': 1.0,
            'macd': 2.0,
            'fib': 1.5,
            'adx': 2.0,
            'kijun': 1.5,
            'obv': 1.0,
            'model': 3.5
        }


    def SMA(self):
        if self.sma_short > self.sma_long:
            self.score += self.weights['sma']
            self.indicators.append("SMA")


    def MACD(self):
        if self.macd > self.signal_line:
            self.score += self.weights['macd']
            self.indicators.append("MACD")


    def ADX(self):
        if self.adx and self.adx[0] > 25:
            self.score += self.weights['adx']
            self.indicators.append("ADX")


    def Kijun(self):
        if self.kijun:
            if self.close_price > self.kijun:
                self.score += self.weights['kijun']
                self.indicators.append("Kijun")
            
            if isinstance(self.kijun, list) and len(self.kijun) >= 3:
                if self.kijun[-1] > self.kijun[-2] > self.kijun[-3]:
                    self.score += self.weights['kijun']
                    self.indicators.append("Kijun+")


    def OBV(self):
        if self.obv:
            self.score += self.weights['obv']
            self.indicators.append("OBV")
        

    def RSI(self):
        if self.rsi < 35:
            self.score += self.weights['rsi']
            self.indicators.append("RSI")

    
    def Fibonacci(self):
        # if self.fib and self.fib['0.382'] and self.fib['0.236'] and self.fib['0.236'] < self.close_price < self.fib['0.382']:
        if self.fib and self.fib.get('0.5') and self.fib.get('0.382') and self.fib['0.382'] < self.close_price < self.fib['0.5']:
            self.score += self.weights['fib']
            self.indicators.append("FIB")

    
    def ClassificationModel(self):
                
        if self.crypto == "BTC":
            model = joblib.load("Models/btc_classification_model.pkl")

        sma_slope = self.sma_short - self.sma_long
        macd_diff = self.macd - self.signal_line
        model_input = [[sma_slope, self.rsi, macd_diff, self.candle_body]]
        self.model_prob = model.predict_proba(model_input)[0][1]

        if self.model_prob > 0.75:
            self.score += self.weights['model']
            self.indicators.append(f"MODEL({self.model_prob:.2f})")


    def ComputeScores(self):
        self.SMA(),
        self.MACD(),
        self.ADX(),
        self.Kijun(),
        self.OBV(),
        self.RSI(),
        self.Fibonacci()
        self.ClassificationModel()

        return self.score, self.indicators, self.model_prob