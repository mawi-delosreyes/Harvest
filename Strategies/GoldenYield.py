from decimal import Decimal, ROUND_HALF_UP
from Database.Database import Database
from Database.DataRetrieval import DataRetrieval
from Indicators.GY_Invicators import Indicators
from Indicators.Scores import Scores
from Indicators.Momentum_Indicators import Indicators
from Logging.Logger import Logger
from Coins.constants import host
from Indicators.GY_Invicators import Indicators
from datetime import datetime, timedelta


class GoldenYield:

    def __init__(self, crypto):
        self.interval = "1m"
        self.crypto = crypto
        self.sma = None
        self.macd = None
        self.adx = None
        self.kijun = None
        self.obv = None
        self.rsi = None
        self.fib = None
        self.close_price = None
        self.sma_trend = None
        self.macd_diff = None
        self.candle_body = None
        self.entry_threshold = 8.5
        self.score = None
        self.verdict = None
        self.logger = Logger(crypto)
    

    def Indicators(self, crypto, interval):
        indicator = Indicators(crypto)
        self.sma, self.macd, self.adx, self.kijun, self.obv, self.rsi, self.fib, self.close_price, self.sma_trend, self.candle_body = indicator.runIndicators(interval)
        

    def Strategy(self, crypto, cooldown, interval, hold, tp, sl):

        self.Indicators(crypto, interval)
        score = Scores(self.crypto, self.sma, self.macd, self.adx, self.kijun, self.obv, self.rsi, self.fib, self.close_price, self.candle_body)
        self.score, indicators, model_prob = score.ComputeScores()

        self.logger.info(f"Score: {self.score}, Indicators: {indicators}, Model Probability: {model_prob}")
        
        crypto_data = DataRetrieval(crypto, crypto + "PHP").getPrice(True, "1m")
        crypto_price = float(crypto_data[4])

        # Entry logic
        if not hold and cooldown == 0:
            if score >= self.entry_threshold and crypto_price < self.sma_trend and model_prob > 0.5:
                self.verdict = "buy"

        # Exit logic
        if hold:
            if crypto_price >= tp:
                self.verdict = "take profit"
            elif crypto_price <= sl:
                self.verdict = "stop loss"
            else:
                exit_score = 0
                if self.sma[0] < self.sma[1]: exit_score += 1
                if self.macd[2] < self.macd[3]: exit_score += 1
                if self.rsi > 70: exit_score += 1
                if model_prob < 0.4: exit_score += 1   

                if exit_score >= 3: self.verdict = "exit"
