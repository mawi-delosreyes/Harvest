from datetime import datetime, timedelta

from Implementation.Indicators.SMA import SMA
from Implementation.Indicators.MACD import MACD
from Implementation.Indicators.ADX import ADX
from Implementation.Indicators.Signals import Signals
from Implementation.Database.Database import Database
from Implementation.API.API import RetrieveAPIData
from Implementation.API.Database import RetrieveDBData


class main:
    def __init__(self, crypto, timestamp, hold, purchase_signal, entry_price, total_investment_amount, trade_amount, total_trades, errors):
        self.latest_db_data = None
        self.sma_fast_period = 10
        self.sma_slow_period = 30
        self.macd_fast_period = 12
        self.macd_slow_period = 26
        self.macd_signal_line_period = 9
        self.adx_period = 14
        self.rows = max(self.sma_fast_period, self.sma_slow_period, 
                        self.macd_fast_period, self.macd_slow_period, self.macd_signal_line_period,
                        self.adx_period)
        self.crypto = crypto
        self.sma_fast = None
        self.sma_slow = None
        self.ema_fast = None
        self.ema_slow = None
        self.macd = None
        self.signal_line = None
        self.atr = None
        self.plus_di = None
        self.minus_di = None
        self.adx = None
        self.signal = None
        self.latest_data = RetrieveAPIData().retrieveAPIData(timestamp)
        self.latest_db_data = RetrieveDBData(self.crypto, self.rows).retrieveDBData()
        self.total_investment_amount = total_investment_amount
        self.trade_amount = trade_amount
        self.entry_price = entry_price
        self.hold = hold
        self.total_trades = total_trades
        self.errors = errors
        self.tp = 2
        self.sl = -1
        self.profit = 0
        self.purchase_signal = purchase_signal


    def getIndicators(self):

        if not self.latest_db_data or len(self.latest_db_data) < 17: return
        (_, _, open, high, low, close, volume,
            sma_fast, sma_slow, ema_fast, ema_slow,
            macd, signal_line, atr, plus_di, minus_di, adx
        ) = zip(*self.latest_db_data)

        open = list(open)
        high = list(high)
        low = list(low)
        close = list(close)
        volume = list(volume)
        sma_fast = list(sma_fast)
        sma_slow = list(sma_slow)
        ema_fast = list(ema_fast)
        ema_slow = list(ema_slow)
        macd = list(macd)
        signal_line = list(signal_line)
        atr = list(atr)
        plus_di = list(plus_di)
        minus_di = list(minus_di)
        adx = list(adx)

        
        sma = SMA(close, self.sma_fast_period, self.sma_slow_period)
        self.sma_fast, self.sma_slow = sma.computeSMA()

        macd = MACD(close, self.macd_fast_period, self.macd_slow_period, self.macd_signal_line_period, ema_fast[-1], ema_slow[-1], signal_line[-1])
        self.ema_fast, self.ema_slow, self.macd, self.signal_line = macd.computeMACD()

        adx = ADX(high, low, close, self.adx_period, atr[-1], plus_di[-1], minus_di[-1], adx[-1])
        self.adx, self.atr, self.plus_di, self.minus_di = adx.computeADX()


    def saveToDatabase(self):
        crypto_columns = "(timestamp, open, high, low, close, volume)"
        crypto_data_value = (self.latest_data['timestamp'], self.latest_data['open'], 
                             self.latest_data['high'], self.latest_data['low'], self.latest_data['close'], 
                             self.latest_data['volume'])
        last_data_index = Database().saveDB(self.crypto, crypto_columns, crypto_data_value)

        if all(value is not None for value in [self.sma_fast, self.sma_slow]):
            sma_table = self.crypto + "_SMA"
            sma_columns = "(id, sma_fast, sma_slow)"
            sma_data_values = (last_data_index, self.sma_fast, self.sma_slow)
            Database().saveDB(sma_table, sma_columns, sma_data_values)

        if all(value is not None for value in [self.ema_fast, self.ema_slow, self.macd, self.signal_line]):
            macd_table = self.crypto + "_MACD"
            macd_columns = "(id, ema_fast, ema_slow, macd, signal_line)"
            macd_data_values = (last_data_index, self.ema_fast, self.ema_slow, self.macd, self.signal_line)
            Database().saveDB(macd_table, macd_columns, macd_data_values)

        if all(value is not None for value in [self.atr, self.plus_di, self.minus_di, self.adx]):
            adx_table = self.crypto + "_ADX"
            adx_columns = "(id, atr, plus_di, minus_di, adx)"
            adx_data_values = (last_data_index, self.atr, self.plus_di, self.minus_di, self.adx)
            Database().saveDB(adx_table, adx_columns, adx_data_values)

        print(self.crypto + " : Inserted " + str(self.latest_data))


    def checkSignals(self):
        if all(value is not None for value in [self.sma_fast, self.sma_slow, self.ema_fast, self.ema_slow, self.macd, self.signal_line,
                                        self.plus_di, self.minus_di, self.adx]):

            indicator_signals = Signals(self.sma_fast, self.sma_slow, self.ema_fast, self.ema_slow, self.macd, self.signal_line,
                                        self.plus_di, self.minus_di, self.adx)
            
            self.signal = indicator_signals.SMA() * indicator_signals.MACD() * indicator_signals.ADX()


    def tradeExecution(self):
        # No Position
        if not self.hold:
            if self.signal == 1 or self.signal == -1:
                if self.signal == 1:
                    self.purchase_signal = "buy"
                elif self.signal == -1:
                    self.purchase_signal = "sell"
                else:
                    self.purchase_signal = None

                execution_data = RetrieveAPIData().executeTrade(self.purchase_signal, self.trade_amount, self.latest_data['close'])
                self.entry_price = execution_data['entry_price']
                self.total_trades += 1
                self.hold = True

        # Holding a Position
        elif self.hold:
            trade_info = RetrieveAPIData().tradeInfo(self.purchase_signal, self.trade_amount, self.entry_price, self.latest_data['close'])
            self.profit = trade_info["profit"]

            take_profit = self.tp * self.adx
            stop_loss = self.sl * self.adx

            if (self.profit >= take_profit or self.profit <= stop_loss) or self.signal == 0:
                self.total_investment_amount += self.profit  # Update investment amount with the profit or loss from this trade
                if self.profit < 0:
                    self.errors += 1
                self.hold = False  # Exit the position
                self.profit = 0  # Reset after trade is closed     

        if self.total_investment_amount < self.trade_amount:
            self.trade_amount = self.total_investment_amount
        else: self.trade_amount = 200

        print(self.total_investment_amount)

        if self.total_investment_amount <= 0:
            print(f"Investment depleted at iteration {i} on {self.latest_data['timestamp']}")
        
        return self.hold, self.purchase_signal, self.entry_price, self.total_investment_amount, self.trade_amount, self.total_trades, self.errors
        



if __name__ == '__main__':

    '''
    strategy = main("XRP")
    strategy.connectDB()
    strategy.retrieveAPIData("2018-05-04 10:50:00")
    strategy.retrieveDBData()
    #strategy.getIndicators()
    strategy.saveToDatabase()
    strategy.closeDB()
    '''

    timestamp = datetime.strptime("2025-03-31 23:55:00", '%Y-%m-%d %H:%M:%S')
    hold = False
    purchase_signal = None
    entry_price = None
    total_investment_amount = 200
    trade_amount = 200
    total_trades = 0
    errors = 0

    for i in range(1, 100):
        #print("Retrieving Data")
        strategy = main("XRP", timestamp, hold, purchase_signal, entry_price, total_investment_amount, 
                        trade_amount, total_trades, errors)
        strategy.getIndicators()
        strategy.saveToDatabase()
        strategy.checkSignals()
        hold, purchase_signal, entry_price, total_investment_amount, trade_amount, total_trades, errors = strategy.tradeExecution()
        timestamp = timestamp + timedelta(minutes=5)

