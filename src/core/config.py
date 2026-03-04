import os

class ConfigManager:
    def __init__(self):
        self.settings = {
            'db_path': 'cryptosafe.db',
            'clipboard_timeout': 30,
            'auto_lock_timeout': 300
        }
        self.db = None

    def set_db(self, db_helper):
        self.db = db_helper
        self.load_from_db()
    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        if self.db:
            try:
                val_str = str(value)
                self.db.execute(
                    "INSERT OR REPLACE INTO settings (setting_key, setting_value) VALUES (?, ?)",
                    (key, val_str)
                )
            except Exception as e:
                print(f"[ConfigManager] Error saving setting '{key}': {e}")

    def load_from_db(self):
        if not self.db:
            return
        try:
            rows = self.db.fetchall("SELECT setting_key, setting_value FROM settings")
            for key, value in rows:
                if value.isdigit():
                    value = int(value)
                self.settings[key] = value
        except Exception as e:
            print(f"[ConfigManager] Error loading settings: {e}")
