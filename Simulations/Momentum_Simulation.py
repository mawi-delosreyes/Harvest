import threading
from Database.Database import Database
from Simulations.Indicator_Simulation import Indicator_Simulation
from Indicators.Signals import Signals
from decimal import Decimal

class Momentum_Simulation:

    def retrieveDatabaseData(self, crypto):
        col_names = "crypto.open, crypto.high, crypto.low, crypto.close, crypto.volume"

        select_crypto_data_query = "SELECT %s FROM %s AS crypto " % (col_names, crypto) 
        select_crypto_data_query += "ORDER BY crypto.id ASC"

        return Database(crypto).retrieveData(select_crypto_data_query)
        

    def getSignals(self, crypto, data):
        sma, macd, adx, bb, kijun, obv, pp, rsi, close_price = Indicator_Simulation(crypto, data).runIndicators()
        sma_fast = sma[0]
        sma_slow = sma[1]
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

        indicator_signals = Signals(sma_fast, sma_slow, ema_fast, ema_slow, macd_value, signal_line,
        plus_di, minus_di, adx_value, upper_band, bb_sma, lower_band,
        kijun, obv_value, obv_prev, pivot, r1, s1, r2, s2,
        r3, s3, rsi_value, close_price)

        weights = {
            'SMA': 1,
            'MACD': 1.5,
            'ADX': 1,
            'BollingerBand': 0.5,
            'Kijun': 1,
            'OBV': 0.5,
            'RSI': 1,
            'PivotPoint': 1.5
        }

        signal = sum([
            indicator_signals.SMA() * weights['SMA'], 
            indicator_signals.MACD() * weights['MACD'], 
            indicator_signals.ADX() * weights['ADX'], 
            indicator_signals.BollingerBand() * weights['BollingerBand'], 
            indicator_signals.Kijun() * weights['Kijun'], 
            indicator_signals.OBV() * weights['OBV'], 
            indicator_signals.RSI() * weights['RSI'], 
            indicator_signals.PivotPoint() * weights['PivotPoint'], 
        ])

        return signal
    

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
        max_periods = 35
        cooldown_period = 3
        btc = self.retrieveDatabaseData("BTC")
        eth = self.retrieveDatabaseData("ETH")
        xrp = self.retrieveDatabaseData("XRP")

        if len(btc) < max_periods:
            print("Not enough data.")
            return

        btc_window = btc[:max_periods]
        eth_window = eth[:max_periods]
        xrp_window = xrp[:max_periods]

        crypto_holdings = {
            "BTC": {
                'hold': 0,
                'take_profit': 0,
                'break_even': 0,
                'stop_loss': 0,
                'cooldown': 0
            },
            "ETH": {
                'hold': 0,
                'take_profit': 0,
                'break_even': 0,
                'stop_loss': 0,
                'cooldown': 0
            },
            "XRP": {
                'hold': 0,
                'take_profit': 0,
                'break_even': 0,
                'stop_loss': 0,
                'cooldown': 0
            }
        }

        for i in range(max_periods, len(btc)):
            #print("|")
            btc_data = btc_window
            eth_data = eth_window
            xrp_data = xrp_window

            crypto_signals = {
                "BTC": self.getSignals("BTC", btc_data),
                "ETH": self.getSignals("ETH", eth_data),
                "XRP": self.getSignals("XRP", xrp_data)
            }            

            if crypto_holdings['BTC']['cooldown'] > 0:
                crypto_holdings['BTC']['cooldown'] -= 1
            
            if crypto_holdings['ETH']['cooldown'] > 0:
                crypto_holdings['ETH']['cooldown'] -= 1

            if crypto_holdings['XRP']['cooldown'] > 0:
                crypto_holdings['XRP']['cooldown'] -= 1

            if all(crypto['hold'] != 1 for crypto in crypto_holdings.values()):
                sorted_crypto_signals = dict(
                    sorted(
                        crypto_signals.items(),
                        key=lambda item: (item[1], -list(crypto_signals).index(item[0])),
                        reverse=True
                    )
                )

                crypto = None
                for key in sorted_crypto_signals:
                    if crypto_holdings[key]['cooldown'] == 0 and crypto_signals[key] > 4:
                        crypto = key
                        break

                if crypto != None:
                        
                    if crypto == "BTC":
                        crypto_price = btc_data[-1][3]
                    elif crypto == "ETH":
                        crypto_price = eth_data[-1][3]
                    elif crypto == "XRP":
                        crypto_price = xrp_data[-1][3]

                    tp, sl, be = self.executeBuySignal(crypto_price) 

                    crypto_holdings[crypto]['hold'] = 1
                    crypto_holdings[crypto]['take_profit'] = tp
                    crypto_holdings[crypto]['break_even'] = be
                    crypto_holdings[crypto]['stop_loss'] = sl
                    crypto_holdings[crypto]['cooldown'] = 2
                    trades += 1
                    #print(f"{crypto}: Price: {crypto_price}, TP: {tp}, BE: {be}, SL: {sl}")

            elif any(crypto['hold'] == 1 for crypto in crypto_holdings.values()):
                crypto = [k for k, v in crypto_holdings.items() if v['hold'] == 1][0]

                if crypto == "BTC":
                    crypto_price = btc_data[-1][3]
                elif crypto == "ETH":
                    crypto_price = eth_data[-1][3]
                elif crypto == "XRP":
                    crypto_price = xrp_data[-1][3]

                if (
                    crypto_price >= crypto_holdings[crypto]['take_profit'] or 
                    (crypto_price <= crypto_holdings[crypto]['stop_loss'] and crypto_holdings[crypto]['cooldown'] == 0) or
                    (crypto_signals[crypto] < -3 and crypto_holdings[crypto]['cooldown'] == 0)
                ):
                    if crypto_price < crypto_holdings[crypto]['break_even']:
                        fail_trades += 1
                        #print(f"Fail: {crypto}: Crypto Price: {crypto_price}, Sell Price: {crypto_holdings[crypto]['stop_loss']}")
                    else:
                        success_trades += 1
                        #print(f"Success: {crypto}: Crypto Price: {crypto_price}, Sell Price: {crypto_holdings[crypto]['break_even']}")

                    crypto_holdings[crypto]['hold'] = 0
                    crypto_holdings[crypto]['take_profit'] = 0
                    crypto_holdings[crypto]['break_even'] = 0
                    crypto_holdings[crypto]['stop_loss'] = 0
                    crypto_holdings[crypto]['cooldown'] = cooldown_period
                    


            btc_window.pop(0)
            eth_window.pop(0)
            xrp_window.pop(0)

            btc_window.append(btc[i])
            eth_window.append(eth[i])
            xrp_window.append(xrp[i])

        print(f"Success: {success_trades}, Fail: {fail_trades}, Trades: {trades}")
        print(f"Success Rate: {success_trades/trades}")



if __name__ == "__main__":
    simulate = Momentum_Simulation()
    simulate.simulateTrade()
    
