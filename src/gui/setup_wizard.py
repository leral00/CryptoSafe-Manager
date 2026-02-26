import tkinter as tk
from tkinter import filedialog, messagebox

class SetupWizard:

    def __init__(self, master):
        self.window = tk.Toplevel(master)
        self.window.title("Первоначальная настройка")

        tk.Label(self.window, text="Мастер-пароль:").pack()
        self.pass1 = tk.Entry(self.window, show="*")
        self.pass1.pack()

        tk.Label(self.window, text="Подтверждение:").pack()
        self.pass2 = tk.Entry(self.window, show="*")
        self.pass2.pack()

        tk.Label(self.window, text="Файл базы данных:").pack()
        self.db_entry = tk.Entry(self.window)
        self.db_entry.pack()

        tk.Button(self.window, text="Выбрать файл", command=self.choose_file).pack()

        tk.Label(self.window, text="Параметры шифрования (заглушка)").pack(pady=5)

        tk.Button(self.window, text="Сохранить", command=self.save).pack(pady=10)

    def choose_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".db")
        self.db_entry.delete(0, tk.END)
        self.db_entry.insert(0, path)

    def save(self):
        if self.pass1.get() != self.pass2.get():
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return

        messagebox.showinfo("Готово", "Настройка завершена")
        self.window.destroy()
