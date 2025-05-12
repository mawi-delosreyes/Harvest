import hmac
import hashlib
from Coins.constants import host, api_key, secret_key

def generateSignature(url, params):
    url = host + url

    query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
    signature = hmac.new(secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    return url, api_key, signature