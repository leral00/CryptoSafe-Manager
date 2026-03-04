import sys
sys.path.insert(0, '.')
from src.core.crypto.placeholder import AES256Placeholder

def test_encryption_decryption():
    service = AES256Placeholder()
    key = b'secretkey1234567'
    data = b'my_secret_data'
    
    encrypted = service.encrypt(data, key)
    decrypted = service.decrypt(encrypted, key)
    
    assert data == decrypted

def test_xor_encryption_changes_data():
    service = AES256Placeholder()
    key = b'key'
    data = b'data'
    encrypted = service.encrypt(data, key)
    assert encrypted != data
