from src.core.crypto.abstract import EncryptionService
class AES256Placeholder(EncryptionService):
    def encrypt(self, data: bytes, key_id: str) -> bytes:
        key = self.key_manager.get_key(key_id)

        if not key:
            raise ValueError(f"Ключ с ID {key_id} не найден в KeyManager")
        key_repeated = (key * ((len(data) // len(key)) + 1))[:len(data)]
        return bytes([b ^ k for b, k in zip(data, key_repeated)])

    def decrypt(self, ciphertext: bytes, key_id: str) -> bytes:
        return self.encrypt(ciphertext, key_id)
