import sqlite3
from .models import ALL_SCHEMAS

class DatabaseHelper:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None

    def get_connection(self):
        if not self.connection:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        return self.connection

    def initialize_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA user_version")
        version = cursor.fetchone()[0]
        
        if version == 0:
            for schema in ALL_SCHEMAS:
                cursor.execute(schema)
            cursor.execute("PRAGMA user_version = 1")
            conn.commit()
            print("Database initialized (Version 1)")

    def execute(self, query, params=()):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor

    def fetchall(self, query, params=()):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
