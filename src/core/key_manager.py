import hashlib
import secrets
import sqlite3
import ctypes

class KeyManager:
    def __init__(self, db_path="vault.db"):
        self.db_path = db_path
    def derive_key(self, password: str, salt: bytes) -> bytes:
        """
        Простая заглушка.
        В Спринте 2 будет PBKDF2.
        """
        data = password.encode() + salt
        key = hashlib.sha256(data).digest()

        mutable = bytearray(data)
        ptr = (ctypes.c_char * len(mutable)).from_buffer(mutable)
        ctypes.memset(ptr, 0, len(mutable))

        return key

    def store_key(self, key_type: str, salt: bytes, key_hash: bytes, params: str = ""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO key_store (key_type, salt, hash, params)
            VALUES (?, ?, ?, ?)
        """, (key_type, salt, key_hash, params))

        conn.commit()
        conn.close()

    def load_key(self, key_type: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT salt, hash, params
            FROM key_store
            WHERE key_type = ?
        """, (key_type,))

        result = cursor.fetchone()
        conn.close()

        return result

    def generate_salt(self, length=16) -> bytes:
        return secrets.token_bytes(length)
