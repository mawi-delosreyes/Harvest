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
        self.entry_threshold = 7.5
        self.buy_score = None
        self.verdict = None
        self.logger = Logger(crypto)
    

    def Indicators(self, crypto, interval):
        indicator = Indicators(crypto)
        self.sma, self.macd, self.adx, self.kijun, self.obv, self.rsi, self.fib, self.close_price, self.sma_trend, self.candle_body = indicator.runIndicators(interval)
        

    def Strategy(self, crypto, cooldown, interval, hold, tp, be, sl):

        self.Indicators(crypto, interval)
        score = Scores(self.crypto, self.sma, self.macd, self.adx, self.kijun, self.obv, self.rsi, self.fib, self.close_price, self.candle_body)
        self.buy_score, indicators, model_prob = score.ComputeScores()

        if model_prob > 0.8: self.buy_score += 0.5

        if self.adx[0] > 30:  # strong trend
            self.entry_threshold = 7.0
        elif self.adx[0] < 15:  # weak trend
            self.entry_threshold = 8.0

        crypto_data = DataRetrieval(crypto, crypto + "PHP").getPrice(True, "1m")
        crypto_price = float(crypto_data[4])
        self.logger.info(f"Score: {self.buy_score}, Indicators: {indicators}, Model Probability: {model_prob}")

        # Entry logic
        if not hold and cooldown == 0:
            if self.buy_score >= self.entry_threshold and crypto_price < self.sma_trend and model_prob > 0.5:
                self.verdict = "buy"

        # Exit logic
        if hold:
            exit_score = 0
            if self.sma[0] < self.sma[1]: exit_score += 1
            if self.macd[2] < self.macd[3]: exit_score += 1
            if self.rsi > 70: exit_score += 1
            if model_prob < 0.4: exit_score += 1 

            # TP
            if self.close_price >= tp:
                self.verdict = "take profit"

            # SL  
            elif self.close_price <= sl:
                self.verdict = "stop loss"

            # Early Exit
            elif exit_score >= 3:
                self.verdict = "exit"
