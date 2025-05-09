import mysql.connector
import configparser

class Database:
    def __init__(self):

        config = configparser.ConfigParser()
        config.read('./config.ini')
        self.hostname = config['database']['host']
        self.user= config['database']['user']
        self.password= config['database']['password']
        self.database= config['database']['database']
        self.port = config['database']['port']
        self.conn = None


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

    
    def saveDB(self, table, columns, values):
        if self.conn is None or not self.conn.is_connected():
            self.connectDB()
        if self.conn is None:
            raise ConnectionError("Failed to connect to database.")

        placeholders = ", ".join(["%s"] * len(values))
        insert_query = f"""INSERT INTO {table} {columns} VALUES ({placeholders})"""
        cur = self.conn.cursor()

        cur.execute(insert_query, values)
        self.conn.commit()


    def closeDB(self):
        if self.conn is not None or self.conn.is_connected():
            self.conn.close()

