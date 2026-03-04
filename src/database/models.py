SCHEMA_VAULT_ENTRIES = """
CREATE TABLE IF NOT EXISTS vault_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    username TEXT,
    encrypted_password BLOB,
    url TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags TEXT
);
"""

SCHEMA_AUDIT_LOG = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    entry_id INTEGER,
    details TEXT,
    signature TEXT
);
"""

SCHEMA_SETTINGS = """
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT,
    encrypted INTEGER DEFAULT 0
);
"""

SCHEMA_KEY_STORE = """
CREATE TABLE IF NOT EXISTS key_store (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_type TEXT,
    salt BLOB,
    hash TEXT,
    params TEXT
);
"""

SCHEMA_INDICES = [
    "CREATE INDEX IF NOT EXISTS idx_audit_entry ON audit_log(entry_id);",
    "CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(setting_key);"
]

ALL_SCHEMAS = [SCHEMA_VAULT_ENTRIES, SCHEMA_AUDIT_LOG, SCHEMA_SETTINGS, SCHEMA_KEY_STORE] + SCHEMA_INDICES
