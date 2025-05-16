import threading
from Database.DataRetrieval import DataRetrieval
from Database.Database import Database
from Strategies.Momentum import Momentum
from datetime import datetime
from Logging.Logger import Logger

class Harvest:
    def __init__(self, crypto, cryptoPair):
        self.crypto = crypto
        self.cryptoPair = cryptoPair
        self.logger = Logger(crypto)
        

    def saveData(self):
        retrieval = DataRetrieval(self.crypto, self.cryptoPair)

        select_last_saved_data_query = "SELECT close_timestamp FROM %s ORDER BY id DESC LIMIT 1" % (self.crypto)
        last_timestamp = Database(self.crypto).retrieveData(select_last_saved_data_query)


        if len(last_timestamp) == 0:
            retrieval.saveCryptoData()
        elif last_timestamp[0][0].hour == datetime.now().hour and last_timestamp[0][0].minute == datetime.now().minute:
            retrieval.saveCryptoData()
        else:
            retrieval.saveDelayedData(last_timestamp[0][0])

    
    def executeStrategy(self):
        try:
            strategy = Momentum(self.crypto)
            strategy.retrieveData()
            strategy.checkSignals()
            strategy.tradeExecution()
        except Exception as e:
            self.logger.error(f"Error in strategy execution: {e}")
    
    def actions(self):
        self.saveData()

        if datetime.now().hour == 0 and datetime.now().minute == 0:
           retrieval = DataRetrieval(self.crypto, self.cryptoPair)
           retrieval.saveWalletBalance()

        self.executeStrategy()




if __name__ == "__main__":

    xrp_trading = threading.Thread(target=Harvest("XRP", "XRPPHP").actions)
    xrp_trading.start()
    xrp_trading.join()

