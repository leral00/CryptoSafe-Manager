import unittest
from src.core.crypto.placeholder import AES256Placeholder

class TestCrypto(unittest.TestCase):

    def test_encrypt(self):
        crypto = AES256Placeholder(b"key")
        text = b"hello"
        encrypted = crypto.encrypt(text)
        decrypted = crypto.decrypt(encrypted)
        self.assertEqual(text, decrypted)


if __name__ == "__main__":
    unittest.main()
