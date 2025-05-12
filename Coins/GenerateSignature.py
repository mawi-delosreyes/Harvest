import hmac
import hashlib
from Coins.constants import host, api_key, secret_key, ro_api_key, ro_secret_key

def generateTradeSignature(url, params):
    url = host + url

    query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
    signature = hmac.new(secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    return url, api_key, signature

def generateReadSignature(url, params):
    url = host + url

    query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
    signature = hmac.new(ro_secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    return url, ro_api_key, signature