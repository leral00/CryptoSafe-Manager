import sys
import os
import json

sys.path.insert(0, '.')
from src.database.db import DatabaseHelper
from src.core.crypto.key_storage import KeyManager
from src.core.crypto.key_derivation import KeyDerivator
from src.core.crypto.authentication import AuthManager
from src.core.crypto.placeholder import AES256Placeholder

TEST_DB = "test_integration_scenario.db"

def setup_function():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def teardown_function():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_full_lifecycle_scenario():
    print("\n[TEST-5] Step 1: Initializing DB and User")
    db = DatabaseHelper(TEST_DB)
    db.initialize_db()

    km = KeyManager()
    derivator = KeyDerivator()

    old_pass = "InitialPass_123!"
    username = "admin"

    auth_salt = derivator.generate_salt()
    pass_hash = derivator.derive_argon2(old_pass, auth_salt).hex()

    db.execute("INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
               (username, pass_hash, auth_salt.hex()))

    enc_salt = derivator.generate_salt(16)
    enc_key = derivator.derive_pbkdf2(old_pass, enc_salt, 100000)

    db.execute("INSERT INTO key_store (key_type, key_data, version, created_at) VALUES (?, ?, ?, ?)",
               ('enc_salt', enc_salt, 1, "2023-01-01"))
    params_data = json.dumps({'iterations': 100000}).encode('utf-8')
    db.execute("INSERT INTO key_store (key_type, key_data, version, created_at) VALUES (?, ?, ?, ?)",
               ('params', params_data, 1, "2023-01-01"))

    print("[TEST-5] Step 2: Adding Entry")
    km.set_key("master_key", enc_key)
    crypto = AES256Placeholder(km)

    secret_data = "MySecretPassword"
    encrypted_entry = crypto.encrypt(secret_data.encode(), "master_key")

    db.execute("INSERT INTO vault_entries (title, encrypted_password, created_at, updated_at) VALUES (?, ?, ?, ?)",
               ('Test Site', encrypted_entry, "2023-01-01", "2023-01-01"))

    print("[TEST-5] Step 3: Changing Password")
    new_pass = "NewSecurePass_456!"
    new_auth_salt = derivator.generate_salt()
    new_pass_hash = derivator.derive_argon2(new_pass, new_auth_salt).hex()

    new_enc_salt = derivator.generate_salt(16)
    new_enc_key = derivator.derive_pbkdf2(new_pass, new_enc_salt, 100000)

    km_new = KeyManager()
    km_new.set_key("master_key", new_enc_key)
    crypto_new = AES256Placeholder(km_new)

    row = db.fetchone("SELECT id, encrypted_password FROM vault_entries WHERE title='Test Site'")
    old_cipher = row['encrypted_password']

    decrypted_data = crypto.decrypt(old_cipher, "master_key")
    assert decrypted_data.decode() == secret_data, "Data must be correct before re-encryption"

    new_cipher = crypto_new.encrypt(decrypted_data, "master_key")

    db.execute("UPDATE vault_entries SET encrypted_password = ? WHERE id = ?", (new_cipher, row['id']))

    db.execute("UPDATE users SET password_hash = ?, salt = ? WHERE username = ?",
               (new_pass_hash, new_auth_salt.hex(), username))

    db.execute("UPDATE key_store SET key_data = ? WHERE key_type = 'enc_salt'", (new_enc_salt,))

    print("[TEST-5] Step 4: Verifying Access")

    km_check = KeyManager()
    auth_check = AuthManager(db, km_check)

    assert not auth_check.login(username, old_pass), "Old password should not work"

    assert auth_check.login(username, new_pass), "New password should work"

    crypto_check = AES256Placeholder(km_check)
    row_check = db.fetchone("SELECT encrypted_password FROM vault_entries WHERE title='Test Site'")

    decrypted_final = crypto_check.decrypt(row_check['encrypted_password'], "master_key")
    assert decrypted_final.decode() == secret_data, "Data must be accessible with new password"

    print("[TEST-5] Scenario passed successfully")

    db.close()
