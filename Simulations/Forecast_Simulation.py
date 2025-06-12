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
        sma, macd, adx, bb, kijun, obv, pp, rsi, close_price = Indicator_Simulation(crypto, data).runIndicators()
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
        upper_band = bb[0]
        bb_sma = bb[1]
        lower_band = bb[2]
        kijun = kijun
        obv_value = obv[0]
        obv_prev = obv[1]
        pivot = pp[0]
        r1 = pp[1]
        s1 = pp[2]
        r2 = pp[3]
        s2 = pp[4]
        r3 = pp[5]
        s3 = pp[6]
        rsi_value = rsi


        indicator_signals = Signals(sma_short, sma_mid, sma_long, ema_fast, ema_slow, macd_value, signal_line,
        plus_di, minus_di, adx_value, upper_band, bb_sma, lower_band,
        kijun, obv_value, obv_prev, pivot, r1, s1, r2, s2,
        r3, s3, rsi_value, close_price)


        weights = {
            'SMA': 0.8,
            'MACD': 1.3,
            'ADX': 1.6,
            'BollingerBand': 1.0,
            'Kijun': 1.8,
            'OBV': 1.5,
            'RSI': 1.0,
            'PivotPoint': 0.5
        }

        indicator_signal = sum([
            indicator_signals.SMA() * weights['SMA'], 
            indicator_signals.MACD() * weights['MACD'], 
            indicator_signals.ADX() * weights['ADX'], 
            indicator_signals.BollingerBand() * weights['BollingerBand'], 
            indicator_signals.Kijun() * weights['Kijun'], 
            indicator_signals.OBV() * weights['OBV'], 
            indicator_signals.RSI() * weights['RSI'], 
            indicator_signals.PivotPoint() * weights['PivotPoint']
        ])

        return indicator_signal, (sma_mid, sma_long)


    def executeBuySignal(self, crypto_price):
        risk_percent = Decimal("0.003")
        reward_percent = Decimal("0.005")
        total_fee_percent = Decimal("0.006")  # 0.3% entry + 0.3% exit

        break_even_price = (crypto_price * (1 + (total_fee_percent+risk_percent)))
        take_profit = (crypto_price * (1 + total_fee_percent)) * (1 + reward_percent)
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

        btc_window = btc[:max_periods]
        eth_window = eth[:max_periods]


        crypto_holdings = {
            "BTC": {
                'hold': 0,
                'take_profit': 0,
                'break_even': 0,
                'stop_loss': 0,
                'reach_even': 0,
                'reach_stoploss': 0,
                'cooldown': 0
            },
            "ETH": {
                'hold': 0,
                'take_profit': 0,
                'break_even': 0,
                'stop_loss': 0,
                'reach_even': 0,
                'reach_stoploss': 0,
                'cooldown': 0
            }
        }

        coin_max_thresholds = {
            'BTC': 8.5,
            'ETH': 8.0
        }
        coin_min_thresholds = {
            'BTC': 4.0,
            'ETH': 3.5
        }

        btc_model = joblib.load("Models/btc_model.pkl")
        eth_model = joblib.load("Models/eth_model.pkl")

        for i in range(max_periods, len(btc)):

            btc_data = btc_window
            eth_data = eth_window

            btc_signal, btc_sma = self.getSignals("BTC", btc_data)
            eth_signal, eth_sma = self.getSignals("ETH", eth_data)

            crypto_signals = {
                "BTC": btc_signal,
                "ETH": eth_signal
            }   

            if crypto_holdings['BTC']['cooldown'] > 0:
                crypto_holdings['BTC']['cooldown'] -= 1
            
            if crypto_holdings['ETH']['cooldown'] > 0:
                crypto_holdings['ETH']['cooldown'] -= 1

            
            if all(crypto['hold'] != 1 for crypto in crypto_holdings.values()):
                # print("|")

                uptred_filter = {k: v for k, v in crypto_signals.items() if v > 0}
                crypto = max(uptred_filter.items(), key=lambda item: item[1])[0] if uptred_filter else None

                # Entry
                if crypto and crypto_holdings[crypto]['cooldown'] == 0:
                    if crypto == "BTC":
                        crypto_price = btc_data[-1][3]
                        sma_mid, sma_long = btc_sma
                        forecast = btc_model.predict(np.array(btc_data[-n_lags:])[:, [0, 1, 2, 4]]) * 1e6
                    elif crypto == "ETH":
                        crypto_price = eth_data[-1][3]
                        sma_mid, sma_long = eth_sma
                        forecast = eth_model.predict(np.array(eth_data[-n_lags:])[:, [0, 1, 2, 4]]) * 1e6

                    min_forecast = min(forecast)

                    # Buy condition: price low, SMA trending up, signal strength within threshold, model bullish
                    if (sma_mid > sma_long and
                        coin_min_thresholds[crypto] < crypto_signals[crypto] < coin_max_thresholds[crypto]):

                        tp, sl, be = self.executeBuySignal(crypto_price)

                        trades += 1
                        crypto_holdings[crypto]['hold'] = 1
                        crypto_holdings[crypto]['take_profit'] = tp
                        crypto_holdings[crypto]['break_even'] = be
                        crypto_holdings[crypto]['stop_loss'] = min(sl, min_forecast)
                        crypto_holdings[crypto]['cooldown'] = max(0, int((crypto_signals[crypto] - coin_min_thresholds[crypto]) * 2))

                        # print(f"|- BUY {crypto}: Price: {crypto_price}, TP: {tp}, BE: {be}, SL: {sl}")

            # exit
            elif any(crypto['hold'] == 1 for crypto in crypto_holdings.values()):
                # print("|")

                crypto = [k for k, v in crypto_holdings.items() if v['hold'] == 1][0]

                if crypto == "BTC":
                    crypto_price = btc_data[-1][3]
                    sma_mid, sma_long = btc_sma
                    forecast = btc_model.predict(np.array(btc_data[-n_lags:])[:, [0, 1, 2, 4]]) * 1e6
                elif crypto == "ETH":
                    crypto_price = eth_data[-1][3]
                    sma_mid, sma_long = eth_sma
                    forecast = eth_model.predict(np.array(eth_data[-n_lags:])[:, [0, 1, 2, 4]]) * 1e6

                max_forecast = max(forecast)


                # Move to break-even once price is +0.3% above entry
                if crypto_holdings[crypto]['reach_even'] == 0 and crypto_price >= crypto_holdings[crypto]['break_even']:
                    crypto_holdings[crypto]['reach_even'] = 1

                # Stop Loss
                if crypto_holdings[crypto]['reach_even'] != 1 and crypto_price < crypto_holdings[crypto]['stop_loss']:
                    # print(f"|- SELL (Loss) {crypto}: Price: {crypto_price}, SL Hit")
                    
                    if crypto_holdings[crypto]['reach_stoploss'] == 1:
                        fail_trades += 1
                        crypto_holdings[crypto]['hold'] = 0
                        crypto_holdings[crypto]['cooldown'] = 3
                        crypto_holdings[crypto]['take_profit'] = 0
                        crypto_holdings[crypto]['break_even'] = 0
                        crypto_holdings[crypto]['stop_loss'] = 0
                        crypto_holdings[crypto]['reach_even'] = 0
                        crypto_holdings[crypto]['reach_stoploss'] = 0
                    else:
                        crypto_holdings[crypto]['cooldown'] = 6
                        crypto_holdings[crypto]['reach_stoploss'] = 1

                # Reach Even
                elif crypto_holdings[crypto]['reach_even'] == 1:
                    # stop loss
                    if crypto_price < crypto_holdings[crypto]['break_even'] and sma_mid < sma_long:
                        if crypto_holdings[crypto]['reach_stoploss'] == 1:
                            # print(f"|- SELL (Loss) {crypto}: Price: {crypto_price}, BE Hit")
                            fail_trades += 1
                            crypto_holdings[crypto]['hold'] = 0
                            crypto_holdings[crypto]['cooldown'] = 3
                            crypto_holdings[crypto]['take_profit'] = 0
                            crypto_holdings[crypto]['break_even'] = 0
                            crypto_holdings[crypto]['stop_loss'] = 0
                            crypto_holdings[crypto]['reach_even'] = 0
                            crypto_holdings[crypto]['reach_stoploss'] = 0
                        else:
                            crypto_holdings[crypto]['cooldown'] = 3
                            crypto_holdings[crypto]['reach_stoploss'] = 1  

                    # break even
                    elif crypto_price > crypto_holdings[crypto]['break_even']:
                        if (sma_mid < sma_long or crypto_price > max_forecast or 
                            coin_min_thresholds[crypto] > crypto_signals[crypto] 
                            ):
                            # print(f"|- SELL (Win) {crypto}: Price: {crypto_price}, BE Hit")
                            success_trades += 1
                            crypto_holdings[crypto]['hold'] = 0
                            crypto_holdings[crypto]['cooldown'] = 3
                            crypto_holdings[crypto]['take_profit'] = 0
                            crypto_holdings[crypto]['break_even'] = 0
                            crypto_holdings[crypto]['stop_loss'] = 0
                            crypto_holdings[crypto]['reach_even'] = 0  
                            crypto_holdings[crypto]['reach_stoploss'] = 0

                elif crypto_price > crypto_holdings[crypto]['take_profit']:
                    # print(f"|- SELL (Win) {crypto}: Price: {crypto_price}, TP Hit")

                    success_trades += 1
                    crypto_holdings[crypto]['hold'] = 0
                    crypto_holdings[crypto]['cooldown'] = 3
                    crypto_holdings[crypto]['take_profit'] = 0
                    crypto_holdings[crypto]['break_even'] = 0
                    crypto_holdings[crypto]['stop_loss'] = 0
                    crypto_holdings[crypto]['reach_even'] = 0    
                    crypto_holdings[crypto]['reach_stoploss'] = 0


            btc_window.pop(0)
            eth_window.pop(0)

            btc_window.append(btc[i])
            eth_window.append(eth[i])

        print(f"Success: {success_trades}, Fail: {fail_trades}, Trades: {trades}")
        print(f"Success Rate: {success_trades/trades}")


if __name__ == "__main__":
    simulate = Forecast_Simulation()
    simulate.simulateTrade()