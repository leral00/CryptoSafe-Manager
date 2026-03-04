import tkinter as tk
from tkinter import ttk
class PasswordEntry(ttk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, show="*", **kwargs)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.toggle_btn = ttk.Button(self, text="Show", width=5, command=self.toggle)
        self.toggle_btn.pack(side=tk.RIGHT)

    def toggle(self):
        if self.entry['show'] == '*':
            self.entry['show'] = ''
            self.toggle_btn.config(text="Hide")
        else:
            self.entry['show'] = '*'
            self.toggle_btn.config(text="Show")

    def get(self):
        return self.var.get()
