import secrets
import json
import hmac
import hashlib
import time
import os
from src.core.crypto.key_derivation import KeyDerivator
class AuthManager:
    def __init__(self, db_helper, key_manager):
        self.db = db_helper
        self.key_manager = key_manager
        self.derivator = KeyDerivator()

    def _verify_totp(self, secret: str, code: str) -> bool:
        if not secret or not code: return False
        try:
            timestep = int(time.time() // 30)
            try:
                key = bytes.fromhex(secret)
            except ValueError:
                key = secret.encode('utf-8')
            msg = timestep.to_bytes(8, 'big')
            h = hmac.new(key, msg, hashlib.sha1).digest()
            offset = h[-1] & 0x0f
            code_binary = (h[offset] & 0x7f) << 24 | (h[offset + 1] & 0xff) << 16 | (h[offset + 2] & 0xff) << 8 | (
                        h[offset + 3] & 0xff)
            expected_code = str(code_binary % 10 ** 6).zfill(6)
            return secrets.compare_digest(code, expected_code)
        except Exception:
            return False

    def login(self, username, password, mfa_code=None):
        if not username or not password:
            return False
        if len(username) > 128 or len(password) > 1024:
            return False

        user = self.db.fetchone("SELECT password_hash, salt, mfa_secret FROM users WHERE username=?", (username,))
        if not user:
            self.derivator.derive_argon2("dummy_password", os.urandom(16))
            return False

        try:
            auth_key = self.derivator.derive_argon2(password, bytes.fromhex(user['salt']))

            if not secrets.compare_digest(auth_key.hex(), user['password_hash']):
                return False

            if user['mfa_secret']:
                if not mfa_code or not self._verify_totp(user['mfa_secret'], mfa_code):
                    return False

            salt_row = self.db.fetchone("SELECT key_data FROM key_store WHERE key_type='enc_salt'")
            params_row = self.db.fetchone("SELECT key_data FROM key_store WHERE key_type='params'")

            if salt_row and params_row:
                enc_salt = salt_row['key_data']
                try:
                    params = json.loads(params_row['key_data'].decode('utf-8'))
                    iterations = params.get('iterations', 100000)
                except:
                    iterations = 100000

                encryption_key = self.derivator.derive_pbkdf2(password, enc_salt, iterations)
                self.key_manager.set_key("master_key", encryption_key)
                return True

        except Exception as e:
            print("[AUTH] Error during login process.")
            return False

        return False
