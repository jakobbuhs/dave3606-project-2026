
import os

import psycopg


# Connection settings are read from the standard PostgreSQL environment variables,
# falling back to the local Docker defaults created by create_and_run_database.sh.
# The fallback password is a throwaway, localhost-only development credential from
# the course scaffold, not a production secret. See .env.example.
DB_CONFIG = {
    "host": os.environ.get("PGHOST", "localhost"),
    "port": int(os.environ.get("PGPORT", "9876")),
    "dbname": os.environ.get("PGDATABASE", "lego-db"),
    "user": os.environ.get("PGUSER", "lego"),
    "password": os.environ.get("PGPASSWORD", "bricks"),
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
