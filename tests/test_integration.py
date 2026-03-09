import sys
import os
import base64

sys.path.insert(0, '.')
from src.database.db import DatabaseHelper
from src.core.key_manager import KeyManager

TEST_DB = "test_integration.db"

def setup_function():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def teardown_function():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_first_run_setup_flow():
    assert not os.path.exists(TEST_DB)

    db = DatabaseHelper(TEST_DB)
    
    try:
        db.initialize_db()
        
        km = KeyManager()

        salt = km.generate_salt() 
        key = km.derive_key("master_password", salt)
        km.store_key(key)

        salt_str = base64.b64encode(salt).decode('utf-8')

        db.execute("INSERT INTO key_store (key_type, salt) VALUES (?, ?)", ('master', salt_str))

        assert os.path.exists(TEST_DB), "DB file should exist"
        assert km.load_key() == key, "Key should be loaded from memory"

        rows = db.fetchall("SELECT salt FROM key_store WHERE key_type='master'")
        assert len(rows) == 1, "Salt should be stored"

        assert rows[0][0] == salt_str
        
    finally:
        db.close()

def test_main_window_imports():
    try:
        from src.gui.main_window import MainWindow
        from src.gui.widgets.password_entry import PasswordEntry
        from src.gui.widgets.secure_table import SecureTable
        assert True
    except ImportError as e:
        assert False, f"Failed to import GUI components: {e}"
