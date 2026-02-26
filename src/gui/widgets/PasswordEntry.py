import tkinter as tk

class PasswordEntry(tk.Frame):

    def __init__(self, master):
        super().__init__(master)

        self.showing = False

        self.entry = tk.Entry(self, show="*")
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.button = tk.Button(self, text="Показать", command=self.toggle)
        self.button.pack(side=tk.RIGHT)

    def toggle(self):
        if self.showing:
            self.entry.config(show="*")
            self.button.config(text="Показать")
        else:
            self.entry.config(show="")
            self.button.config(text="Скрыть")
        self.showing = not self.showing

    def get(self):
        return self.entry.get()
