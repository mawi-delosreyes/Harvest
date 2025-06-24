import requests
import sys
from decimal import Decimal, ROUND_HALF_UP
from Database.Database import Database
from Database.DataRetrieval import DataRetrieval
from Logging.Logger import Logger
from Coins.GenerateSignature import generateTradeSignature
from Coins.constants import host


class Trade:
       
    def __init__(self, crypto):
        self.crypto = crypto
        self.logger = Logger(crypto)

    def executeBuySignal(self):
        self.logger.info("Buy Signal Detected")

        wallet_info = DataRetrieval(self.crypto, self.crypto+'PHP').getWalletBalance()

        order_url = "openapi/v1/order"
        time_url = host + "openapi/v1/time"
        server_timestamp = requests.get(time_url).json()["serverTime"]

        params = {
            "symbol": self.crypto + "PHP",
            "side": "buy",
            "type": "MARKET",
            "quoteOrderQty": wallet_info['PHP']['free'],
            "timestamp": server_timestamp,
            "recvWindow": 20000,
        }

        order_url, api_key, params['signature'] = generateTradeSignature(order_url, params)

        headers = {
            'X-COINS-APIKEY': api_key
        }
        
        try:
            response = requests.post(order_url, params=params, headers=headers)
            self.logger.info("Order Response: {}".format(response.json()))
        except Exception as e:
            self.logger.error("Error executing order: {}".format(e))
            sys.exit(0)

        try:
            trade = response.json()['fills'][0]
        except Exception as e:
            print(e)
            self.logger.error(e)
            print(response.json())

        crypto_price = Decimal(trade['price'])
        risk_percent = Decimal("0.003")
        reward_percent = Decimal("0.005")
        qty = Decimal(trade['qty'])
        php_converted_commission = Decimal(trade['commission']) * Decimal(trade['price'])
        total_fee_php = php_converted_commission * Decimal(2) 
        
        break_even_price = (crypto_price + (total_fee_php / qty))
        take_profit = (crypto_price + (total_fee_php / qty)) * (1 + reward_percent)
        stop_loss = crypto_price * (1 - risk_percent)

        update_statement = "take_profit={}, stop_loss={}, break_even={}, cooldown=0, hold=1".format(take_profit, stop_loss, break_even_price)
        condition = "WHERE crypto_name='{}'".format(self.crypto)
        Database(self.crypto).updateDB('Cryptocurrency', update_statement, condition)
        self.logger.info("Updated Take Profit: {}, Stop Loss: {}".format(take_profit, stop_loss))
        self.logger.info("Added hold")

    def executeTPSL(self, cooldown):
        self.logger.info("Sell Signal Detected")

        wallet_info = DataRetrieval(self.crypto, self.crypto+'PHP').getWalletBalance()

        order_url = "openapi/v1/order"
        time_url = host + "openapi/v1/time"
        server_timestamp = requests.get(time_url).json()["serverTime"]

        if self.crypto == "XRP":
            quantity = int(Decimal(wallet_info[self.crypto]['free']) * 100) / 100
        elif self.crypto == "BTC":
            quantity = int(Decimal(wallet_info[self.crypto]['free']) * 10000000) / 10000000
        elif self.crypto == "ETH":
            quantity = int(Decimal(wallet_info[self.crypto]['free']) * 1000000) / 1000000
        elif self.crypto == "SOL":
            quantity = int(Decimal(wallet_info[self.crypto]['free']) * 10000) / 10000

        params = {
            "symbol": self.crypto + "PHP",
            "side": "SELL",
            "type": "MARKET",
            "quantity": quantity,
            "timestamp": server_timestamp,
            "recvWindow": 20000,
        }

        order_url, api_key, params['signature'] = generateTradeSignature(order_url, params)

        headers = {
            'X-COINS-APIKEY': api_key
        }
        
        try:
            response = requests.post(order_url, params=params, headers=headers)
            self.logger.info("Order Response: {}".format(response.json()))
        except Exception as e:
            self.logger.error("Error executing order: {}".format(e))
            sys.exit(0)

        update_statement = "take_profit=0, stop_loss=0, break_even=0, hold=0, cooldown={}, reach_even=0, reach_stoploss=0".format(cooldown)
        condition = "WHERE crypto_name='{}'".format(self.crypto)
        Database(self.crypto).updateDB('Cryptocurrency', update_statement, condition)
        self.logger.info("Updated Take Profit: 0, Stop Loss: 0")
        self.logger.info("Removed hold")


        wallet_info = DataRetrieval(self.crypto, self.crypto+'PHP').getWalletBalance()
        if float(wallet_info['PHP']['free']) < float(130.0):
            Database(None).updateDB('User', 'active = 0', "WHERE user_id=1")