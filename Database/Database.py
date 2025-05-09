import mysql.connector
import configparser
from Logging.Logger import Logger

class Database:
    def __init__(self, crypto):

        config = configparser.ConfigParser()
        config.read('Database/config.ini')
        self.hostname = config['database']['host']
        self.user= config['database']['user']
        self.password= config['database']['password']
        self.database= config['database']['db']
        self.port = config['database']['port']
        self.conn = None
        self.logger = Logger(crypto)


    def connectDB(self):
        self.conn = mysql.connector.connect(
            host=self.hostname,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database
        )


    def retrieveData(self, query):
        if self.conn is None or not self.conn.is_connected():
            self.connectDB()
        if self.conn is None:
            print("Failed to connect to database.")
            return    
        
        cur = self.conn.cursor()
        cur.execute(query)

        return cur.fetchall()

    
    def saveDB(self, type, table, columns, values):
        if self.conn is None or not self.conn.is_connected():
            self.connectDB()
        if self.conn is None:
            raise ConnectionError("Failed to connect to database.")

        placeholders = ", ".join(["%s"] * len(values))
        insert_query = f"""INSERT INTO {table} {columns} VALUES ({placeholders})"""

        cur = self.conn.cursor()
        cur.execute(insert_query, values)
        self.conn.commit()

        self.logger.info(type + " Saved to Database : " + str(values))
        return cur.lastrowid


    def closeDB(self):
        if self.conn is not None or self.conn.is_connected():
            self.conn.close()

