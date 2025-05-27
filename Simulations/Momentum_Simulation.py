import threading
from Database.Database import Database
from Simulations.Indicator_Simulation import Indicator_Simulation
from Indicators.Signals import Signals
from decimal import Decimal, ROUND_HALF_UP

class Momentum_Simulation:

    def retrieveDatabaseData(self, crypto):
        col_names = "crypto.open, crypto.high, crypto.low, crypto.close, crypto.volume"

        select_crypto_data_query = "SELECT %s FROM %s AS crypto " % (col_names, crypto) 
        select_crypto_data_query += "ORDER BY crypto.id ASC"

        return Database(crypto).retrieveData(select_crypto_data_query)
        

    def getSignals(self, crypto, data):
        sma, macd, adx, bb, kijun, obv, pp, rsi, close_price, forecast = Indicator_Simulation(crypto, data).runIndicators()
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
        forecast_start = forecast[0]
        forecast_end = forecast[1]

        indicator_signals = Signals(sma_short, sma_mid, sma_long, ema_fast, ema_slow, macd_value, signal_line,
        plus_di, minus_di, adx_value, upper_band, bb_sma, lower_band,
        kijun, obv_value, obv_prev, pivot, r1, s1, r2, s2,
        r3, s3, rsi_value, close_price, forecast_start, forecast_end)

        weights = {
            'SMA': 1,
            'MACD': 2,
            'ADX': 1.5,
            'BollingerBand': 0.3,
            'Kijun': 1,
            'OBV': 0.2,
            'RSI': 1.5,
            'PivotPoint': 1,
            'Forecast': 2.5
        }

        indicator_signal = sum([
            indicator_signals.SMA() * weights['SMA'], 
            indicator_signals.MACD() * weights['MACD'], 
            indicator_signals.ADX() * weights['ADX'], 
            indicator_signals.BollingerBand() * weights['BollingerBand'], 
            indicator_signals.Kijun() * weights['Kijun'], 
            indicator_signals.OBV() * weights['OBV'], 
            indicator_signals.RSI() * weights['RSI'], 
            indicator_signals.PivotPoint() * weights['PivotPoint'], 
            indicator_signals.Forecast() * weights['Forecast']
        ])

        forecast_signal = indicator_signals.Forecast()
        return (indicator_signal, forecast_signal), (sma_mid, sma_long)
    

    def executeBuySignal(self, crypto_price):
        risk_percent = Decimal("0.002")
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
        btc = self.retrieveDatabaseData("BTC")
        eth = self.retrieveDatabaseData("ETH")
        # xrp = self.retrieveDatabaseData("XRP")
        sol = self.retrieveDatabaseData("SOL")


        if len(btc) < max_periods:
            print("Not enough data.")
            return

        btc_window = btc[:max_periods]
        eth_window = eth[:max_periods]
        # xrp_window = xrp[:max_periods]
        sol_window = sol[:max_periods]

        crypto_holdings = {
            "BTC": {
                'hold': 0,
                'take_profit': 0,
                'break_even': 0,
                'stop_loss': 0,
                'cooldown': 0,
                'potential_entry': 0,
                'entry_hold': 0
            },
            "ETH": {
                'hold': 0,
                'take_profit': 0,
                'break_even': 0,
                'stop_loss': 0,
                'cooldown': 0,
                'potential_entry': 0,
                'entry_hold': 0
            },
            # "XRP": {
            #     'hold': 0,
            #     'take_profit': 0,
            #     'break_even': 0,
            #     'stop_loss': 0,
            #     'cooldown': 0
            # },
            "SOL": {
                'hold': 0,
                'take_profit': 0,
                'break_even': 0,
                'stop_loss': 0,
                'cooldown': 0,
                'potential_entry': 0,
                'entry_hold': 0
            }
        }

        coin_max_thresholds = {
            'BTC': 9,
            'ETH': 8.7,
            # 'XRP': 4.5,
            'SOL': 6.5
        }
        coin_min_thresholds = {
            'BTC': 3.3,
            'ETH': 3.1,
            # 'XRP': 2.2,
            'SOL': 2.4
        }

        for i in range(max_periods, len(btc)):
            btc_data = btc_window
            eth_data = eth_window
            # xrp_data = xrp_window
            sol_data = sol_window

            btc_signal, btc_sma = self.getSignals("BTC", btc_data)
            eth_signal, eth_sma = self.getSignals("ETH", eth_data)
            # xrp_signal, xrp_sma = self.getSignals("XRP", xrp_data)
            sol_signal, sol_sma = self.getSignals("SOL", sol_data)

            crypto_signals = {
                "BTC": btc_signal,
                "ETH": eth_signal,
                # "XRP": xrp_signal,
                "SOL": sol_signal
            }            

            if crypto_holdings['BTC']['cooldown'] > 0:
                crypto_holdings['BTC']['cooldown'] -= 1
            
            if crypto_holdings['ETH']['cooldown'] > 0:
                crypto_holdings['ETH']['cooldown'] -= 1

            # if crypto_holdings['XRP']['cooldown'] > 0:
            #     crypto_holdings['XRP']['cooldown'] -= 1

            if crypto_holdings['SOL']['cooldown'] > 0:
                crypto_holdings['SOL']['cooldown'] -= 1


            if all(crypto['hold'] != 1 for crypto in crypto_holdings.values()):
                # print("|" + str(crypto_signals))

                uptred_filter = {k: v for k, v in crypto_signals.items() if v[1] > 0}
                crypto = max(uptred_filter.items(), key=lambda item: item[1][0])[0] if uptred_filter else None

                if crypto != None:
                    if crypto == "BTC":
                        crypto_price = btc_data[-1][3]
                        sma_mid = btc_sma[0]
                        sma_long = btc_sma[1]
                    elif crypto == "ETH":
                        crypto_price = eth_data[-1][3]
                        sma_mid = eth_sma[0]
                        sma_long = eth_sma[1]
                    # elif crypto == "XRP":
                    #     crypto_price = xrp_data[-1][3]
                    #     sma_mid = xrp_sma
                    elif crypto == "SOL":
                        crypto_price = sol_data[-1][3]
                        sma_mid = sol_sma[0]
                        sma_long = sol_sma[1]

                    if crypto_holdings[crypto]['entry_hold'] == 0:

                        if (crypto_holdings[crypto]['cooldown'] == 0 and 
                            coin_min_thresholds[crypto] + 0.5 < crypto_signals[crypto][0] < coin_max_thresholds[crypto] - 0.5 and
                            crypto_signals[crypto][1] > 0.3 and
                            crypto_signals[crypto][0] - crypto_signals[crypto][1] > 1.2 and
                            crypto_holdings[crypto]['possible_entry'] == 0
                        ):

                            if crypto_price > sma_mid + Decimal("1.005") and sma_long > sma_mid and crypto_holdings[crypto]['possible_entry'] == 0:
                                crypto_holdings[crypto]['entry_hold'] = 3
                                crypto_holdings[crypto]['possible_entry'] = crypto_price * Decimal("1.002")

                    else:
                        if crypto_price <= crypto_holdings[crypto]['possible_entry']:

                                tp, sl, be = self.executeBuySignal(crypto_price) 

                                crypto_holdings[crypto]['hold'] = 1
                                crypto_holdings[crypto]['take_profit'] = tp
                                crypto_holdings[crypto]['break_even'] = be
                                crypto_holdings[crypto]['stop_loss'] = sl
                                crypto_holdings[crypto]['cooldown'] = 3

                                crypto_holdings[crypto]['possible_entry'] = 0
                                crypto_holdings[crypto]['entry_hold'] = 0
                                trades += 1
                                print(f"{crypto}: Price: {crypto_price}, TP: {tp}, BE: {be}, SL: {sl}")
                        else:
                            crypto_holdings[crypto]['entry_hold'] -= 1


            elif any(crypto['hold'] == 1 for crypto in crypto_holdings.values()):
                # print("|")

                crypto = [k for k, v in crypto_holdings.items() if v['hold'] == 1][0]

                if crypto == "BTC":
                    crypto_price = btc_data[-1][3]
                elif crypto == "ETH":
                    crypto_price = eth_data[-1][3]
                # elif crypto == "XRP":
                #     crypto_price = xrp_data[-1][3]
                elif crypto == "SOL":
                    crypto_price = sol_data[-1][3]

                if (crypto_holdings[crypto]['cooldown'] == 0 and 
                    crypto_price >= crypto_holdings[crypto]['take_profit'] or 
                    crypto_price <= crypto_holdings[crypto]['stop_loss'] or
                    (crypto_price >= crypto_holdings[crypto]['break_even']and crypto_signals[crypto][1] < 0) or
                    ((crypto_signals[crypto][0] > coin_max_thresholds[crypto] or crypto_signals[crypto][0] < coin_min_thresholds[crypto]) 
                     and crypto_price >= crypto_holdings[crypto]['break_even'])
                ):
                    if crypto_price < crypto_holdings[crypto]['break_even']:
                        fail_trades += 1
                        print(f"Fail: {crypto}: Crypto Price: {crypto_price}, Sell Price: {crypto_holdings[crypto]['stop_loss']}")
                    else:
                        success_trades += 1
                        print(f"Success: {crypto}: Crypto Price: {crypto_price}, Sell Price: {crypto_holdings[crypto]['break_even']}")

                    crypto_holdings[crypto]['hold'] = 0
                    crypto_holdings[crypto]['take_profit'] = 0
                    crypto_holdings[crypto]['break_even'] = 0
                    crypto_holdings[crypto]['stop_loss'] = 0
                    crypto_holdings[crypto]['cooldown'] = 4  


            btc_window.pop(0)
            eth_window.pop(0)
            # xrp_window.pop(0)
            sol_window.pop(0)

            btc_window.append(btc[i])
            eth_window.append(eth[i])
            # xrp_window.append(xrp[i])
            sol_window.append(sol[i])

        print(f"Success: {success_trades}, Fail: {fail_trades}, Trades: {trades}")
        print(f"Success Rate: {success_trades/trades}")



if __name__ == "__main__":
    simulate = Momentum_Simulation()
    simulate.simulateTrade()
    
