from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class VaultEntry:
    id: Optional[int] = None
    title: str = ""
    username: str = ""
    encrypted_password: bytes = b""  
    url: str = ""
    notes: str = ""
    created_at: datetime = None
    updated_at: datetime = None
    tags: str = ""

VAULT_ENTRIES_SCHEMA = """
CREATE TABLE IF NOT EXISTS vault_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    username TEXT NOT NULL,
    encrypted_password TEXT NOT NULL,  
    url TEXT,
    notes TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    tags TEXT
);
"""

KEY_STORE_SCHEMA = """
CREATE TABLE IF NOT EXISTS key_store (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_type TEXT NOT NULL,
    salt TEXT NOT NULL,                
    hash TEXT,
    params TEXT
);
"""

SETTINGS_SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT UNIQUE NOT NULL,
    setting_value TEXT,
    encrypted BOOLEAN DEFAULT 0
);
"""

AUDIT_LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    entry_id INTEGER,
    details TEXT,
    signature TEXT
);
"""

SETTINGS_INDEX_SCHEMA = """
CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(setting_key);
"""

ALL_SCHEMAS = [
    VAULT_ENTRIES_SCHEMA,
    KEY_STORE_SCHEMA,
    SETTINGS_SCHEMA,
    AUDIT_LOG_SCHEMA,
    SETTINGS_INDEX_SCHEMA  
]
