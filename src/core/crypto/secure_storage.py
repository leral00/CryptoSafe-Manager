import keyring
import json
import os
from pathlib import Path

class SecureStorage:
    SERVICE_NAME = "CryptoSafeApp"

    def __init__(self):
        try:
            self._keyring_available = keyring.get_keyring() is not None
        except:
            self._keyring_available = False

        self.fallback_path = Path.home() / ".cryptosafe_fallback.json"

    def store_secret(self, key, value):
        if self._keyring_available:
            try:
                keyring.set_password(self.SERVICE_NAME, key, value)
                return
            except:
                pass

        data = self._load_fallback()
        data[key] = value
        with open(self.fallback_path, 'w') as f:
            json.dump(data, f)
        os.chmod(self.fallback_path, 0o600)

    def _load_fallback(self):
        if not self.fallback_path.exists(): return {}
        with open(self.fallback_path, 'r') as f:
            return json.load(f)
