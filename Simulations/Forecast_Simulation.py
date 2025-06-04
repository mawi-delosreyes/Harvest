import joblib
import numpy as np
import warnings

from Database.Database import Database
from decimal import Decimal

warnings.filterwarnings('ignore')

class Forecast_Simulation:

    def retrieveDatabaseData(self, crypto):
        col_names = "crypto.open, crypto.high, crypto.low, crypto.close, crypto.volume"

        select_crypto_data_query = "SELECT %s FROM %s AS crypto " % (col_names, crypto) 
        select_crypto_data_query += "ORDER BY crypto.id ASC"

        return Database(crypto).retrieveData(select_crypto_data_query)
    
    
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

            btc_latest_data = np.array(btc_data[-n_lags:])
            features = btc_latest_data[:, [0, 1, 2, 4]]
            forecast = model.predict(features)
            forecast = forecast * 1e6

            max_forecast = max(forecast)
            min_forecast = min(forecast)
                
            crypto_price = btc_data[-1][3]
            crypto = "BTC"
            
            if crypto_holdings[crypto]['cooldown'] > 0: 
                crypto_holdings[crypto]['cooldown'] -= 1
                print("|")
            elif crypto_holdings[crypto]['cooldown'] == 0:
                if crypto_holdings[crypto]["hold"] == 0:
                    if crypto_price < min_forecast:
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