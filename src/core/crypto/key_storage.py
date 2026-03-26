import time
import ctypes
import secrets
import hashlib
from typing import Optional
from src.core.crypto.key_derivation import KeyDerivator

class KeyManager:
    def __init__(self, ttl: int = 300):
        self._key_cache = {}
        self._ttl = ttl
        self.derivator = KeyDerivator()

        self._session_key = secrets.token_bytes(32)
        self._is_locked = False

    def _secure_wipe(self, buffer: bytearray):
        if buffer and len(buffer) > 0:
            ctypes.memset(ctypes.c_char.from_buffer(buffer), 0, len(buffer))

    def _encrypt_for_cache(self, data: bytes) -> bytearray:
        mask = self._session_key
        encrypted = bytearray(len(data))
        for i in range(len(data)):
            encrypted[i] = data[i] ^ mask[i % len(mask)]
        return encrypted

    def _decrypt_from_cache(self, data: bytearray) -> bytes:
        mask = self._session_key
        decrypted = bytearray(len(data))
        for i in range(len(data)):
            decrypted[i] = data[i] ^ mask[i % len(mask)]
        return bytes(decrypted)

    def derive_functional_key(self, purpose: str) -> bytes:
        master_key = self.get_key("master_key")
        if not master_key:
            raise PermissionError("Master key not available. User not logged in.")

        h = hashlib.sha256()
        h.update(master_key)
        h.update(purpose.encode('utf-8'))
        return h.digest()

    def get_audit_key(self) -> bytes:
        return self.derive_functional_key("audit_log_encryption_key_v1")

    def get_totp_encryption_key(self) -> bytes:
        return self.derive_functional_key("totp_secrets_encryption_key_v1")

    def get_export_key(self) -> bytes:
        return self.derive_functional_key("secure_export_key_v1")

    def derive_and_store_key(self, key_id: str, password: str, salt: bytes, time_cost: int = 3,
                             memory_cost: int = 65536, parallelism: int = 4) -> bytes:
        if not salt:
            raise ValueError("Для деривации ключа необходима соль")

        key_bytes = self.derivator.derive_argon2(password, salt, time_cost, memory_cost, parallelism)
        self.set_key(key_id, key_bytes)
        return key_bytes

    def set_key(self, key_id: str, key_bytes: bytes):
        encrypted_key = self._encrypt_for_cache(key_bytes)

        self._key_cache[key_id] = {
            "key": encrypted_key,
            "expires": time.time() + self._ttl
        }
        self._is_locked = False

    def get_key(self, key_id: str) -> Optional[bytes]:
        if self._is_locked:
            return None

        entry = self._key_cache.get(key_id)
        if not entry:
            return None

        if time.time() > entry["expires"]:
            self._secure_wipe(entry["key"])
            del self._key_cache[key_id]
            return None

        return self._decrypt_from_cache(entry["key"])

    def clear_cache(self):
        print(f"[FUTURE-3] Clearing {len(self._key_cache)} keys from memory.")
        for key_id in list(self._key_cache.keys()):
            entry = self._key_cache[key_id]
            self._secure_wipe(entry["key"])

        self._key_cache.clear()
        self._is_locked = True
