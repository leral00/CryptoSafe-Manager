import sqlite3
import threading
from .models import (
    VAULT_TABLE, VAULT_INDEX,
    AUDIT_TABLE, AUDIT_INDEX,
    SETTINGS_TABLE, SETTINGS_INDEX,
    KEY_STORE_TABLE
)
class Database:
    def __init__(self, db_path="vault.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False
        )
        self.create_tables()
    def create_tables(self):
        with self.lock:
            cursor = self.conn.cursor()

            cursor.execute(VAULT_TABLE)
            cursor.execute(VAULT_INDEX)

            cursor.execute(AUDIT_TABLE)
            cursor.execute(AUDIT_INDEX)

            cursor.execute(SETTINGS_TABLE)
            cursor.execute(SETTINGS_INDEX)

            cursor.execute(KEY_STORE_TABLE)

            cursor.execute("PRAGMA user_version = 1;")

            self.conn.commit()
    def add_entry(self, title, username, encrypted_password,
                  url="", notes="", created_at="",
                  updated_at="", tags=""):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO vault_entries
                (title, username, encrypted_password,
                 url, notes, created_at, updated_at, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title, username, encrypted_password,
                url, notes, created_at, updated_at, tags
            ))
            self.conn.commit()
    def get_entries(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, title, username
                FROM vault_entries
            """)
            return cursor.fetchall()
    def get_version(self):
        with self.lock:
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA user_version;")
            return cursor.fetchone()[0]
    def close(self):
        self.conn.close()
