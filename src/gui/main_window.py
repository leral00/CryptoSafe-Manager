import tkinter as tk
from tkinter import messagebox, simpledialog
import shutil
import os

from src.gui.widgets.secure_table import SecureTable
from src.gui.widgets.audit_log_viewer import AuditLogViewer
from src.gui.setup_wizard import SetupWizard
from src.database.db import Database
class MainWindow:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CryptoSafe Manager")
        self.root.geometry("600x400")

        self.db = Database()

        self.logged_in = False
        self.clipboard_timer = 30

        self.build_menu()
        self.build_table()
        self.build_statusbar()

        self.root.after(100, self.open_setup)

    def build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Создать", command=self.new_vault)
        file_menu.add_command(label="Открыть", command=self.load_entries)
        file_menu.add_command(label="Резервная копия", command=self.backup_db)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_exit)
        menubar.add_cascade(label="Файл", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Добавить", command=self.add_entry)
        edit_menu.add_command(label="Изменить", command=self.edit_entry)
        edit_menu.add_command(label="Удалить", command=self.delete_entry)
        menubar.add_cascade(label="Правка", menu=edit_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Логи", command=self.open_logs)
        view_menu.add_command(label="Настройки", command=self.open_settings)
        menubar.add_cascade(label="Вид", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.root.config(menu=menubar)

    def build_table(self):
        self.table = SecureTable(self.root)
        self.table.pack(fill="both", expand=True)

    def build_statusbar(self):
        self.status = tk.Label(self.root, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(fill=tk.X)
        self.update_status()

    def update_status(self):
        login_status = "Вошел" if self.logged_in else "Не вошел"
        self.status.config(
            text=f"Статус: {login_status} | Таймер буфера: {self.clipboard_timer} сек"
        )

    def new_vault(self):
        self.table.clear()
        messagebox.showinfo("Создать", "Новый список создан")

    def load_entries(self):
        self.table.clear()

        entries = self.db.get_entries()  # ← исправлено

        for entry in entries:
            entry_id = entry[0]
            title = entry[1]
            username = entry[2]

            self.table.insert(entry_id, title, username)

    def backup_db(self):
        if os.path.exists("vault.db"):
            shutil.copy("vault.db", "vault_backup.db")
            messagebox.showinfo("Резервная копия", "Создан файл vault_backup.db")
        else:
            messagebox.showerror("Ошибка", "vault.db не найден")

    def on_exit(self):
        self.db.close()
        self.root.destroy()

    def add_entry(self):
        title = simpledialog.askstring("Добавить", "Название:")
        username = simpledialog.askstring("Добавить", "Username:")
        password = simpledialog.askstring("Добавить", "Пароль:")

        if title and username and password:

            encrypted_password = password.encode()

            self.db.add_entry(title, username, encrypted_password)

            self.load_entries()

    def edit_entry(self):
        selected = self.table.get_selected()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите запись")
            return

        entry_id, title, username = selected

        new_title = simpledialog.askstring("Изменить", "Новое название:", initialvalue=title)
        new_username = simpledialog.askstring("Изменить", "Новый username:", initialvalue=username)

        if new_title and new_username:
            self.db.update_entry(entry_id, new_title, new_username)
            self.load_entries()

    def delete_entry(self):
        selected = self.table.get_selected()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите запись")
            return

        entry_id, _, _ = selected
        self.db.delete_entry(entry_id)
        self.load_entries()

    def open_logs(self):
        AuditLogViewer(self.root)

    def open_settings(self):
        messagebox.showinfo("Настройки", "Диалог настроек (заглушка)")

    def show_about(self):
        messagebox.showinfo("О программе", "CryptoSafe Manager\nSprint 1")

    def open_setup(self):
        SetupWizard(self.root)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = MainWindow()
    app.run()
