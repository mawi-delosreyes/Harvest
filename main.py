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
        self.atr = None


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
        self.signal, self.atr = strategy.checkSignals()


    def tradeExecution(self):
        Database(None).updateDB('Cryptocurrency', 'cooldown = GREATEST(cooldown - 1, 0)', '')

        time_url = host + "openapi/v1/time"
        server_timestamp = requests.get(time_url).json()["serverTime"]
        
        check_hold_query = "SELECT crypto_name, hold, take_profit, break_even, stop_loss, cooldown FROM Cryptocurrency"
        hold = Database(None).retrieveData(check_hold_query)
        crypto_holdings = {
            entry[0]: {
                'hold': entry[1],
                'take_profit': entry[2],
                'break_even': entry[3],
                'stop_loss': entry[4],
                'cooldown': entry[5]
            }
            for entry in hold
        }

        eth = Harvest()
        btc = Harvest()
        # xrp = Harvest()

        eth_trading = threading.Thread(target=eth.getSignals, args=("ETH",))
        btc_trading = threading.Thread(target=btc.getSignals, args=("BTC",))
        # xrp_trading = threading.Thread(target=xrp.getSignals, args=("XRP",))

        eth_trading.start()
        btc_trading.start()
        # xrp_trading.start()

        eth_trading.join()
        btc_trading.join()
        # xrp_trading.join()

        crypto_signals = {
            "ETH": eth.signal,
            "BTC": btc.signal,
            # "XRP": xrp.signal,
        }

        crypto = max(crypto_signals, key=lambda k: (crypto_signals[k], -list(crypto_signals).index(k)))
        if all(crypto['hold'] != 1 for crypto in crypto_holdings.values()):
            with open('/dev/tty8', 'w') as tty:
                tty.write(str(crypto_signals) + '\n')
        
            if crypto_signals[crypto] > 3:

                if crypto == "BTC" and crypto_holdings[crypto]['cooldown'] != 0 and crypto_signals['ETH'] > 4 and crypto_holdings['ETH']['hold'] != 1:
                    crypto = "ETH"
                elif crypto == "ETH" and crypto_holdings[crypto]['cooldown'] != 0 and crypto_signals['BTC'] > 4 and crypto_holdings['BTC']['hold'] != 1:
                    crypto = "BTC"

                if crypto_holdings[crypto]['cooldown'] == 0:
                    strategy = Momentum(crypto)
                    strategy.executeBuySignal(server_timestamp)

        elif any(crypto['hold'] == 1 for crypto in crypto_holdings.values()):
            crypto = [k for k, v in crypto_holdings.items() if v['hold'] == 1][0]
            crypto_price = float(DataRetrieval(crypto, crypto + "PHP").getPrice(True)[4])

            with open('/dev/tty8', 'w') as tty:
                tty.write(str(crypto) + " Signal: " + str(crypto_signals[crypto]) + "\n")
                tty.write(str(crypto) + " TP: " + str(crypto_holdings[crypto]['take_profit']) + "\n")
                tty.write(str(crypto) + " BE: " + str(crypto_holdings[crypto]['break_even']) + "\n")
                tty.write(str(crypto) + " SL: " + str(crypto_holdings[crypto]['stop_loss']) + "\n")
                tty.write("\n")

            if (
                crypto_price >= crypto_holdings[crypto]['take_profit'] or 
                (crypto_price <= crypto_holdings[crypto]['stop_loss'] and crypto_holdings[crypto]['cooldown'] == 0) or
                (crypto_signals[crypto] < -3 and crypto_holdings[crypto]['cooldown'] == 0)
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
