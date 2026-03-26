import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import os
import time
import threading
import queue
import sqlite3
import secrets
import json
import hashlib
import hmac
from src.core.config import ConfigManager
from src.core.events import EventBus, EventType, AuditManager
from src.core.state_manager import StateManager
from src.core.crypto.placeholder import AES256Placeholder
from src.core.crypto.key_storage import KeyManager
from src.core.crypto.authentication import AuthManager
from src.database.db import DatabaseHelper
from src.gui.widgets.password_entry import PasswordEntry
from src.gui.widgets.secure_table import SecureTable

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("CryptoSafe Manager")
        self.root.geometry("800x600")

        self.config = ConfigManager()
        self.events = EventBus()
        self.state = StateManager()

        self.key_manager = KeyManager(ttl=3600)
        self.crypto = AES256Placeholder(self.key_manager)

        self.audit_manager = None
        self.auth_manager = None
        self.db = None

        self.lockout_until = 0
        self.inactivity_limit = 3600
        self.inactivity_timer = None

        self.root.bind('<Key>', self.reset_inactivity_timer)
        self.root.bind('<Button>', self.reset_inactivity_timer)
        self.root.bind('<Unmap>', self.on_minimize)

        db_path = self.config.get('db_path', 'cryptosafe.db')
        self.root.withdraw()
        self.show_auth_dialog(db_path)

    def init_db_and_ui(self, db_path):
        try:
            self.db = DatabaseHelper(db_path)
            self.db.initialize_db()

            self.config.set_db(self.db)
            self.load_security_settings()

            self.audit_manager = AuditManager(self.events, self.db)
            self.auth_manager = AuthManager(self.db, self.key_manager)

            self.events.subscribe(EventType.USER_LOGGED_IN, self.on_login)
            self.build_ui()
            self.root.deiconify()
            self.reset_inactivity_timer()

        except Exception as e:
            messagebox.showerror("Critical Error", "Initialization failed. Check logs.")
            print(f"[INIT ERROR] {e}")
            self.root.destroy()

    def load_security_settings(self):
        try:
            timeout_val = self.config.get('auto_lock_timeout', '3600')
            self.inactivity_limit = int(timeout_val)
            self.key_manager._ttl = self.inactivity_limit
        except Exception as e:
            print(f"[Config] Error loading settings: {e}")

    def show_auth_dialog(self, db_path):
        auth_win = tk.Toplevel()
        auth_win.title("Authentication")
        auth_win.geometry("350x450")
        auth_win.protocol("WM_DELETE_WINDOW", self.root.destroy)

        is_setup = not os.path.exists(db_path)

        ttk.Label(auth_win, text="CryptoSafe Access", font=('Arial', 14, 'bold')).pack(pady=20)

        label_text = "Create Master Password:" if is_setup else "Enter Master Password:"
        ttk.Label(auth_win, text=label_text).pack(pady=5)

        pass_ent = PasswordEntry(auth_win)
        pass_ent.pack(pady=5, padx=30, fill=tk.X)

        confirm_ent = None
        if is_setup:
            ttk.Label(auth_win, text="Confirm Password:").pack(pady=5)
            confirm_ent = PasswordEntry(auth_win)
            confirm_ent.pack(pady=5, padx=30, fill=tk.X)

        status_label = ttk.Label(auth_win, text="", foreground="red")
        status_label.pack(pady=10)

        def process_auth():
            password = pass_ent.get()

            if len(password) > 1024:
                status_label.config(text="Password too long (max 1024 chars)")
                return

            if is_setup:
                confirm_pass = confirm_ent.get()
                if password != confirm_pass:
                    status_label.config(text="Passwords do not match")
                    return

                is_strong, msg = self.key_manager.derivator.check_password_strength(password)
                if not is_strong:
                    status_label.config(text=f"Weak password: {msg}")
                    return

                try:
                    self.db = DatabaseHelper(db_path)
                    self.db.initialize_db()
                    self.config.set_db(self.db)
                    self.load_security_settings()

                    auth_salt = self.key_manager.derivator.generate_salt()
                    pass_hash = self.key_manager.derivator.derive_argon2(password, auth_salt).hex()
                    self.db.execute(
                        "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                        ('admin', pass_hash, auth_salt.hex())
                    )

                    enc_salt = self.key_manager.derivator.generate_salt(16)
                    iterations = 100000
                    encryption_key = self.key_manager.derivator.derive_pbkdf2(password, enc_salt, iterations)
                    self.key_manager.set_key("master_key", encryption_key)

                    now = datetime.now().isoformat()
                    self.db.execute(
                        "INSERT INTO key_store (key_type, key_data, version, created_at) VALUES (?, ?, ?, ?)",
                        ('enc_salt', enc_salt, 1, now)
                    )
                    params_data = json.dumps({'iterations': iterations}).encode('utf-8')
                    self.db.execute(
                        "INSERT INTO key_store (key_type, key_data, version, created_at) VALUES (?, ?, ?, ?)",
                        ('params', params_data, 1, now)
                    )

                    self.config.set('db_path', db_path)

                    auth_win.destroy()
                    self.init_db_and_ui(db_path)
                    self.state.start_session('admin')
                    self.events.publish(EventType.USER_LOGGED_IN, {'user': 'admin'})

                except Exception as e:
                    print(f"[SETUP ERROR] {e}")
                    status_label.config(text="Setup failed. See logs.")

            else:
                if time.time() < self.lockout_until:
                    remaining = int(self.lockout_until - time.time())
                    status_label.config(text=f"Locked. Wait {remaining}s")
                    return

                if len(password) == 0:
                    status_label.config(text="Password required")
                    return

                temp_db = DatabaseHelper(db_path)
                temp_auth = AuthManager(temp_db, self.key_manager)

                user = temp_db.fetchone("SELECT mfa_secret FROM users WHERE username='admin'")
                requires_mfa = user and user['mfa_secret']

                login_success = False

                if requires_mfa:
                    mfa_code = simpledialog.askstring("Two-Factor Auth", "Enter Google Authenticator Code:",
                                                      parent=auth_win)
                    if mfa_code:
                        if temp_auth.login("admin", password, mfa_code=mfa_code):
                            login_success = True
                else:
                    if temp_auth.login("admin", password):
                        login_success = True

                if login_success:
                    self.state.reset_failed_attempts()
                    temp_db.close()
                    auth_win.destroy()
                    self.init_db_and_ui(db_path)
                    self.state.start_session('admin')
                    self.events.publish(EventType.USER_LOGGED_IN, {'user': 'admin'})
                else:
                    temp_db.close()
                    self.state.record_failed_attempt()
                    fails = self.state.get_failed_attempts()
                    delay = 30 if fails >= 5 else (5 if fails >= 3 else 1)
                    self.lockout_until = time.time() + delay
                    status_label.config(text=f"Invalid credentials. Locked for {delay}s")

        btn_text = "Create Vault" if is_setup else "Unlock"
        ttk.Button(auth_win, text=btn_text, command=process_auth).pack(pady=20)

    def build_ui(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Lock Session", command=self.lock_app)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Add Entry", command=self.add_entry_dialog)
        edit_menu.add_command(label="Delete Selected", command=self.delete_selected_entry)
        edit_menu.add_separator()
        edit_menu.add_command(label="Change Master Password", command=self.show_change_password_dialog)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        self.root.config(menu=menubar)

        self.table = SecureTable(self.root)
        self.table.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.load_data()

    def on_login(self, data):
        self.update_status_bar(f"Logged in as {data.get('user')}")

    def update_status_bar(self, text):
        info = self.state.get_session_info()
        if info.get('login_time'):
            time_str = info['login_time'].strftime("%H:%M")
            text += f" | Session: {time_str}"
        self.status_bar.config(text=text)

    def reset_inactivity_timer(self, event=None):
        self.state.update_activity()
        if self.inactivity_timer:
            try:
                self.root.after_cancel(self.inactivity_timer)
            except:
                pass
        self.inactivity_timer = self.root.after(self.inactivity_limit * 1000, self.lock_app)

    def on_minimize(self, event):
        if event.widget == self.root:
            self.lock_app()

    def lock_app(self):
        if self.inactivity_timer:
            try:
                self.root.after_cancel(self.inactivity_timer)
            except:
                pass

        self.key_manager.clear_cache()

        if hasattr(self, 'table'):
            for item in self.table.get_children():
                self.table.delete(item)

        self.root.withdraw()
        db_path = self.config.get('db_path')
        if db_path:
            self.show_auth_dialog(db_path)

    def load_data(self):
        for item in self.table.get_children():
            self.table.delete(item)
        if self.db:
            rows = self.db.fetchall("SELECT id, title, username FROM vault_entries")
            for row in rows:
                self.table.insert("", tk.END, values=(row['id'], row['title'], row['username']))

    def add_entry_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Entry")
        dialog.geometry("300x350")

        ttk.Label(dialog, text="Title:").pack(pady=2)
        title_ent = ttk.Entry(dialog)
        title_ent.pack(pady=2)

        ttk.Label(dialog, text="Username:").pack(pady=2)
        user_ent = ttk.Entry(dialog)
        user_ent.pack(pady=2)

        ttk.Label(dialog, text="Password:").pack(pady=2)
        pass_ent = ttk.Entry(dialog, show="*")
        pass_ent.pack(pady=2)

        def save():
            title = title_ent.get()
            if not title:
                messagebox.showwarning("Warning", "Title is required")
                return
            if len(title) > 256:
                messagebox.showwarning("Warning", "Title too long")
                return

            try:
                enc_data = self.crypto.encrypt(pass_ent.get().encode(), "master_key")

                try:
                    audit_key = self.key_manager.get_audit_key()
                    sig = hmac.new(audit_key, enc_data.encode('utf-8'), hashlib.sha256).hexdigest()
                    print(f"[FUTURE-1] Entry signed: {sig[:10]}...")
                except Exception as e:
                    print(f"Could not sign entry: {e}")

                now = datetime.now().isoformat()
                self.db.execute(
                    """INSERT INTO vault_entries 
                    (title, username, encrypted_password, created_at, updated_at) 
                    VALUES (?, ?, ?, ?, ?)""",
                    (title, user_ent.get(), enc_data, now, now)
                )
                self.load_data()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", "Failed to save entry. Check logs.")
                print(f"[SAVE ENTRY ERROR] {e}")

        ttk.Button(dialog, text="Save", command=save).pack(pady=20)

    def delete_selected_entry(self):
        selected = self.table.selection()
        if not selected:
            return
        if messagebox.askyesno("Confirm", "Delete selected entry?"):
            entry_id = self.table.item(selected[0])['values'][0]
            self.db.execute("DELETE FROM vault_entries WHERE id = ?", (entry_id,))
            self.load_data()

    def show_change_password_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Rotate Master Keys")
        dialog.geometry("400x450")
        dialog.grab_set()

        ttk.Label(dialog, text="Current Password:").pack(pady=5)
        old_ent = PasswordEntry(dialog)
        old_ent.pack(pady=5, padx=20, fill=tk.X)

        ttk.Label(dialog, text="New Password:").pack(pady=5)
        new_ent = PasswordEntry(dialog)
        new_ent.pack(pady=5, padx=20, fill=tk.X)

        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(dialog, variable=progress_var, maximum=100)

        self._is_paused = False
        msg_queue = queue.Queue()

        def toggle_pause():
            self._is_paused = not self._is_paused
            pause_btn.config(text="Resume" if self._is_paused else "Pause")

        pause_btn = ttk.Button(dialog, text="Pause", command=toggle_pause, state=tk.DISABLED)

        def process_messages():
            try:
                while True:
                    msg = msg_queue.get_nowait()
                    if isinstance(msg, (int, float)):
                        progress_var.set(msg)
                    elif msg == "DONE":
                        messagebox.showinfo("Success", "Keys rotated and storage re-encrypted.")
                        dialog.destroy()
                        self.lock_app()
                    elif msg.startswith("ERROR"):
                        messagebox.showerror("Critical Error",
                                             "Operation failed due to security constraints. Check logs.")
                        dialog.destroy()
            except queue.Empty:
                if dialog.winfo_exists():
                    self.root.after(100, process_messages)

        def worker(old_p, new_p):
            conn = sqlite3.connect(self.config.get('db_path'))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            try:
                if len(old_p) > 1024 or len(new_p) > 1024:
                    raise ValueError("Invalid input length")

                cursor.execute("SELECT password_hash, salt FROM users WHERE username='admin'")
                user = cursor.fetchone()
                if not user:
                    msg_queue.put("ERROR: User not found")
                    return

                old_auth_key = self.key_manager.derivator.derive_argon2(old_p, bytes.fromhex(user['salt'])).hex()
                if not secrets.compare_digest(old_auth_key, user['password_hash']):
                    msg_queue.put("ERROR: Invalid current password")
                    return

                cursor.execute("BEGIN TRANSACTION")

                new_auth_salt = self.key_manager.derivator.generate_salt()
                new_pass_hash = self.key_manager.derivator.derive_argon2(new_p, new_auth_salt).hex()

                new_enc_salt = self.key_manager.derivator.generate_salt(16)
                iterations = 100000

                cursor.execute("SELECT key_data FROM key_store WHERE key_type='enc_salt'")
                old_salt_row = cursor.fetchone()
                cursor.execute("SELECT key_data FROM key_store WHERE key_type='params'")
                old_params_row = cursor.fetchone()

                if not old_salt_row or not old_params_row:
                    raise Exception("Key store data missing")

                old_enc_salt = old_salt_row['key_data']
                old_params = json.loads(old_params_row['key_data'].decode('utf-8'))
                old_iterations = old_params.get('iterations', 100000)

                old_key = self.key_manager.derivator.derive_pbkdf2(old_p, old_enc_salt, old_iterations)
                new_key = self.key_manager.derivator.derive_pbkdf2(new_p, new_enc_salt, iterations)

                old_km = KeyManager()
                old_km.set_key("tmp_old", old_key)
                old_crypto = AES256Placeholder(old_km)

                new_km = KeyManager()
                new_km.set_key("tmp_new", new_key)
                new_crypto = AES256Placeholder(new_km)

                cursor.execute("SELECT id, encrypted_password FROM vault_entries")
                rows = cursor.fetchall()
                total = len(rows)

                for i, row in enumerate(rows):
                    while self._is_paused:
                        time.sleep(0.1)

                    decrypted = old_crypto.decrypt(row['encrypted_password'], "tmp_old")
                    new_cipher = new_crypto.encrypt(decrypted, "tmp_new")

                    cursor.execute("UPDATE vault_entries SET encrypted_password = ? WHERE id = ?",
                                   (new_cipher, row['id']))

                    progress = ((i + 1) / total) * 100 if total > 0 else 100
                    msg_queue.put(progress)

                cursor.execute("UPDATE users SET password_hash=?, salt=? WHERE username='admin'",
                               (new_pass_hash, new_auth_salt.hex()))

                cursor.execute("UPDATE key_store SET key_data=?, version=version+1 WHERE key_type='enc_salt'",
                               (new_enc_salt,))

                params_data = json.dumps({'iterations': iterations}).encode('utf-8')
                cursor.execute("UPDATE key_store SET key_data=?, version=version+1 WHERE key_type='params'",
                               (params_data,))

                conn.commit()
                msg_queue.put("DONE")

            except Exception as e:
                conn.rollback()
                print(f"[SEC-2] Critical error during rotation: {type(e).__name__}")
                msg_queue.put("ERROR: Operation failed due to security constraints.")
            finally:
                conn.close()

        def start():
            new_pass = new_ent.get()
            is_strong, msg = self.key_manager.derivator.check_password_strength(new_pass)
            if not is_strong:
                messagebox.showwarning("Weak Password", msg)
                return

            pause_btn.config(state=tk.NORMAL)
            progress_bar.pack(pady=20, padx=20, fill=tk.X)
            threading.Thread(target=worker, args=(old_ent.get(), new_pass), daemon=True).start()
            process_messages()

        ttk.Button(dialog, text="Start Re-encryption", command=start).pack(pady=10)
        pause_btn.pack(pady=5)
