import joblib
import threading
import numpy as np
import warnings
from Database.Database import Database
from decimal import Decimal
from .GY_Invicators_Simulation import Indicators
from Indicators.Scores import Scores

warnings.filterwarnings('ignore')

class GYSimulation:
    def __init__(self, crypto, capital=100.0):
        self.crypto = crypto
        self.model = joblib.load("Models/btc_classification_model.pkl")
        self.initial_capital = capital
        self.capital = capital
        self.entry_threshold = 8.5

    def retrieveDatabaseData(self):
        col_names = "crypto.open, crypto.high, crypto.low, crypto.close, crypto.volume"
        query = f"SELECT {col_names} FROM {self.crypto}_1 AS crypto ORDER BY crypto.id ASC"
        return Database(self.crypto).retrieveData(query)

    def executeBuySignal(self, price):
        risk = Decimal("0.004")
        reward = Decimal("0.006")
        fees = Decimal("0.006")

        break_even = price * (1 + fees)
        take_profit = break_even * (1 + reward)
        stop_loss = price * (1 - risk)

        return take_profit, stop_loss, break_even

    def runSimulation(self, interval="1m"):
        success = fail = trades = 0
        gross_profit = gross_loss = float("0")
        max_periods = 60

        data = self.retrieveDatabaseData()
        window = data[:max_periods]

        crypto_holdings = {
            self.crypto: {
                'hold': 0,
                'tp': 0,
                'sl': 0,
                'be': 0,
                'entry_price': 0,
                'cooldown': 0
            }
        }

        for i in range(max_periods, len(data)):   
            btc_indicators = Indicators("BTC", window)
            sma, macd, adx, kijun, obv, rsi, fib, close_price, sma_trend, candle_body = btc_indicators.runIndicators(interval)
            score = Scores(self.crypto, sma, macd, adx, kijun, obv, rsi, fib, close_price, candle_body)
            score, indicators, model_prob = score.ComputeScores()

            if crypto_holdings[self.crypto]['cooldown'] > 0:
                crypto_holdings[self.crypto]['cooldown'] -= 1

            # Entry
            if not crypto_holdings[self.crypto]['hold'] and crypto_holdings[self.crypto]['cooldown'] == 0:
                if score >= self.entry_threshold and close_price < sma_trend and model_prob > 0.5:
                    # print(f"| BUY @ {close_price:.2f} | Score: {score:.1f} | Conditions: {indicators}")

                    tp, sl, be = self.executeBuySignal(close_price)
                    crypto_holdings[self.crypto].update({
                        'hold': 1,
                        'tp': tp,
                        'sl': sl,
                        'be': be,
                        'entry_price': close_price,
                        'cooldown': 0
                    })
                    trades += 1
            
            # Exit
            if crypto_holdings[self.crypto]['hold']:
                if close_price >= crypto_holdings[self.crypto]['tp']:
                    gain = float(crypto_holdings[self.crypto]['tp'] - crypto_holdings[self.crypto]['entry_price'])
                    self.capital += gain
                    gross_profit += gain
                    success += 1
                    crypto_holdings[self.crypto]['hold'] = 0
                    crypto_holdings[self.crypto]['cooldown'] = 10
                    # print(f"| TP hit @ {close_price:.2f}")

                elif close_price <= crypto_holdings[self.crypto]['sl']:
                    loss = float(crypto_holdings[self.crypto]['entry_price'] - crypto_holdings[self.crypto]['sl'])
                    self.capital -= loss
                    gross_loss += loss
                    fail += 1
                    crypto_holdings[self.crypto]['hold'] = 0
                    crypto_holdings[self.crypto]['cooldown'] = 15
                    # print(f"| SL hit @ {close_price:.2f}")

                else:
                    exit_score = 0
                    if sma[0] < sma[1]: exit_score += 1
                    if macd[2] < macd[3]: exit_score += 1
                    if rsi > 70: exit_score += 1
                    if model_prob < 0.4: exit_score += 1

                    if exit_score >= 3:
                        gain_or_loss = close_price - crypto_holdings[self.crypto]['entry_price']
                        self.capital += float(gain_or_loss)
                        if gain_or_loss > 0:
                            gross_profit += float(gain_or_loss)
                            success += 1
                        else:
                            gross_loss += float(-gain_or_loss)
                            fail += 1
                        crypto_holdings[self.crypto]['hold'] = 0
                        crypto_holdings[self.crypto]['cooldown'] = 10 
                        # print(f"| Early exit @ {close_price:.2f} | Score: {exit_score}")

            window.pop(0)
            window.append(data[i])

        net_gain = self.capital - self.initial_capital
        avg_gain = net_gain / trades if trades else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else Decimal('inf')

        print("\n--- Summary ---")
        print(f"TP: {success}, SL: {fail}, Trades: {trades}")
        print(f"Success Rate: {(success / trades):.2%}" if trades else "No trades executed.")
        print(f"Profit Factor: {profit_factor:.2f}")
        print(f"Net Capital: {self.capital:.2f}")
        print(f"Net Gain: {net_gain:.2f}")
        print(f"Avg Gain/Trade: {avg_gain:.2f}")

if __name__ == "__main__":
    simulate = GYSimulation("BTC", capital=100.0)
    simulate.runSimulation()
