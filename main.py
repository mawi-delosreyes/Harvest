import joblib
import numpy as np
import warnings
import threading
import requests
from decimal import Decimal
from Database.DataRetrieval import DataRetrieval
from Database.Database import Database
from Strategies.Momentum import Momentum
from Indicators.Indicators import Indicators
from datetime import datetime
from Coins.constants import host

warnings.filterwarnings('ignore')

class Harvest:
    def __init__(self):
        self.signal = None
        self.sma = None


    def saveData(self, crypto, cryptoPair):
        retrieval = DataRetrieval(crypto, cryptoPair)

        select_last_saved_data_query = "SELECT close_timestamp FROM %s ORDER BY id DESC LIMIT 1" % (crypto)
        last_timestamp = Database(crypto).retrieveData(select_last_saved_data_query)


        if len(last_timestamp) == 0:
            retrieval.saveCryptoData()
        elif last_timestamp[0][0].hour == datetime.now().hour and last_timestamp[0][0].minute == datetime.now().minute:
            retrieval.saveCryptoData()
        else:
            retrieval.saveDelayedData(last_timestamp[0][0])

    
    def getSignals(self, crypto):
        strategy = Momentum(crypto)
        strategy.retrieveData()
        self.signal, self.sma = strategy.checkSignals()


    def tradeExecution(self):
        Database(None).updateDB('Cryptocurrency', 'cooldown = GREATEST(cooldown - 1, 0)', '')

        time_url = host + "openapi/v1/time"
        server_timestamp = requests.get(time_url).json()["serverTime"]
        
        check_hold_query = "SELECT crypto_name, hold, take_profit, break_even, stop_loss, cooldown, reach_even FROM Cryptocurrency"
        hold = Database(None).retrieveData(check_hold_query)
        crypto_holdings = {
            entry[0]: {
                'hold': entry[1],
                'take_profit': entry[2],
                'break_even': entry[3],
                'stop_loss': entry[4],
                'cooldown': entry[5],
                'reach_even': entry[6]
            }
            for entry in hold
        }

        coin_max_thresholds = {
            'BTC': 9.0,
            'ETH': 8.5
            # 'SOL': 8.0
        }
        coin_min_thresholds = {
            'BTC': 5.3,
            'ETH': 4.8
            # 'SOL': 4.3
        }

        eth = Harvest()
        btc = Harvest()
        # sol = Harvest()

        eth_trading = threading.Thread(target=eth.getSignals, args=("ETH",))
        btc_trading = threading.Thread(target=btc.getSignals, args=("BTC",))
        # sol_trading = threading.Thread(target=sol.getSignals, args=("SOL",))

        eth_trading.start()
        btc_trading.start()
        # sol_trading.start()

        eth_trading.join()
        btc_trading.join()
        # sol_trading.join()

        crypto_signals = {
            "BTC": btc.signal,
            "ETH": eth.signal
            # "SOL": sol.signal
        }

        with open('/dev/tty8', 'w') as tty:
            tty.write(str(datetime.now().minute) + ' - ' + str(crypto_signals) + '\n')

        uptred_filter = {k: v for k, v in crypto_signals.items() if v > 0}
        crypto = max(uptred_filter.items(), key=lambda item: item[1])[0] if uptred_filter else None
        if crypto and crypto_holdings[crypto]['cooldown'] == 0:
            if all(crypto['hold'] == 0 for crypto in crypto_holdings.values()):
                crypto_price = float(DataRetrieval(crypto, crypto + "PHP").getPrice(True)[4])

                if crypto == "BTC":
                    btc_data = Indicators("BTC").retrieveDatabaseData()
                    btc_model = joblib.load("Models/btc_model.pkl")
                    sma_mid, sma_long = btc.sma
                    forecast = btc_model.predict(np.array(btc_data[-50:])[:, [2, 3, 4, 6]]) * 1e6
                elif crypto == "ETH":
                    eth_data = Indicators("ETH").retrieveDatabaseData()
                    eth_model = joblib.load("Models/eth_model.pkl")
                    sma_mid = eth.sma[0]
                    sma_long = eth.sma[1]
                    forecast = eth_model.predict(np.array(eth_data[-50:])[:, [2, 3, 4, 6]]) * 1e6
                # elif crypto == "SOL":
                #     sol_data = Indicators("SOL").retrieveDatabaseData()
                #     sol_model = joblib.load("Models/sol_model.pkl")
                #     sma_mid = sol.sma[0]
                #     sma_long = sol.sma[1]
                #     forecast = sol_model.predict(np.array(sol_data[-50:])[:, [2, 3, 4, 6]]) * 1e6

                min_forecast = min(forecast)

                if ((crypto_price < (min_forecast * 1.002) or (forecast[-1] - forecast[0]) / len(forecast) > 0.01) and
                    sma_mid > sma_long and
                    coin_min_thresholds[crypto] < crypto_signals[crypto] < coin_max_thresholds[crypto]
                ):
                    strategy = Momentum(crypto)
                    strategy.executeBuySignal(server_timestamp)
                    Database(None).updateDB('Cryptocurrency', f'cooldown = {max(0, int((crypto_signals[crypto] - coin_min_thresholds[crypto]) * 2))}, reach_even = 0', f"WHERE crypto_name='{crypto}'")

            elif any(crypto['hold'] == 1 for crypto in crypto_holdings.values()) and crypto_holdings[crypto]['cooldown'] == 0:
                crypto = [k for k, v in crypto_holdings.items() if v['hold'] == 1][0]
                crypto_price = float(DataRetrieval(crypto, crypto + "PHP").getPrice(True)[4])

                with open('/dev/tty8', 'w') as tty:
                    tty.write(str(crypto) + " Signal: " + str(crypto_signals[crypto]) + "\n")
                    tty.write(str(crypto) + " TP: " + str(crypto_holdings[crypto]['take_profit']) + "\n")
                    tty.write(str(crypto) + " BE: " + str(crypto_holdings[crypto]['break_even']) + "\n")
                    tty.write(str(crypto) + " SL: " + str(crypto_holdings[crypto]['stop_loss']) + "\n")
                    tty.write("\n")

                if crypto == "BTC":
                    btc_data = Indicators("BTC").retrieveDatabaseData()
                    btc_model = joblib.load("Models/btc_model.pkl")
                    sma_mid, sma_long = btc.sma
                    forecast = btc_model.predict(np.array(btc_data[-50:])[:, [2, 3, 4, 6]]) * 1e6
                elif crypto == "ETH":
                    eth_data = Indicators("ETH").retrieveDatabaseData()
                    eth_model = joblib.load("Models/eth_model.pkl")
                    sma_mid,sma_long = eth.sma
                    forecast = eth_model.predict(np.array(eth_data[-50:])[:, [2, 3, 4, 6]]) * 1e6
                # elif crypto == "SOL":
                #     sol_data = Indicators("SOL").retrieveDatabaseData()
                #     sol_model = joblib.load("Models/sol_model.pkl")
                #     sma_mid, sma_long = sol.sma
                #     forecast = sol_model.predict(np.array(sol_data[-50:])[:, [2, 3, 4, 6]]) * 1e6

                max_forecast = max(forecast)

                if crypto_holdings[crypto]['reach_even'] == 0 and crypto_price >= crypto_holdings[crypto]['break_even']:
                    Database(None).updateDB('Cryptocurrency', 'reach_even = 1', f"WHERE crypto_name='{crypto}'")

                if ((crypto_holdings[crypto]['reach_even'] != 1 and crypto_price < crypto_holdings[crypto]['stop_loss']) or
                    (crypto_holdings[crypto]['reach_even'] == 1 and ((crypto_price < crypto_holdings[crypto]['break_even'] and sma_mid < sma_long) or
                                                                     (crypto_price > crypto_holdings[crypto]['break_even']))) or
                    (crypto_price > crypto_holdings[crypto]['take_profit'] or crypto_price > max_forecast)
                ):
                    strategy = Momentum(crypto)
                    strategy.executeTPSL(server_timestamp)

                    with open('/dev/tty8', 'w') as tty:
                        tty.write("\n\nExit {} at price: {:.4f}.\n\n".format(crypto, crypto_price))

                    wallet_info = DataRetrieval(self.crypto, self.crypto+'PHP').getWalletBalance(server_timestamp)
                    if wallet_info['PHP'] < 150:
                        Database(None).updateDB('User', 'active = 0', f"WHERE user_id=1")


    def action(self):

        self.saveData("ETH", "ETHPHP")
        self.saveData("BTC", "BTCPHP")
        self.saveData("XRP", "XRPPHP")  
        self.saveData("SOL", "SOLPHP")

        with open('/dev/tty8', 'w') as tty:
            tty.write(str(datetime.now().strftime("%H:%M:%S")) + " - Saved Data" + '\n')
        
        select_active = "SELECT active FROM User WHERE user_id=1"
        active = Database(None).retrieveData(select_active)
        if active[0][0] == 1:
            self.tradeExecution()
        else:
            with open('/dev/tty8', 'w') as tty:
                tty.write('User not active\n')     


if __name__ == "__main__":
    Harvest().action()
