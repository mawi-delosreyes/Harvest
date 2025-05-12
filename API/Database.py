from Implementation.Database.Database import Database

class RetrieveDBData:
    def __init__(self, crypto, rows):
        self.crypto = crypto
        self.rows = rows

    def retrieveDBData(self):

        col_names = "crypto.id, crypto.timestamp, crypto.open, crypto.high, crypto.low, crypto.close, crypto.volume, " \
        "sma.sma_fast, sma.sma_slow, macd.ema_fast, macd.ema_slow, macd.macd, macd.signal_line, " \
        "adx.atr, adx.plus_di, adx.minus_di, adx.adx"

        select_crypto_data_query = "SELECT * FROM ("
        select_crypto_data_query += "SELECT %s FROM %s AS crypto " % (col_names, self.crypto) 
        select_crypto_data_query += "LEFT JOIN %s_SMA as sma ON crypto.id=sma.id " % (self.crypto)
        select_crypto_data_query += "LEFT JOIN %s_MACD as macd ON crypto.id=macd.id "  % (self.crypto)
        select_crypto_data_query += "LEFT JOIN %s_ADX as adx ON crypto.id=adx.id "  % (self.crypto)
        select_crypto_data_query +=  "ORDER BY crypto.id DESC LIMIT %s" % (self.rows) 
        select_crypto_data_query += ") AS crypto_data ORDER BY crypto_data.timestamp ASC"

        latest_db_data = Database().retrieveData(select_crypto_data_query)

        return latest_db_data