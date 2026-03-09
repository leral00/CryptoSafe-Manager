import sqlite3
import os
import base64
from datetime import datetime
from typing import Optional, List
from contextlib import contextmanager
from .models import ALL_SCHEMAS, VaultEntry

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
            # Включаем поддержку Foreign Keys (если нужно)
            self.connection.execute("PRAGMA foreign_keys = ON")
            # Нужно для доступа к колонкам по имени (через dict(row))
            self.connection.row_factory = sqlite3.Row
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

    def add_entry(self, entry: VaultEntry) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        created_at = entry.created_at.isoformat() if entry.created_at else datetime.now().isoformat()
        updated_at = entry.updated_at.isoformat() if entry.updated_at else datetime.now().isoformat()

        pass_str = base64.b64encode(entry.encrypted_password).decode('utf-8')

        cursor.execute("""
          INSERT INTO vault_entries 
          (title, username, encrypted_password, url, notes, created_at, updated_at, tags)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
          entry.title, 
          entry.username, 
          pass_str, # Сохраняем строку
          entry.url, 
          entry.notes, 
          created_at, 
          updated_at, 
          entry.tags
        ))
        conn.commit()
        return cursor.lastrowid

    def get_entry(self, entry_id: int) -> Optional[VaultEntry]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM vault_entries WHERE id = ?",
            (entry_id,)
        )
        row = cursor.fetchone()
        if row:
            data = dict(row)

            if data.get('encrypted_password'):
                try:
                    data['encrypted_password'] = base64.b64decode(data['encrypted_password'])
                except Exception:
                    pass # Если там не base64, оставляем как есть

            if data.get('created_at'):
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            if data.get('updated_at'):
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
            return VaultEntry(**data)
        return None

    def get_all_entries(self) -> List[VaultEntry]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vault_entries ORDER BY updated_at DESC")
        
        entries = []
        for row in cursor.fetchall():
            data = dict(row)

            if data.get('encrypted_password'):
                try:
                    data['encrypted_password'] = base64.b64decode(data['encrypted_password'])
                except Exception:
                    pass

            if data.get('created_at'):
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            if data.get('updated_at'):
                data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            
            entries.append(VaultEntry(**data))
        return entries

    def update_entry(self, entry: VaultEntry):
        if entry.id is None:
            raise ValueError("ID не может быть None")
        
        entry.updated_at = datetime.now()
        conn = self.get_connection()
        cursor = conn.cursor()

        pass_str = base64.b64encode(entry.encrypted_password).decode('utf-8')
        time_str = entry.updated_at.isoformat()

        cursor.execute("""
            UPDATE vault_entries 
            SET title=?, username=?, encrypted_password=?, url=?, 
                notes=?, updated_at=?, tags=?
            WHERE id=?
        """, (entry.title, entry.username, pass_str,
              entry.url, entry.notes, time_str, entry.tags, entry.id))
        conn.commit()

    def delete_entry(self, entry_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vault_entries WHERE id = ?", (entry_id,))
        conn.commit()

    def backup_db(self, backup_path):
        print(f"[STUB] Backup called. Target: {backup_path}")
        pass

    def restore_db(self, restore_path):
        print(f"[STUB] Restore called. Source: {restore_path}")
        pass
