import sqlite3
import os
import base64
from datetime import datetime
from typing import List, Dict, Optional
from .models import VaultEntry

class DatabaseHelper:
    def __init__(self, db_path: str = "cryptosafe.db"):
        self.db_path = os.path.abspath(db_path)
        self.connection = None

        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
            except OSError as e:
                print(f"Ошибка создания директории: {e}")

    def get_connection(self):
        if not self.connection:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.execute("PRAGMA foreign_keys = ON")
            self.connection.row_factory = sqlite3.Row
        return self.connection

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def initialize_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        print("[DB] Initializing database with migration system...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
        """)

        cursor.execute("SELECT MAX(version) FROM schema_migrations")
        row = cursor.fetchone()
        current_version = row[0] if row and row[0] is not None else 0

        migrations = self._get_migrations()

        for version, sql_script in migrations.items():
            if version > current_version:
                try:
                    print(f"[DB] Applying migration version {version}...")
                    cursor.executescript(sql_script)

                    cursor.execute(
                        "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                        (version, datetime.now().isoformat())
                    )
                    conn.commit()
                    print(f"[DB] Migration {version} applied successfully.")
                except sqlite3.Error as e:
                    conn.rollback()
                    print(f"[DB ERROR] Migration {version} failed: {e}")
                    raise e

        print("[DB] Database is up to date.")

    def _get_migrations(self) -> Dict[int, str]:
        return {
            1: """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS vault_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    username TEXT,
                    encrypted_password TEXT,
                    url TEXT,
                    notes TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    tags TEXT
                );
            """,

            2: """
                CREATE TABLE IF NOT EXISTS key_store (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_type TEXT UNIQUE NOT NULL,
                    key_data BLOB NOT NULL,
                    version INTEGER NOT NULL,
                    created_at TEXT
                );
            """,

            3: """
                CREATE TABLE IF NOT EXISTS settings (
                    setting_key TEXT PRIMARY KEY,
                    setting_value TEXT NOT NULL
                );

                INSERT INTO settings (setting_key, setting_value) VALUES 
                ('password_min_length', '12'),
                ('password_policy_mixed', 'true'),
                ('key_iterations', '100000'),
                ('auto_lock_timeout', '3600');
            """,

            4: """
                ALTER TABLE users ADD COLUMN mfa_secret TEXT;
            """
        }

    def execute(self, query, params=()):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            print(f"[DB ERROR] Ошибка выполнения запроса: {e}")
            conn.rollback()
            raise e

    def fetchall(self, query, params=()):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def fetchone(self, query, params=()):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()

    def get_setting(self, key: str, default=None):
        try:
            row = self.fetchone("SELECT setting_value FROM settings WHERE setting_key = ?", (key,))
            if row:
                return row['setting_value']
            return default
        except Exception as e:
            print(f"[DB] Error getting setting {key}: {e}")
            return default

    def set_setting(self, key: str, value: str):
        try:
            self.execute(
                "INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES (?, ?)",
                (key, str(value))
            )
        except Exception as e:
            print(f"[DB] Error setting {key}: {e}")

    def add_entry(self, entry: VaultEntry) -> int:
        created_at = entry.created_at.isoformat() if entry.created_at else datetime.now().isoformat()
        updated_at = entry.updated_at.isoformat() if entry.updated_at else datetime.now().isoformat()

        pass_data = entry.encrypted_password
        if isinstance(pass_data, bytes):
            pass_str = base64.b64encode(pass_data).decode('utf-8')
        else:
            pass_str = pass_data

        cursor = self.execute("""
          INSERT INTO vault_entries 
          (title, username, encrypted_password, url, notes, created_at, updated_at, tags)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.title, entry.username, pass_str, entry.url,
            entry.notes, created_at, updated_at, entry.tags
        ))
        return cursor.lastrowid

    def delete_entry(self, entry_id: int):
        self.execute("DELETE FROM vault_entries WHERE id = ?", (entry_id,))
