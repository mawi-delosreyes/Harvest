import logging
import os
from datetime import datetime 

class Logger:
    def __init__(self, crypto):
        self.logger = logging.getLogger(crypto)
        self.logger.setLevel(logging.DEBUG)

        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs/' + crypto + '/')
        log_filename = datetime.now().strftime(f"{log_dir}{crypto}-%Y-%m-%d.0.log")
        if not os.path.exists(log_dir): os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_filename)
        file_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)