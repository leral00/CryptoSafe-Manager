import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from src.core.config import ConfigManager
from src.core.events import EventBus, EventType, AuditManager
from src.core.state_manager import StateManager
from src.core.crypto.placeholder import AES256Placeholder
from src.core.key_manager import KeyManager
from src.database.db import DatabaseHelper
from .widgets.password_entry import PasswordEntry
from .widgets.secure_table import SecureTable
import os

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("CryptoSafe Manager")
        self.root.geometry("800x600")

        self.config = ConfigManager()
        self.events = EventBus()
        self.state = StateManager()
        self.crypto = AES256Placeholder()
        self.key_manager = KeyManager()
        self.audit_manager = None

        db_path = self.config.get('db_path')

        if not os.path.exists(db_path):
            print(f"[INFO] База данных не найдена. Запуск мастера...")
            self.root.withdraw()
            self.show_setup_wizard()
        else:
            print(f"[INFO] База данных найдена. Загрузка...")
            self.init_db_and_ui(db_path)

    def init_db_and_ui(self, db_path):
        try:
            self.db = DatabaseHelper(db_path)
            self.db.initialize_db()

            self.audit_manager = AuditManager(self.events, self.db)
            self.config.set_db(self.db)

            self.events.subscribe(EventType.USER_LOGGED_IN, self.on_login)

            self.build_ui()
            self.root.deiconify()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть базу данных:\n{e}")
            self.root.destroy()

    def on_login(self, data):
        self.update_status_bar(f"Logged in as {data.get('user', 'admin')}")

    def update_status_bar(self, text):
        if hasattr(self, 'status_bar'):
            self.status_bar.config(text=text)

    def show_setup_wizard(self):
        wizard = tk.Toplevel()
        wizard.title("First Run Setup")
        wizard.geometry("450x450")
        wizard.protocol("WM_DELETE_WINDOW", self.root.destroy)

        ttk.Label(wizard, text="Database Location:").pack(pady=5)
        path_frame = ttk.Frame(wizard)
        path_frame.pack(pady=5, fill=tk.X, padx=20)
        self.wizard_db_path = tk.StringVar(value=self.config.get('db_path'))
        ttk.Entry(path_frame, textvariable=self.wizard_db_path).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="Browse", command=self.browse_db_file).pack(side=tk.RIGHT, padx=5)

        ttk.Label(wizard, text="Create Master Password").pack(pady=10)
        self.wizard_pass = PasswordEntry(wizard)
        self.wizard_pass.pack(pady=5, fill=tk.X, padx=20)

        ttk.Label(wizard, text="Confirm Password").pack(pady=10)
        self.wizard_confirm = PasswordEntry(wizard)
        self.wizard_confirm.pack(pady=5, fill=tk.X, padx=20)

        ttk.Label(wizard, text="Encryption Settings (Placeholder):").pack(pady=10)
        enc_frame = ttk.Frame(wizard)
        enc_frame.pack(pady=5, fill=tk.X, padx=20)
        ttk.Label(enc_frame, text="KDF Iterations:").pack(side=tk.LEFT)
        ttk.Entry(enc_frame, width=10).insert(0, "10000")
        ttk.Entry(enc_frame, width=10).pack(side=tk.RIGHT)

        ttk.Button(wizard, text="Create Vault", command=lambda: self.finish_setup(wizard)).pack(pady=20)
    def browse_db_file(self):
        filename = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("Database", "*.db")])
        if filename:
            self.wizard_db_path.set(filename)

    def finish_setup(self, wizard):
        p1 = self.wizard_pass.get()
        p2 = self.wizard_confirm.get()

        if not p1 or len(p1) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters")
            return
        if p1 != p2:
            messagebox.showerror("Error", "Passwords do not match")
            return

        db_path = self.wizard_db_path.get()
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        self.db = DatabaseHelper(db_path)
        self.db.initialize_db()

        self.config.set_db(self.db)
        self.config.set('db_path', db_path)

        self.audit_manager = AuditManager(self.events, self.db)

        salt = self.key_manager.generate_salt()
        key = self.key_manager.derive_key(p1, salt)
        self.key_manager.store_key(key)
        self.key_manager.secure_zero(p1.encode())

        self.db.execute("INSERT INTO key_store (key_type, salt) VALUES (?, ?)", ('master', salt))

        wizard.destroy()
        self.events.publish(EventType.USER_LOGGED_IN, {'action': 'USER_LOGGED_IN', 'user': 'admin'})
        self.init_db_and_ui(db_path)

    def build_ui(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=lambda: print("Stub: New"))
        file_menu.add_command(label="Open", command=lambda: print("Stub: Open"))
        file_menu.add_command(label="Backup", command=lambda: print("Stub: Backup"))  # DB-4 Stub
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Add Entry", command=self.add_entry_dialog)
        edit_menu.add_command(label="Edit Entry", command=lambda: print("Stub: Edit"))  # Added Edit
        edit_menu.add_command(label="Delete Entry", command=self.delete_selected_entry)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Logs", command=self.show_logs_stub)
        view_menu.add_command(label="Settings", command=self.show_settings_stub)
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "CryptoSafe Manager v1.0"))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

        self.table = SecureTable(self.root)
        self.table.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.load_data()

        self.status_bar = ttk.Label(self.root, text="Status: Locked | Clipboard: Empty", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def load_data(self):
        for item in self.table.get_children():
            self.table.delete(item)
        if hasattr(self, 'db'):
            rows = self.db.fetchall("SELECT id, title, username FROM vault_entries")
            for row in rows:
                self.table.insert("", tk.END, values=row)

    def add_entry_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Entry")
        dialog.geometry("300x200")

        ttk.Label(dialog, text="Title:").grid(row=0, column=0, padx=5, pady=5)
        title_entry = ttk.Entry(dialog)
        title_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(dialog, text="Password:").grid(row=1, column=0, padx=5, pady=5)
        pass_entry = ttk.Entry(dialog, show="*")
        pass_entry.grid(row=1, column=1, padx=5, pady=5)

        def save():
            if not title_entry.get():
                messagebox.showwarning("Error", "Title cannot be empty")
                return

            key = self.key_manager.load_key()
            enc_pass = self.crypto.encrypt(pass_entry.get().encode(), key)

            self.db.execute(
                "INSERT INTO vault_entries (title, encrypted_password) VALUES (?, ?)",
                (title_entry.get(), enc_pass)
            )

            self.events.publish(EventType.ENTRY_ADDED, {
                'action': 'ENTRY_ADDED',
                'title': title_entry.get()
            })

            self.load_data()
            dialog.destroy()

        ttk.Button(dialog, text="Save", command=save).grid(row=2, column=1, pady=20)

    def delete_selected_entry(self):
        selected = self.table.selection()
        if not selected:
            return

        item = self.table.item(selected[0])
        entry_id = item['values'][0]

        self.db.execute("DELETE FROM vault_entries WHERE id = ?", (entry_id,))

        self.events.publish(EventType.ENTRY_DELETED, {
            'action': 'ENTRY_DELETED',
            'id': entry_id
        })

        self.load_data()

    def show_logs_stub(self):
        messagebox.showinfo("Logs", "Audit Log Viewer will be implemented in Sprint 5")

    def show_settings_stub(self):
        sett = tk.Toplevel(self.root)
        sett.title("Settings")
        notebook = ttk.Notebook(sett)

        tab_security = ttk.Frame(notebook)
        tab_appearance = ttk.Frame(notebook)
        tab_advanced = ttk.Frame(notebook)

        notebook.add(tab_security, text="Security")
        notebook.add(tab_appearance, text="Appearance")
        notebook.add(tab_advanced, text="Advanced")

        ttk.Label(tab_security, text="Clipboard Timeout (s):").pack(pady=5)
        ttk.Entry(tab_security).pack(pady=5)

        ttk.Label(tab_security, text="Auto-lock Timeout (s):").pack(pady=5)  # Added Auto-lock
        ttk.Entry(tab_security).pack(pady=5)

        notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        sett.geometry("400x300")
