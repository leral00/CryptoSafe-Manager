import hashlib
import os
import re
from argon2.low_level import hash_secret_raw, Type

class KeyDerivator:
    @staticmethod
    def generate_salt(size: int = 16) -> bytes:
        return os.urandom(size)
    @staticmethod
    def derive_pbkdf2(password: str, salt: bytes, iterations: int = 100000) -> bytes:
        if not password:
            raise ValueError("Пароль не может быть пустым")
        if len(password.encode('utf-8')) > 1024:
            raise ValueError("Пароль превышает допустимую длину (1024 байта)")

        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            iterations,
            dklen=32
        )

    @staticmethod
    def derive_argon2(password: str, salt: bytes, time_cost: int = 3, memory_cost: int = 65536,
                      parallelism: int = 4) -> bytes:

        if not password:
            raise ValueError("Пароль не может быть пустым")
        if len(password.encode('utf-8')) > 1024:
            raise ValueError("Пароль превышает допустимую длину (1024 байта)")

        return hash_secret_raw(
            password.encode(),
            salt,
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
            hash_len=32,
            type=Type.ID
        )

    @staticmethod
    def check_password_strength(password: str) -> tuple:
        if len(password) < 12:
            return False, "Длина пароля должна быть не менее 12 символов"

        if len(password) > 256:
            return False, "Пароль слишком длинный"

        if not re.search(r"[A-Z]", password):
            return False, "Пароль должен содержать заглавные буквы"
        if not re.search(r"[a-z]", password):
            return False, "Пароль должен содержать строчные буквы"
        if not re.search(r"\d", password):
            return False, "Пароль должен содержать цифры"
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
            return False, "Пароль должен содержать специальные символы"

        weak_phrases = ['password', '123456', 'qwerty', 'admin', 'login', 'iloveyou']
        for phrase in weak_phrases:
            if phrase in password.lower():
                return False, f"Пароль содержит слабую фразу: '{phrase}'"

        return True, "OK"
