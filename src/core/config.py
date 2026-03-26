class ConfigManager:
    def __init__(self):
        self.db = None

        self._defaults = {
            'db_path': 'cryptosafe.db',
            'clipboard_timeout': '30',
            'auto_lock_timeout': '3600'
        }

    def set_db(self, db_helper):
        self.db = db_helper

    def get(self, key, default=None):
        if self.db:
            val = self.db.get_setting(key)
            if val is not None:
                return val

        return self._defaults.get(key, default)

    def set(self, key, value):
        if self.db:
            self.db.set_setting(key, str(value))
        else:
            print(f"[Config] Warning: Database not connected. Cannot save setting '{key}'.")
