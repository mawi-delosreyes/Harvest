import warnings
import threading
from Database.DataRetrieval import DataRetrieval
from Database.Database import Database
from Coins.constants import host
from Strategies.GoldenYield import GoldenYield
from datetime import datetime
from Coins.Trade import Trade
from datetime import datetime

warnings.filterwarnings('ignore')

class Harvest:
    def saveData(self, crypto, cryptoPair, interval):
        retrieval = DataRetrieval(crypto, cryptoPair)

        if interval == "1m":
            select_last_saved_data_query = "SELECT close_timestamp FROM %s ORDER BY id DESC LIMIT 1" % (crypto+"_1")
        elif interval == "5m":
            select_last_saved_data_query = "SELECT close_timestamp FROM %s ORDER BY id DESC LIMIT 1" % (crypto+"_5")

        last_timestamp = Database(crypto).retrieveData(select_last_saved_data_query)
        # last_timestamp = 1748707200000


        if len(last_timestamp) == 0:
            retrieval.saveCryptoData(interval)
        elif last_timestamp[0][0].hour == datetime.now().hour and last_timestamp[0][0].minute == datetime.now().minute:
            retrieval.saveCryptoData(interval)
        else:
            retrieval.saveDelayedData(last_timestamp[0][0], interval)

        # while last_timestamp < int(datetime.now().timestamp() * 1000):
        #     retrieval.saveDelayedData(last_timestamp, interval)
        #     last_timestamp += 7200000
    
    def executeTrade(self, crypto, interval):
        Database(None).updateDB('Cryptocurrency', 'cooldown = GREATEST(cooldown - 1, 0)', '')

        check_hold_query = "SELECT crypto_name, hold, take_profit, break_even, stop_loss, cooldown, reach_even, reach_stoploss FROM Cryptocurrency"
        hold = Database(None).retrieveData(check_hold_query)
        crypto_holdings = {
            entry[0]: {
                'hold': entry[1],
                'take_profit': entry[2],
                'break_even': entry[3],
                'stop_loss': entry[4],
                'cooldown': entry[5],
                'reach_even': entry[6],
                'reach_stoploss': entry[7]
            }
            for entry in hold
        }

        btc = GoldenYield("BTC")
        btc_cooldown = crypto_holdings[crypto]['cooldown']
        btc_hold = crypto_holdings[crypto]['hold']
        btc_tp = crypto_holdings[crypto]['take_profit']
        btc_sl = crypto_holdings[crypto]['stop_loss']
        btc_trading = threading.Thread(target=btc.Strategy, args=(crypto, btc_cooldown, interval, btc_hold, btc_tp, btc_sl))
        btc_trading.start()
        btc_trading.join()      

        crypto_scores = {
            "BTC": btc.score
        }

        uptred_filter = {k: v for k, v in crypto_scores.items() if v is not None and v > 0}
        crypto = next(
            (k for k, v in crypto_holdings.items() if v['hold'] == 1),
            next(
                (k for k, v in sorted(uptred_filter.items(), key=lambda x: x[1], reverse=True)),
                None
            ))   

        if crypto:
            trade = Trade(crypto)

            if crypto == "BTC":
                if btc.verdict == "buy" and crypto_holdings[crypto]['cooldown'] == 0:
                    trade.executeBuySignal()
                elif btc.verdict == "take profit":
                    trade.executeTPSL(10)
                elif btc.verdict == "stop loss":
                    trade.executeTPSL(15)
                elif btc.verdict == "exit":
                    trade.executeTPSL(10)



    def action(self):

        # self.saveData("ETH", "ETHPHP", "1m")
        self.saveData("BTC", "BTCPHP", "1m")
        # self.saveData("XRP", "XRPPHP", "1m")  
        # self.saveData("SOL", "SOLPHP", "1m")

        # if datetime.now().minute % 5 == 0:
            # self.saveData("ETH", "ETHPHP", "5m")
            # self.saveData("BTC", "BTCPHP", "5m")
            # self.saveData("XRP", "XRPPHP", "5m")  
            # self.saveData("SOL", "SOLPHP", "5m")

        select_active = "SELECT active FROM User WHERE user_id=1"
        active = Database(None).retrieveData(select_active)
        if active[0][0] == 1:
           self.executeTrade("BTC", "1m")


if __name__ == "__main__":
    Harvest().action()
