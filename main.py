import threading
import requests
from decimal import Decimal
from Database.DataRetrieval import DataRetrieval
from Database.Database import Database
from Strategies.Momentum import Momentum
from datetime import datetime
from Coins.constants import host

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
        Database(None).updateDB('Cryptocurrency', 'cooldown = GREATEST(cooldown - 1, 0), entry_hold = GREATEST(entry_hold - 1, 0)', '')

        time_url = host + "openapi/v1/time"
        server_timestamp = requests.get(time_url).json()["serverTime"]
        
        check_hold_query = "SELECT crypto_name, hold, take_profit, break_even, stop_loss, cooldown, potential_entry, entry_hold FROM Cryptocurrency"
        hold = Database(None).retrieveData(check_hold_query)
        crypto_holdings = {
            entry[0]: {
                'hold': entry[1],
                'take_profit': entry[2],
                'break_even': entry[3],
                'stop_loss': entry[4],
                'cooldown': entry[5],
                'potential_entry': entry[6],
                'entry_hold': entry[7]
            }
            for entry in hold
        }

        coin_max_thresholds = {
            'BTC': 9,
            'ETH': 8.7,
            'SOL': 6.5
        }
        coin_min_thresholds = {
            'BTC': 3.3,
            'ETH': 3.1,
            'SOL': 2.4
        }

        eth = Harvest()
        btc = Harvest()
        sol = Harvest()

        eth_trading = threading.Thread(target=eth.getSignals, args=("ETH",))
        btc_trading = threading.Thread(target=btc.getSignals, args=("BTC",))
        sol_trading = threading.Thread(target=sol.getSignals, args=("SOL",))

        eth_trading.start()
        btc_trading.start()
        sol_trading.start()

        eth_trading.join()
        btc_trading.join()
        sol_trading.join()

        crypto_signals = {
            "BTC": btc.signal,
            "ETH": eth.signal,
            "SOL": sol.signal
        }

        uptred_filter = {k: v for k, v in crypto_signals.items() if v[1] > 0}
        crypto = max(uptred_filter.items(), key=lambda item: item[1][0])[0] if uptred_filter else None
        if crypto != None:
            if all(crypto['hold'] == 0 for crypto in crypto_holdings.values()):
                crypto_price = float(DataRetrieval(crypto, crypto + "PHP").getPrice(True)[4])

                with open('/dev/tty8', 'w') as tty:
                    tty.write(str(datetime.now().minute) + ' - ' + str(crypto_signals) + '\n')

                if (crypto_holdings[crypto]['cooldown'] == 0 and 
                    coin_min_thresholds[crypto] + 0.5 < crypto_signals[crypto][0] < coin_max_thresholds[crypto] - 0.5 and
                    crypto_signals[crypto][1] > 0.3 and
                    crypto_signals[crypto][0] - crypto_signals[crypto][1] > 1.2
                ):
                    if crypto == "BTC":
                        sma_mid = btc.sma[0]
                        sma_long = btc.sma[1]
                    elif crypto == "ETH":
                        sma_mid = eth.sma[0]
                        sma_long = eth.sma[1]
                    elif crypto == "SOL":
                        sma_mid = sol.sma[0]
                        sma_long = sol.sma[1]
                    if crypto_holdings[crypto]['entry_hold'] == 0 and sma_long > sma_mid:
                        potential_entry = Decimal(crypto_price) - (Decimal(crypto_price) * Decimal("0.002"))
                        Database(None).updateDB('Cryptocurrency', f'entry_hold = 10, potential_entry={potential_entry}', f"WHERE crypto_name='{crypto}'")
                    elif crypto_holdings[crypto]['entry_hold'] != 0:
                        if crypto_price <= crypto_holdings[crypto]['potential_entry']:
                            strategy = Momentum(crypto)
                            strategy.executeBuySignal(server_timestamp)
                            Database(None).updateDB('Cryptocurrency', f'entry_hold = 0, potential_entry=0', f"WHERE crypto_name='{crypto}'")

            elif any(crypto['hold'] == 1 for crypto in crypto_holdings.values()):
                crypto = [k for k, v in crypto_holdings.items() if v['hold'] == 1][0]
                crypto_price = float(DataRetrieval(crypto, crypto + "PHP").getPrice(True)[4])

                with open('/dev/tty8', 'w') as tty:
                    tty.write(str(crypto) + " Signal: " + str(crypto_signals[crypto]) + "\n")
                    tty.write(str(crypto) + " TP: " + str(crypto_holdings[crypto]['take_profit']) + "\n")
                    tty.write(str(crypto) + " BE: " + str(crypto_holdings[crypto]['break_even']) + "\n")
                    tty.write(str(crypto) + " SL: " + str(crypto_holdings[crypto]['stop_loss']) + "\n")
                    tty.write("\n")

                if ( crypto_holdings[crypto]['cooldown'] == 0 and 
                    crypto_price >= crypto_holdings[crypto]['take_profit'] or 
                    crypto_price <= crypto_holdings[crypto]['stop_loss']or
                    (crypto_price >= crypto_holdings[crypto]['break_even'] and crypto_signals[crypto][1] < 0) or
                    ((crypto_signals[crypto][0] > coin_max_thresholds[crypto] or crypto_signals[crypto][0] < coin_min_thresholds[crypto]) 
                        and crypto_price >= crypto_holdings[crypto]['break_even'])
                ):
                    strategy = Momentum(crypto)
                    strategy.executeTPSL(server_timestamp)

                    with open('/dev/tty8', 'w') as tty:
                        tty.write("\n\nExit {} at price: {:.4f}.\n\n".format(crypto, crypto_price))


    def action(self):

        if datetime.now().minute % 5 == 0:
            self.saveData("ETH", "ETHPHP")
            self.saveData("BTC", "BTCPHP")
            self.saveData("XRP", "XRPPHP")  
            self.saveData("SOL", "SOLPHP")

            with open('/dev/tty8', 'w') as tty:
                tty.write(str(datetime.now().strftime("%H:%M:%S")) + " - Saved Data" + '\n')

        if datetime.now().hour == 0 and datetime.now().minute == 0:
            DataRetrieval(None, None).saveWalletBalance()
            with open('/dev/tty8', 'w') as tty:
                tty.write("Wallet balance saved to database\n")
        
        self.tradeExecution()


if __name__ == "__main__":
    Harvest().action()
