import sqlite3
import os
from .models import ALL_SCHEMAS

class DatabaseHelper:
    def __init__(self, db_path):
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
        return self.connection

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def initialize_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("PRAGMA user_version")
        version = cursor.fetchone()[0]

        if version == 0:
            print(f"[DB] Создание схемы базы данных...")
            for schema in ALL_SCHEMAS:
                cursor.execute(schema)
            cursor.execute("PRAGMA user_version = 1")
            conn.commit()
            print(f"[DB] База данных успешно инициализирована: {self.db_path}")
        else:
            print(f"[DB] База данных найдена (версия {version})")

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

    def backup_db(self, backup_path):
        print(f"[STUB] Backup called. Target: {backup_path}")
        pass

    def restore_db(self, restore_path):
        print(f"[STUB] Restore called. Source: {restore_path}")
        pass
