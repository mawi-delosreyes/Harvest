import joblib
import numpy as np
import warnings
from Indicators.Signals import Signals
from Simulations.Indicator_Simulation import Indicator_Simulation
from Database.Database import Database
from decimal import Decimal

warnings.filterwarnings('ignore')

class Forecast_Simulation:

    def retrieveDatabaseData(self, crypto):
        col_names = "crypto.open, crypto.high, crypto.low, crypto.close, crypto.volume"

        select_crypto_data_query = "SELECT %s FROM %s AS crypto " % (col_names, crypto) 
        select_crypto_data_query += "ORDER BY crypto.id ASC"

        return Database(crypto).retrieveData(select_crypto_data_query)
    
    def getSignals(self, crypto, data):
        sma, macd, adx, kijun, obv, rsi, close_price = Indicator_Simulation(crypto, data).runIndicators()
        sma_short = sma[0]
        sma_mid = sma[1]
        sma_long = sma[2]
        ema_fast = macd[0]
        ema_slow = macd[1]
        macd_value = macd[2]
        signal_line = macd[3]
        adx_value = adx[0]
        atr = adx[1]
        plus_di = adx[2]
        minus_di = adx[3]
        obv_value = obv[0]
        obv_prev = obv[1]
        rsi_value = rsi


        # indicator_signals = Signals(sma_short, sma_mid, sma_long, ema_fast, ema_slow, macd_value, signal_line,
        # plus_di, minus_di, adx_value, upper_band, bb_sma, lower_band,
        # kijun, obv_value, obv_prev, pivot, r1, s1, r2, s2,
        # r3, s3, rsi_value, close_price, forecast_start, forecast_end)

        indicator_signals = Signals(sma_short, sma_mid, sma_long, ema_fast, ema_slow, macd_value, signal_line,
        plus_di, minus_di, adx_value, None, None, None,
        kijun, obv_value, obv_prev, None, None, None, None, None,
        None, None, rsi_value, close_price, None, None)

        weights = {
            'SMA': 1,
            'MACD': 2,
            'ADX': 1.5,
            # 'BollingerBand': 0.3,
            # 'Kijun': 1,
            'OBV': 0.2,
            'RSI': 1.5
            # 'PivotPoint': 1,
            # 'Forecast': 2.5
        }

        indicator_signal = sum([
            indicator_signals.SMA() * weights['SMA'], 
            indicator_signals.MACD() * weights['MACD'], 
            indicator_signals.ADX() * weights['ADX'], 
            # indicator_signals.BollingerBand() * weights['BollingerBand'], 
            # indicator_signals.Kijun() * weights['Kijun'], 
            indicator_signals.OBV() * weights['OBV'], 
            indicator_signals.RSI() * weights['RSI']
            # indicator_signals.PivotPoint() * weights['PivotPoint'], 
            # indicator_signals.Forecast() * weights['Forecast']
        ])

        # forecast_signal = indicator_signals.Forecast()
        return indicator_signal, (sma_mid, sma_long)


    def executeBuySignal(self, crypto_price):
        risk_percent = Decimal("0.005")
        reward_percent = Decimal("0.005")
        total_fee_percent = Decimal("0.006")  # 0.3% entry + 0.3% exit

        break_even_price = crypto_price * (1 + total_fee_percent)
        take_profit = break_even_price * (1 + reward_percent)
        stop_loss = crypto_price * (1 - risk_percent)

        return take_profit, stop_loss, break_even_price
    

    def simulateTrade(self):
        success_trades = 0
        fail_trades = 0
        trades = 0
        max_periods = 50
        n_lags = 50 

        btc = self.retrieveDatabaseData("BTC")
        eth = self.retrieveDatabaseData("ETH")
        sol = self.retrieveDatabaseData("SOL")

        btc_window = btc[:max_periods]
        eth_window = eth[:max_periods]
        sol_window = sol[:max_periods]


        crypto_holdings = {
            "BTC": {
                'hold': 0,
                'take_profit': 0,
                'break_even': 0,
                'stop_loss': 0,
                'reach_even': 0,
                'cooldown': 0
            }
        }

        model = joblib.load("Simulations/lightgbm_model.pkl")

        for i in range(max_periods, len(btc)):

            btc_data = btc_window

            btc_signal, btc_sma = self.getSignals("BTC", btc_data)

            btc_latest_data = np.array(btc_data[-n_lags:])
            features = btc_latest_data[:, [0, 1, 2, 4]]
            forecast = model.predict(features)
            forecast = forecast * 1e6

            max_forecast = max(forecast)
            min_forecast = min(forecast)
                
            crypto = "BTC"            
            if crypto != None:
                if crypto == "BTC":
                    crypto_price = btc_data[-1][3]
                    sma_mid = btc_sma[0]
                    sma_long = btc_sma[1]

            if crypto_holdings[crypto]['cooldown'] > 0: 
                crypto_holdings[crypto]['cooldown'] -= 1
                print("|")
            elif crypto_holdings[crypto]['cooldown'] == 0:
                if crypto_holdings[crypto]["hold"] == 0:
                    if crypto_price < min_forecast and sma_mid > sma_long:
                        tp, sl, be = self.executeBuySignal(crypto_price) 

                        trades += 1
                        crypto_holdings[crypto]['hold'] = 1
                        crypto_holdings[crypto]['take_profit'] = tp
                        crypto_holdings[crypto]['break_even'] = be
                        crypto_holdings[crypto]['stop_loss'] = sl
                        crypto_holdings[crypto]['cooldown'] = 2

                        print(f"|- {crypto}: Price: {crypto_price}, TP: {tp}, BE: {be}, SL: {sl}")
    
                else:
                        if crypto_price < crypto_holdings[crypto]['stop_loss']:
                            fail_trades += 1
                            print(f"|- Fail: {crypto}: Crypto Price: {crypto_price}, Sell Price: {crypto_holdings[crypto]['stop_loss']}")

                            crypto_holdings[crypto]['hold'] = 0
                            crypto_holdings[crypto]['take_profit'] = 0
                            crypto_holdings[crypto]['break_even'] = 0
                            crypto_holdings[crypto]['stop_loss'] = 0
                            crypto_holdings[crypto]['cooldown'] = 4  

                        elif crypto_price > crypto_holdings[crypto]['take_profit']:
                            success_trades += 1
                            print(f"|- Success: {crypto}: Crypto Price: {crypto_price}, Sell Price: {crypto_holdings[crypto]['break_even']}")

                            crypto_holdings[crypto]['hold'] = 0
                            crypto_holdings[crypto]['take_profit'] = 0
                            crypto_holdings[crypto]['break_even'] = 0
                            crypto_holdings[crypto]['stop_loss'] = 0
                            crypto_holdings[crypto]['cooldown'] = 4  

                        else:
                            print("|")

            btc_window.pop(0)
            eth_window.pop(0)
            sol_window.pop(0)

            btc_window.append(btc[i])
            eth_window.append(eth[i])
            sol_window.append(sol[i])

        print(f"Success: {success_trades}, Fail: {fail_trades}, Trades: {trades}")
        print(f"Success Rate: {success_trades/trades}")


if __name__ == "__main__":
    simulate = Forecast_Simulation()
    simulate.simulateTrade()