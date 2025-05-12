import configparser
config = configparser.ConfigParser()
config.read('Coins/config.ini')

host = config['Coins']['host']
api_key = config['Harvest-Read-Only']['api_key']
secret_key = config['Harvest-Read-Only']['secret_key']