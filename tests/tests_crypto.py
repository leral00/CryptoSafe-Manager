import sys
import time
import secrets

sys.path.insert(0, '.')
from src.core.crypto.key_derivation import KeyDerivator
from src.core.crypto.key_storage import KeyManager

def test_argon2_parameters_validation():
    derivator = KeyDerivator()
    password = "test_password"
    salt = derivator.generate_salt()

    hash1 = derivator.derive_argon2(password, salt)
    assert len(hash1) == 32, "Hash length must be 32 bytes"

    hash2 = derivator.derive_argon2(password, salt, time_cost=1, memory_cost=32768)
    assert len(hash2) == 32, "Hash length must be 32 bytes with custom params"
    assert hash1 == derivator.derive_argon2(password, salt, time_cost=3, memory_cost=65536)

def test_key_format_consistency():
    derivator = KeyDerivator()
    password = "StrongPass_123!"
    salt = derivator.generate_salt()

    key_pbkdf2 = derivator.derive_pbkdf2(password, salt)
    assert len(key_pbkdf2) == 32, "PBKDF2 key must be 32 bytes (KEY-2)"

    key_argon = derivator.derive_argon2(password, salt)
    assert len(key_argon) == 32, "Argon2 key must be 32 bytes"

    assert isinstance(key_pbkdf2, bytes)
    assert isinstance(key_argon, bytes)

def test_timing_attack_resistance():
    derivator = KeyDerivator()
    salt = derivator.generate_salt()

    correct_pass = "CorrectPassword123!"
    stored_hash = derivator.derive_argon2(correct_pass, salt).hex()

    pass_wrong_1 = "WrongPassword123!"
    pass_wrong_2 = "CorrectPassword124!"  

    def verify(pwd):
        derived = derivator.derive_argon2(pwd, salt).hex()
        return secrets.compare_digest(derived, stored_hash)

    verify(pass_wrong_1)
    verify(pass_wrong_2)

    def measure(pwd):
        start = time.perf_counter()
        verify(pwd)
        return time.perf_counter() - start

    times_1 = [measure(pass_wrong_1) for _ in range(5)]
    times_2 = [measure(pass_wrong_2) for _ in range(5)]

    avg_1 = sum(times_1) / len(times_1)
    avg_2 = sum(times_2) / len(times_2)

    diff = abs(avg_1 - avg_2)
    threshold = max(avg_1, avg_2) * 0.5  

    print(f"[TEST-3] Time Wrong1: {avg_1:.6f}, Time Wrong2: {avg_2:.6f}, Diff: {diff:.6f}")
    assert diff < threshold, "Comparison time varies significantly, potential timing attack vector"
    assert verify(pass_wrong_1) is False
    assert verify(pass_wrong_2) is False

def test_memory_security():
    km = KeyManager(ttl=10)
    derivator = KeyDerivator()

    key = derivator.derive_pbkdf2("pass", b"salt_12345678")

    km.set_key("master_key", key)
    assert km.get_key("master_key") is not None

    km.clear_cache()

    assert km.get_key("master_key") is None, "Key must be cleared from memory (CACHE-4)"
