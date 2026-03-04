import tkinter as tk
from tkinter import ttk

class SecureTable(ttk.Treeview):
    def __init__(self, parent, columns=("id", "title", "username"), **kwargs):
        super().__init__(parent, columns=columns, show="headings", **kwargs)
        for col in columns:
            self.heading(col, text=col.capitalize())
            self.column(col, width=100)
