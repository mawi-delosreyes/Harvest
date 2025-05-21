import threading
import requests
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

        time_url = host + "openapi/v1/time"
        server_timestamp = requests.get(time_url).json()["serverTime"]

        check_hold_query = "SELECT crypto_name, hold, stop_loss FROM Cryptocurrency"
        hold = Database(None).retrieveData(check_hold_query)
        crypto_holdings = {entry[0]: entry[1] for entry in hold}
        crypto_sl = {entry[0]: entry[2] for entry in hold}

        if not 1 in crypto_holdings.values():
            eth = Harvest()
            btc = Harvest()

            eth_trading = threading.Thread(target=eth.getSignals, args=("ETH",))
            btc_trading = threading.Thread(target=btc.getSignals, args=("BTC",))

            eth_trading.start()
            btc_trading.start()

            eth_trading.join()
            btc_trading.join()

            crypto_signals = {
                "ETH": eth.signal,
                "BTC": btc.signal
            }
    
            with open('/dev/tty8', 'w') as tty:
                tty.write(crypto_signals + '\n')
                
            crypto = max(crypto_signals, key=lambda k: (crypto_signals[k], -list(crypto_signals).index(k)))

            if crypto == "ETH": atr = eth.atr
            elif crypto == "BTC": atr = btc.atr

            if crypto_signals[crypto] > 3:
                strategy = Momentum(crypto)
                strategy.executeBuySignal(server_timestamp, atr)
        else:
            crypto = [k for k, v in crypto_holdings.items() if v == 1][0]

            with open('/dev/tty8', 'w') as tty:
                tty.write(str(crypto) + " SL: " + str(crypto_sl[crypto]) + "\n")

            strategy = Momentum(crypto)
            strategy.executeTPSL(server_timestamp)


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
