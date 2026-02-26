from .abstract import EncryptionService


class AES256Placeholder(EncryptionService):
    """
    Заглушка вместо настоящего AES.
    Использует XOR.
    """

    def __init__(self, key: bytes):
        self.key = key

    def _xor(self, data: bytes) -> bytes:
        return bytes(
            [b ^ self.key[i % len(self.key)] for i, b in enumerate(data)]
        )

    def encrypt(self, data: bytes) -> bytes:
        return self._xor(data)

    def decrypt(self, data: bytes) -> bytes:
        return self._xor(data)
