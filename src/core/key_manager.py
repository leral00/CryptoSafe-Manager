import os
import ctypes
from src.core.crypto.placeholder import SimpleKDF

class KeyManager:
    def __init__(self):
        self._current_key = None
        self._kdf = SimpleKDF()

    def generate_salt(self) -> bytes:
        return os.urandom(16)

    def derive_key(self, password: str, salt: bytes) -> bytes:
        key = self._kdf.derive(password, salt)
        return key

    def store_key(self, key: bytes):
        self._current_key = key

    def load_key(self) -> bytes:
        return self._current_key

    def secure_zero(self, data):
        if data is None:
            return
        try:
            if isinstance(data, bytearray):
                buffer = (ctypes.c_char * len(data)).from_buffer(data)
                ctypes.memset(buffer, 0, len(data))
            elif isinstance(data, bytes):
                mutable_copy = bytearray(data)
                self.secure_zero(mutable_copy)
        except Exception:
            pass
