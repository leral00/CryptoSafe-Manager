import tkinter as tk
from tkinter import filedialog, messagebox
import os
from datetime import datetime
from src.database.db import DatabaseHelper
from src.core.crypto.key_storage import KeyManager
from src.core.crypto.key_derivation import KeyDerivator

class SetupWizard:

    def __init__(self, master, on_finish_callback=None):
        self.window = tk.Toplevel(master)
        self.window.title("Первоначальная настройка")
        self.on_finish = on_finish_callback

        self.db = None
        self.key_manager = KeyManager()
        self.derivator = KeyDerivator()

        tk.Label(self.window, text="Мастер-пароль:").pack(pady=5)
        self.pass1 = tk.Entry(self.window, show="*")
        self.pass1.pack(pady=5)

        tk.Label(self.window, text="Подтверждение:").pack(pady=5)
        self.pass2 = tk.Entry(self.window, show="*")
        self.pass2.pack(pady=5)

        tk.Label(self.window, text="Файл базы данных:").pack(pady=5)
        self.db_entry = tk.Entry(self.window, width=40)
        self.db_entry.insert(0, os.path.abspath("cryptosafe.db"))
        self.db_entry.pack(pady=5)

        tk.Button(self.window, text="Выбрать файл", command=self.choose_file).pack(pady=5)
        tk.Button(self.window, text="Создать хранилище", command=self.save).pack(pady=20)

    def choose_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("Database files", "*.db")])
        if path:
            self.db_entry.delete(0, tk.END)
            self.db_entry.insert(0, path)

    def save(self):
        p1 = self.pass1.get()
        p2 = self.pass2.get()

        if p1 != p2:
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return

        is_strong, msg = self.derivator.check_password_strength(p1)
        if not is_strong:
            messagebox.showerror("Слабый пароль", f"Пароль не соответствует требованиям:\n{msg}")
            return

        db_path = self.db_entry.get()
        if not db_path:
            messagebox.showerror("Ошибка", "Укажите путь к базе данных")
            return

        try:
            self.db = DatabaseHelper(db_path)
            self.db.initialize_db()

            auth_salt = self.derivator.generate_salt()
            pass_hash = self.derivator.derive_argon2(p1, auth_salt).hex()

            self.db.execute(
                "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                ('admin', pass_hash, auth_salt.hex())
            )

            enc_salt = self.derivator.generate_salt(16)  
            iterations = 100000

            encryption_key = self.derivator.derive_pbkdf2(p1, enc_salt, iterations)

            self.key_manager.set_key("master_key", encryption_key)

            self.db.execute(
                "INSERT INTO key_store (key_id, algorithm, salt, iterations, version, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                ('master_encryption_key', 'PBKDF2-SHA256', enc_salt.hex(), iterations, 1, datetime.now().isoformat())
            )

            messagebox.showinfo("Готово", "Хранилище успешно создано")
            self.window.destroy()

            if self.on_finish:
                self.on_finish(db_path)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать хранилище:\n{e}")
