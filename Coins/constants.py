import configparser
config = configparser.ConfigParser()
config.read('Coins/config.ini')

host = config['Coins']['host']
api_key = config['Harvest-Trading']['api_key']
secret_key = config['Harvest-Trading']['secret_key']
ro_api_key = config['Harvest-Read-Only']['api_key']
ro_secret_key = config['Harvest-Read-Only']['secret_key']