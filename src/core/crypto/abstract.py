from abc import ABC, abstractmethod
class EncryptionService(ABC):
    def __init__(self, key_manager):
        self.key_manager = key_manager

    @abstractmethod
    def encrypt(self, data: bytes, key_id: str) -> bytes:
        pass

    @abstractmethod
    def decrypt(self, ciphertext: bytes, key_id: str) -> bytes:
        pass
