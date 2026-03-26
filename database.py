
import psycopg


DB_CONFIG = {
    "host": "localhost",
    "port": 9876,
    "dbname": "lego-db",
    "user": "lego",
    "password": "bricks",
}

#Data base class
class Database:
    def __init__(self):
        #Connection
        self.connect = psycopg.connect(**DB_CONFIG)
        #Cursor created with connection
        self.cursor = self.connect.cursor()

    #Method for fetching all object with given query
    def execute_and_fetch_all(self, query, vars=None):
        #Perform query
        self.cursor.execute(query, vars)
        #Save result and return
        query_result = self.cursor.fetchall()
        return query_result
        

    #Method for closing connection
    def close(self):
        #Close the connection and cursor
        self.cursor.close()
        self.connect.close()
