VAULT_TABLE = """
CREATE TABLE IF NOT EXISTS vault_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    username TEXT NOT NULL,
    encrypted_password BLOB NOT NULL,
    url TEXT,
    notes TEXT,
    created_at TEXT,
    updated_at TEXT,
    tags TEXT
);
"""

VAULT_INDEX = """
CREATE INDEX IF NOT EXISTS idx_vault_title
ON vault_entries(title);
"""

AUDIT_TABLE = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    entry_id INTEGER,
    details TEXT,
    signature TEXT
);
"""

AUDIT_INDEX = """
CREATE INDEX IF NOT EXISTS idx_audit_timestamp
ON audit_log(timestamp);
"""

SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT UNIQUE,
    setting_value TEXT,
    encrypted INTEGER DEFAULT 0
);
"""

SETTINGS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_settings_key
ON settings(setting_key);
"""

KEY_STORE_TABLE = """
CREATE TABLE IF NOT EXISTS key_store (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_type TEXT,
    salt BLOB,
    hash BLOB,
    params TEXT
);
"""
