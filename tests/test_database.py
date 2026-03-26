import sys
import os

sys.path.insert(0, '.')
from src.database.db import DatabaseHelper
from src.core.config import ConfigManager

TEST_DB = "test_cryptosafe.db"

def setup_function():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def teardown_function():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_db_initialization():
    db = DatabaseHelper(TEST_DB)
    try:
        db.initialize_db()
        result = db.fetchall("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
        assert len(result) == 1, "Migration table should exist"

        result = db.fetchall("SELECT name FROM sqlite_master WHERE type='table' AND name='vault_entries'")
        assert len(result) == 1, "Vault table should exist"
    finally:
        db.close()

def test_db_indices():
    db = DatabaseHelper(TEST_DB)
    try:
        db.initialize_db()
        result = db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in result]
        assert 'vault_entries' in tables
        assert 'users' in tables
    finally:
        db.close()

def test_config_loading():
    db = DatabaseHelper(TEST_DB)
    try:
        db.initialize_db()

        db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT
            )
        """)

        config = ConfigManager()
        config.set_db(db)
        config.set('test_setting', '123')

        result = db.fetchall("SELECT setting_value FROM settings WHERE setting_key='test_setting'")
        assert len(result) == 1
        assert result[0][0] == '123'
    finally:
        db.close()
