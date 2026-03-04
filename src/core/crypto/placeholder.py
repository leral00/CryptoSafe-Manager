from .abstract import EncryptionService
import hashlib
class AES256Placeholder(EncryptionService):
    def encrypt(self, data: bytes, key: bytes) -> bytes:
        if not key: return data
        key_repeated = (key * ((len(data) // len(key)) + 1))[:len(data)]
        return bytes([b ^ k for b, k in zip(data, key_repeated)])

    def decrypt(self, ciphertext: bytes, key: bytes) -> bytes:
        return self.encrypt(ciphertext, key)
class SimpleKDF:

    def derive(self, password: str, salt: bytes) -> bytes:
        if not password or not salt:
            raise ValueError("Password and salt required")
        temp_data = password.encode('utf-8') + salt
        return hashlib.sha256(temp_data).digest()
